import os
import sys
import re
import time
import threading
import random
import pygame
import subprocess
import tempfile
from pydub import AudioSegment
import os

def increase_volume_pydub(input_audio_path, output_audio_path, gain_db):
    """
    Increases the volume of an audio file using pydub.

    Args:
        input_audio_path (str): Path to the input audio file.
        output_audio_path (str): Path to save the output audio file.
        gain_db (float): The amount of decibels to increase the volume by.
                         Positive value increases, negative value decreases.
                         E.g., 6 dB doubles the perceived loudness.
    """
    try:
        # Determine format from file extension
        file_extension = os.path.splitext(input_audio_path)[1][1:]
        if not file_extension:
            print(f"Error: Could not determine file format for {input_audio_path}. Please include extension.")
            return

        print(f"Loading audio from: {input_audio_path} (format: {file_extension})")
        audio = AudioSegment.from_file(input_audio_path, format=file_extension)

        # Increase volume
        louder_audio = audio + gain_db

        # Export the louder audio
        output_file_extension = os.path.splitext(output_audio_path)[1][1:]
        if not output_file_extension:
            output_file_extension = file_extension # Default to input format if not specified in output path

        louder_audio.export(output_audio_path, format=output_file_extension)


    except FileNotFoundError:
        print(f"Error: Input file not found at {input_audio_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Make sure you have ffmpeg installed and it's in your system PATH if using non-WAV files.")
        print("Also ensure the input file exists and its format is supported.")

pygame.mixer.init()

