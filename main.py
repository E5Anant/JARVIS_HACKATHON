import os
import sys
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor
import eel
import asyncio
import traceback
import platform
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("JARVIS")

# Ensure we're using the correct path when running as executable
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle (compiled with PyInstaller)
    application_path = os.path.dirname(sys.executable)
    os.chdir(application_path)
    sys.path.insert(0, application_path)
    logger.info(f"Running as executable from: {application_path}")

# UI imports
try:
    from ui.UI import create_text_widget
except ImportError as e:
    logger.critical(f"Failed to import UI components: {e}")
    sys.exit(1)

from shared_queue import ui_update_queue

# Local imports with platform-specific error handling
try:
    from brain import generate
    from backend.vocalize.stt.listenjs import ListenJS
    # from backend.vocalize.tts.edgetts import Edgetts
    from backend.vocalize.tts.elevenlabstts import ElevenLabsTTS
    from backend.vision import vision_system
    
    logger.info(f"System: {platform.system()}, Release: {platform.release()}")
    logger.info("Core modules successfully imported")
except ImportError as e:
    logger.critical(f"FATAL: Could not import a required local module: {e}")
    traceback.print_exc()
    sys.exit(1)

# --- Global variables for thread-safe access ---
stt = None
tts = None
task_queue = queue.Queue()
ASSISTANT_NAME = os.environ.get('AssistantName', 'Assistant')
GLOBAL_FILE_QUEUE = []
file_queue_lock = threading.Lock()

# --- Enhanced Robust Initialization Functions with Fallbacks ---
def initialize_stt():
    """
    Initializes Speech-to-Text system with fallbacks for different platforms.
    Returns True on success, False on failure.
    """
    global stt
    
    logger.info("Initializing Speech-to-Text system...")
    
    try:
        # Primary initialization
        stt = ListenJS()
        logger.info("STT Initialized successfully using ListenJS.")
        return True
    except Exception as primary_error:
        logger.warning(f"Primary STT initialization failed: {primary_error}")
        
        # Platform-specific fallback attempts could be implemented here
        # For now we'll log detailed diagnostics to help troubleshooting
        
        # Check for common issues
        if "PortAudio" in str(primary_error) or "pyaudio" in str(primary_error):
            logger.error("PyAudio/PortAudio issue detected. Check microphone and driver installation.")
            if platform.system() == "Windows":
                logger.error("On Windows, try: pip install pyaudio")
            elif platform.system() == "Linux":
                logger.error("On Linux, try: sudo apt-get install python3-pyaudio portaudio19-dev")
            elif platform.system() == "Darwin":  # macOS
                logger.error("On macOS, try: brew install portaudio && pip install pyaudio")
        
        logger.error(f"Failed to initialize Speech-to-Text (STT): {primary_error}")
        traceback.print_exc()
        return False

class ElevenLabsSpeaker:
    """Thin adapter so the rest of the app can call tts.speak(text)."""
    def __init__(self, voice_id: str | None = None):
        # Default voice can be overridden via env ELEVENLABS_VOICE_ID
        self.voice_id = voice_id or os.environ.get("ELEVENLABS_VOICE_ID", "EtsjFhqOd0YWASYxlmIg")

    def speak(self, text: str):
        try:
            # Uses the function provided by backend.vocalize.tts.elevenlabstts
            ElevenLabsTTS(text=text, voice_id=self.voice_id)
        except Exception as e:
            logger.error(f"ElevenLabs speak failed: {e}")
            # Fall back to console output so we don't crash the pipeline
            print(f"Jarvis: {text}")


def initialize_tts():
    """
    Initializes Text-to-Speech system using ElevenLabs.
    Returns True on success, False on failure.
    """
    global tts

    logger.info("Initializing Text-to-Speech system (ElevenLabs)...")

    # Basic sanity: API key should be available; the imported module loads dotenv
    if not os.environ.get("ELEVENLABS_API_KEY"):
        logger.error("ELEVENLABS_API_KEY not set. Add it to your .env via setup_env.py.")
        return False

    try:
        voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "EtsjFhqOd0YWASYxlmIg")
        tts = ElevenLabsSpeaker(voice_id=voice_id)
        logger.info("TTS initialized successfully using ElevenLabs.")
        return True
    except Exception as primary_error:
        logger.warning(f"TTS initialization failed: {primary_error}")
        traceback.print_exc()
        return False

def cleanup_history_files():
    """Clean up history directory in a cross-platform safe way"""
    logger.info("Cleaning up history directory...")
    
    # Use Path for cross-platform path handling
    history_dir = Path("history")
    
    if history_dir.exists() and history_dir.is_dir():
        try:
            # Delete files first
            for file_path in history_dir.glob('*'):
                if file_path.is_file():
                    file_path.unlink()
                    logger.debug(f"Removed file: {file_path}")
            
            # Only delete the directory if all files were successfully removed
            if not any(history_dir.iterdir()):
                try:
                    history_dir.rmdir()
                    logger.info("History directory cleaned and removed.")
                except Exception as e:
                    logger.warning(f"Could not remove history directory: {e}")
        except Exception as e:
            logger.error(f"Error cleaning history directory: {e}")
    
    # Create fresh directory
    history_dir.mkdir(exist_ok=True)
    logger.info(f"History directory ready at: {history_dir.absolute()}")

