import os
import time
import hashlib
import pyautogui
import base64
import requests
import cv2  # Added for camera access
import numpy as np
from PIL import Image

from unisonai import BaseTool, Field


class VisionSystem:
    """Manages system state for vision tools, including API calls, caching, and hardware like the camera."""
    def __init__(self):
        self.last_api_call_time = 0
        self.min_call_interval = 3.0
        self.cache = {}
        self.cache_duration = 60
        self.camera = None  # Will hold the camera object

    def __del__(self):
        """Ensure the camera is released when the object is destroyed."""
        if self.camera is not None:
            print("Releasing camera...")
            self.camera.release()
            cv2.destroyAllWindows()

    def initialize_camera(self):
        """Initializes the camera object. Fast because it only runs once."""
        if self.camera is None:
            print("Initializing camera...")
            self.camera = cv2.VideoCapture(0)  # 0 is usually the default webcam
            if not self.camera.isOpened():
                self.camera = None # Reset on failure
                raise IOError("Could not open webcam. Make sure it is not in use.")
            # Allow camera to warm up
            time.sleep(1)

    def take_screenshot(self, filename="Assistant/Images/capture.jpg"):
        """Captures the screen and saves it."""
        screenshot = pyautogui.screenshot()
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        screenshot.save(filename, quality=80, optimize=True)
        print(f"Screenshot saved to {filename}")

    def capture_from_camera(self, filename="Assistant/Images/camera_capture.jpg"):
        """Captures a frame from the webcam and saves it."""
        self.initialize_camera() # Ensures camera is ready
        
        ret, frame = self.camera.read()
        if not ret:
            raise RuntimeError("Failed to capture image from camera.")

        os.makedirs(os.path.dirname(filename), exist_ok=True)
        cv2.imwrite(filename, frame)
        print(f"Camera image saved to {filename}")


vision_system = VisionSystem()


def GeminiVision(prompt, image_path):
    """Sends an image and prompt to the Google Gemini API for analysis."""
    try:
        print("Using Google Gemini for image analysis...")

        import google.generativeai as genai

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        image = Image.open(image_path)

        enhanced_prompt = f"""Analyze this image and answer: {prompt}

KEY INSTRUCTIONS:
• Use bullet points without periods
• DO NOT apologize or use phrases like "I'm sorry"
• DO NOT ask questions
• Maximum 400 characters
• Be direct and factual"""

        response = model.generate_content(
            [enhanced_prompt, image],
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 200,
            }
        )

        if not response.text:
            raise ValueError("Empty response from Gemini")

        result_text = response.text.strip()
        result_text = "\n".join([
            line for line in result_text.split('\n')
            if not line.strip().endswith('?')
            and "sorry" not in line.lower()
            and "apologize" not in line.lower()
        ])

        lines = result_text.split('\n')
        formatted_lines = []
        for line in lines:
            if line.strip() and not line.strip().startswith('•'):
                formatted_lines.append(f"• {line.strip()}")
            elif line.strip():
                formatted_lines.append(line.strip())

        final_result = f"SCREEN ANALYSIS:\n" + "\n".join(formatted_lines)
        if len(final_result) > 600:
            final_result = final_result[:550] + "..."

        return final_result

    except Exception as e:
        print(f"Gemini Vision error: {str(e)}")
        return f"SCREEN ANALYSIS:\n• Unable to analyze image due to technical limitations"


def Vision(prompt: str, mode: str = "screen") -> str:
    """Orchestrator function to capture an image from screen or camera and analyze it."""
    current_time = time.time()
    mode = mode.lower()

    try:
        cache_key = hashlib.md5(f"{prompt}:{mode}".encode()).hexdigest()
        if cache_key in vision_system.cache:
            cached_time, cached_result = vision_system.cache[cache_key]
            if current_time - cached_time < vision_system.cache_duration:
                print("Returning cached vision result...")
                return cached_result

        image_path = ""
        capture_dir = "Assistant/Images"
        os.makedirs(capture_dir, exist_ok=True)
        
        if mode == "screen":
            image_path = os.path.join(capture_dir, "screenshot_capture.jpg")
            vision_system.take_screenshot(image_path)
        elif mode == "camera":
            try:
                image_path = os.path.join(capture_dir, "camera_capture.jpg")
                vision_system.capture_from_camera(image_path)
            except (IOError, RuntimeError) as e:
                 return f"CAMERA ERROR:\n• {str(e)}"
        else:
            return f"INVALID MODE: Please use 'screen' or 'camera'."

        result = GeminiVision(prompt, image_path)
        vision_system.last_api_call_time = current_time

        if not isinstance(result, str) or len(result.strip()) < 10:
            result = f"ANALYSIS FAILED:\n• Image may have been captured\n• But API access or analysis failed"

        vision_system.cache[cache_key] = (current_time, result)
        print(f"Vision analysis complete. Result length: {len(result)}")
        return result

    except Exception as e:
        return f"VISION ERROR:\n• An unexpected technical limitation occurred\n• {str(e)[:100]}"


class VisionTool(BaseTool):
    name = "VisionTool"
    description = (
        "Captures the user's screen or takes a picture with the webcam for analysis. "
        "Use mode='screen' for UI content, reading text on the screen, or summarizing visual elements on the desktop. "
        "Use mode='camera' for analyzing the user's real-world environment and objects nearby."
    )
    params = [
        Field("prompt", "The user's question or goal for the image analysis."),
        Field("mode", "The input source. A choice between 'screen' and 'camera'.", default_value="screen")
    ]

    def _run(self, prompt: str, mode:str) -> str:
        return Vision(prompt, mode)


# Example direct usage
if __name__ == "__main__":
    tool = VisionTool()
    try:
        while True:
            user_prompt = input("\nEnter vision prompt (or 'exit'): ")
            if user_prompt.lower() == "exit":
                break
            
            mode_input = input("Enter mode ('screen' or 'camera'): ").lower().strip()
            if mode_input not in ["screen", "camera"]:
                print("Invalid mode. Defaulting to 'screen'.")
                mode_input = "screen"

            print("\n--- Running Vision Tool ---")
            analysis_result = tool._run(user_prompt, mode=mode_input)
            print("\n--- Result ---")
            print(analysis_result)
            print("----------------\n")
            
    except KeyboardInterrupt:
        print("\nExiting application.")
    finally:
        # The vision_system destructor will handle camera release automatically
        print("Cleanup complete.")