class Edgetts:
    def __init__(self,
                 voice: str = 'en-CA-LiamNeural',
                 pitch: str = "+0Hz",
                 rate: str = "-2%",):
        self.voice = voice
        self.pitch = pitch
        self.rate = rate

    def clean_text_for_tts_simple(self, text: str) -> str:
        """Simplifies text for better Edge TTS performance."""
        text = re.sub('<[^<]+?>', '', text)
        text = re.sub(r'http\S+|www\.\S+|\S+@\S+', ' ', text)
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def play_sound(self, filename: str):
        """Plays the sound and removes the file afterwards."""
        try:
            if not os.path.exists(filename) or os.path.getsize(filename) == 0:
                print(f"Sound Error: Audio file '{filename}' missing or empty.", file=sys.stderr)
                return
            sound = pygame.mixer.Sound(filename)
            sound.play()
            while pygame.mixer.get_busy():
                pygame.time.delay(100)
        except pygame.error as e:
            print(f"Pygame Error playing sound '{filename}': {e}", file=sys.stderr)
        finally:
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except OSError as e:
                    print(f"File Error: Could not remove audio file '{filename}': {e}", file=sys.stderr)

    def speak(self, text: str, subtitle_file_override: str = None) -> None:
        """
        Converts text to speech using Edge TTS. If text is long, speaks a notification
        and prints the full text. Otherwise, speaks and prints the text.
        """
        responses = [
            "The rest of the result has been printed to the chat screen, kindly check it out sir.",
            "The rest of the text is now on the chat screen, sir, please check it.",
            "You can see the rest of the text on the chat screen, sir.",
            "The remaining part of the text is now on the chat screen, sir.",
            "Sir, you'll find more text on the chat screen for you to see.",
            "The rest of the answer is now on the chat screen, sir.",
            "Sir, please look at the chat screen, the rest of the answer is there.",
            "You'll find the complete answer on the chat screen, sir.",
            "The next part of the text is on the chat screen, sir.",
            "Sir, please check the chat screen for more information.",
            "There's more text on the chat screen for you, sir.",
            "Sir, take a look at the chat screen for additional text.",
            "You'll find more to read on the chat screen, sir.",
            "Sir, check the chat screen for the rest of the text.",
            "The chat screen has the rest of the text, sir.",
            "There's more to see on the chat screen, sir, please look.",
            "Sir, the chat screen holds the continuation of the text.",
            "You'll find the complete answer on the chat screen, kindly check it out sir.",
            "Please review the chat screen for the rest of the text, sir.",
            "Sir, look at the chat screen for the complete answer."
        ]

        text_for_tts_command: str
        is_long_text_scenario = len(text) > 300

        if is_long_text_scenario:
            notification = random.choice(responses)
            text_for_tts_command = self.clean_text_for_tts_simple(notification)
        else:
            text_for_tts_command = self.clean_text_for_tts_simple(text)

        if not text_for_tts_command:
            print("Jarvis: Nothing to speak after cleaning text.", file=sys.stderr)
            if is_long_text_scenario: # Still animate original long text if notification failed to clean
                print("\nJarvis: ", end="")
                print(text)
            return

        # Determine subtitle path and ensure directory exists
        actual_subtitle_path = subtitle_file_override if subtitle_file_override else os.path.join('data', 'Subtitles_File.srt')
        
        subtitle_dir = os.path.dirname(actual_subtitle_path)
        if subtitle_dir and not os.path.exists(subtitle_dir):
            try:
                os.makedirs(subtitle_dir)
            except OSError as e:
                print(f"File Error: Could not create subtitle directory '{subtitle_dir}': {e}", file=sys.stderr)

        output_file_mp3 = None
        tts_command_successful = False
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_f:
                output_file_mp3 = tmp_f.name
            
            edge_tts_command_str = (
                f'edge-tts --voice "{self.voice}" --text "{text_for_tts_command}" '
                f'--write-media "{output_file_mp3}" --write-subtitles "{actual_subtitle_path}" '
                f'--pitch={self.pitch} --rate={self.rate} --volume=+250%'
            )
            process = subprocess.run(edge_tts_command_str, shell=True, check=True, capture_output=True, text=True)
            tts_command_successful = True

        except subprocess.CalledProcessError as e:
            error_output = e.stderr or e.stdout or "No error output from edge-tts."
            print(f"TTS Error: edge-tts command failed (Code: {e.returncode}): {error_output.strip()}", file=sys.stderr)
        except FileNotFoundError:
            print("TTS Error: 'edge-tts' command not found. Please ensure it is installed and in your system's PATH.", file=sys.stderr)
        except Exception as e: # Catch any other unexpected errors during TTS generation
            print(f"Unexpected Error during TTS generation: {e}", file=sys.stderr)
        finally:
            if not tts_command_successful and output_file_mp3 and os.path.exists(output_file_mp3):
                # Clean up temp mp3 if TTS failed before play_sound could use and delete it
                os.remove(output_file_mp3)

        # --- Sound playback and animated message ---
        if tts_command_successful and output_file_mp3 and os.path.exists(output_file_mp3) and os.path.getsize(output_file_mp3) > 0:
            print("\nJarvis: ", end="") # Prefix for the spoken audio and subsequent animated text
            increase_volume_pydub(output_file_mp3, output_file_mp3, 7)
            sound_thread = threading.Thread(target=self.play_sound, args=(output_file_mp3,))
            sound_thread.start()
            
            # To wait for sound to finish before this function returns (optional):
            # if sound_thread.is_alive():
            #     sound_thread.join()
        elif is_long_text_scenario:
            # TTS failed, but it was a long text scenario.
            # Original behavior implies the long text animation would still happen.
            print("\nJarvis (TTS for notification failed): ", end="")
    
        # Clean up the subtitle file
        if os.path.exists(actual_subtitle_path):
            try:
                os.remove(actual_subtitle_path)
            except OSError as e:
                print(f"File Error: Could not remove subtitle file '{actual_subtitle_path}': {e}", file=sys.stderr)

if __name__ == "__main__":
    try:
        edge_tts = Edgetts()
        while True:
            try:
                user_input = input("Enter text to speak (or Ctrl+C to exit): ")
                if user_input.strip(): # Check if input is not just whitespace
                    edge_tts.speak(user_input)
                else:
                    print("No text entered.")
            except UnicodeDecodeError:
                print("Input Error: Could not decode input. Please use standard characters.", file=sys.stderr)
    except KeyboardInterrupt:
        print("\nExiting application.")
    finally:
        pygame.mixer.quit() # Clean up Pygame mixer resources