# Run cleanup on startup
cleanup_history_files()

# --- Enhanced Voice Listener Loop with Recovery ---
def voice_listener_loop():
    """
    Voice listener with improved error handling and recovery capabilities.
    Automatically recovers from temporary failures and provides feedback.
    """
    # Explicitly declare we're using the global stt variable
    global stt
    
    ui_update_queue.put(('printToOutput', "Listening..."))
    
    consecutive_errors = 0
    backoff_time = 1  # Initial backoff time in seconds
    
    while True:
        try:
            # Check if stt is initialized
            if stt is None:
                logger.warning("STT not initialized, attempting to initialize...")
                try:
                    stt = ListenJS()
                    logger.info("STT initialized in voice_listener_loop")
                except Exception as init_error:
                    logger.error(f"Failed to initialize STT: {init_error}")
                    time.sleep(5)  # Wait before retrying
                    continue  # Skip this iteration and try again
            
            # Get speech from microphone
            speech = stt.SpeechRecognition()
            logger.debug(f"STT returned: '{speech}'")
            
            # If valid speech was detected
            if speech and speech.strip():
                logger.info(f"Voice input received: '{speech}'")
                ui_update_queue.put(('updateBottomLeftOutput', f"Heard: '{speech}'"))
                task_queue.put(speech)
                
                # Reset error counters on success
                consecutive_errors = 0
                backoff_time = 1
            
        except Exception as e:
            consecutive_errors += 1
            logger.error(f"Error in voice listener (attempt {consecutive_errors}): {e}")
            
            # Adaptive backoff strategy
            if consecutive_errors <= 3:
                # Minor issue - short wait
                message = "Temporary listening issue. Retrying..."
                wait_time = backoff_time
            elif consecutive_errors <= 10:
                # More persistent issue - longer wait
                message = "Microphone access issues. Retrying after short delay..."
                wait_time = backoff_time
                backoff_time = min(backoff_time * 1.5, 10)  # Exponential backoff up to 10 seconds
            else:
                # Serious issue - inform user but keep trying
                message = "Ongoing microphone issues. Please check your audio settings."
                wait_time = 10  # Fixed long delay
                
                # Try to reinitialize STT every 10 errors
                if consecutive_errors % 10 == 0:
                    ui_update_queue.put(('printToOutput', "Attempting to reinitialize speech recognition..."))
                    try:
                        # We're already in global scope for stt because of the global declaration at the top
                        if stt is not None:
                            # Properly close existing instance if needed
                            try:
                                stt.close()
                            except Exception as close_error:
                                logger.error(f"Error closing STT: {close_error}")
                                
                        # Set to None first to ensure clean state
                        stt = None
                        # Initialize new STT instance
                        stt = ListenJS()
                        ui_update_queue.put(('printToOutput', "Speech recognition reinitialized."))
                        consecutive_errors = 0  # Reset on successful reinit
                    except Exception as reinit_error:
                        logger.error(f"Failed to reinitialize STT: {reinit_error}")
            
            # Inform user of issues
            ui_update_queue.put(('printToOutput', message))
            time.sleep(wait_time)

# --- All other functions (Eel-exposed, task processing, etc.) remain the same ---
@eel.expose
def add_file_to_queue(file_data: dict):
    with file_queue_lock:
        print(f"Adding file to backend queue: {file_data.get('name')}")
        GLOBAL_FILE_QUEUE.append(file_data)
        print(f"Files currently in queue: {len(GLOBAL_FILE_QUEUE)}")
@eel.expose
def remove_file_from_queue(filename: str):
    with file_queue_lock:
        initial_count = len(GLOBAL_FILE_QUEUE)
        GLOBAL_FILE_QUEUE[:] = [f for f in GLOBAL_FILE_QUEUE if f.get('name') != filename]
        final_count = len(GLOBAL_FILE_QUEUE)
        if initial_count > final_count:
            print(f"Removed '{filename}' from backend queue.")
            print(f"Files currently in queue: {len(GLOBAL_FILE_QUEUE)}")

def task_processor_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(async_worker())

async def async_worker():
    while True:
        try:
            prompt_text = await asyncio.get_running_loop().run_in_executor(
                None, task_queue.get
            )
            ui_update_queue.put(('clearFrontendFileList', None))
            if prompt_text:
                ui_update_queue.put(('printToOutput', f"User: {prompt_text}"))
            ui_update_queue.put(('printToOutput', "Thinking..."))
            await handle_task_async(prompt_text)
        except Exception as e:
            print(f"CRITICAL ERROR in async_worker's main loop: {e}")
            traceback.print_exc()

async def handle_task_async(prompt_text: str):
    global GLOBAL_FILE_QUEUE
    files_to_send = []
    with file_queue_lock:
        if GLOBAL_FILE_QUEUE:
            files_to_send.extend(GLOBAL_FILE_QUEUE)
            GLOBAL_FILE_QUEUE.clear()
    loop = asyncio.get_running_loop()
    try:
        response = await generate(prompt=prompt_text, files=files_to_send)
        if response and response.strip():
            ui_update_queue.put(('updateBottomLeftOutput', response))
            await loop.run_in_executor(None, tts.speak, response)
        else:
            fallback_message = "I'm sorry, I couldn't determine a response. Please try rephrasing."
            ui_update_queue.put(('updateBottomLeftOutput', fallback_message))
            await loop.run_in_executor(None, tts.speak, fallback_message)
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        print(error_message)
        traceback.print_exc()
        ui_update_queue.put(('updateBottomLeftOutput', "I've encountered an internal error. Please check the logs."))
        await loop.run_in_executor(None, tts.speak, "I've encountered an internal error.")
    finally:
        ui_update_queue.put(('printToOutput', "Listening..."))
        task_queue.task_done()

@eel.expose
def get_assistant_name(): return ASSISTANT_NAME

@eel.expose
def process_text_input(message):
    if message.strip() or GLOBAL_FILE_QUEUE:
        task_queue.put(message)

def main():
    """
    Main entry point for the application.
    Handles initialization of all components and manages the main application loop.
    Designed to work both as a script and as a compiled executable.
    """
    # Determine UI directory based on whether we're running as executable or script
    if getattr(sys, 'frozen', False):
        # Running as executable
        ui_path = os.path.join(os.path.dirname(sys.executable), 'ui')
        logger.info(f"Running as executable. UI path: {ui_path}")
    else:
        # Running as script
        ui_path = 'ui'
        logger.info(f"Running as script. UI path: {ui_path}")
    
    # Initialize Eel with the correct UI path
    try:
        eel.init(ui_path)
        logger.info("Eel UI framework initialized successfully")
    except Exception as e:
        logger.critical(f"Failed to initialize UI framework: {e}")
        return

    logger.info("--- Starting System Initializations ---")

    # Component initialization with proper error handling
    with ThreadPoolExecutor(max_workers=3, thread_name_prefix='Init') as executor:
        stt_future = executor.submit(initialize_stt)
        tts_future = executor.submit(initialize_tts)
        camera_future = executor.submit(vision_system.initialize_camera)

        # Check critical components
        stt_ok = stt_future.result()
        tts_ok = tts_future.result()
        
        # Check non-critical camera component
        try:
            camera_future.result()
            logger.info("Camera initialized successfully")
        except Exception as e:
            logger.warning(f"Non-critical component (Camera) failed to initialize: {e}")
            logger.warning("VisionTool's 'camera' mode will be unavailable.")

    # Exit if critical components failed
    if not stt_ok or not tts_ok:
        logger.critical("--- Critical components (STT/TTS) failed to initialize. Exiting. ---")
        return

    logger.info("--- All critical initializations complete. Starting application. ---")

    # Start worker threads
    try:
        voice_thread = threading.Thread(target=voice_listener_loop, daemon=True, name="VoiceListener")
        voice_thread.start()
        logger.info("Voice listener thread started")
        
        processor_thread = threading.Thread(target=task_processor_loop, daemon=True, name="TaskProcessor")
        processor_thread.start()
        logger.info("Task processor thread started")
    except Exception as e:
        logger.critical(f"Failed to start worker threads: {e}")
        return

    # Set window size based on screen resolution
    try:
        # Default size - will be used if we can't detect screen size
        window_size = (1280, 720)
        
        # Try to get screen resolution for better sizing
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()  # Hide the window
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            window_size = (min(1920, screen_width - 100), min(1080, screen_height - 100))
            root.destroy()
        except Exception as e:
            logger.warning(f"Couldn't detect screen size: {e}. Using default window size.")
        
        logger.info(f"Starting Eel UI with window size: {window_size}")
        eel.start('index.html', size=window_size, block=False)
    except Exception as e:
        logger.critical(f"Failed to start UI: {e}")
        return

    # Main UI event processing loop with improved error handling
    logger.info("Entering main event loop")
    while True:
        try:
            # Process UI commands
            try:
                command, args = ui_update_queue.get(block=True, timeout=0.05)
                
                if command == 'printToOutput':
                    eel.printToOutput(args)
                elif command == 'updateBottomLeftOutput':
                    eel.updateBottomLeftOutput(args)
                elif command == 'clearFrontendFileList':
                    eel.clearFrontendFileList()
                elif command == 'create_widget':
                    widget_type = args.get('type')
                    logger.debug(f"Processing UI command: create_widget of type '{widget_type}'")
                    if widget_type == 'text':
                        create_text_widget(text=args.get('text'), title=args.get('title'))
                else:
                    logger.warning(f"Unknown UI command received: {command}")
                
                ui_update_queue.task_done()
            except queue.Empty:
                # This is expected - we just continue
                pass
                
        except Exception as e:
            logger.error(f"Error in UI update loop: {e}")
            traceback.print_exc()
            # Continue running despite errors in UI updates
            
        # Let Eel process any pending events
        eel.sleep(0.01)

if __name__ == "__main__":
    main()