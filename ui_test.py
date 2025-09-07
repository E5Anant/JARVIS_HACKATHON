import eel
from ui.UI import update_bottom_left
from ui.UI import create_text_widget, create_weather_widget, create_video_widget
import threading
import asyncio
import time
import sys
import os
import subprocess
from os import environ

eel.init('ui')
base_dir = os.path.dirname(os.path.abspath(__file__))
def main():
    create_text_widget("Welcome Home Sir!", title="WELCOME")
    weather_data = {
        "temperature": "27°C",
        "location": "Kolkata, India",
        "description": "Clouds",
        "main_condition": "Clear",  # This key is used by JS to pick the main icon
        "humidity": "40%",
        "wind": "8.7 m/s",
        "feels_like": "30°C",
    }
    create_video_widget(r"https://www.youtube.com/watch?v=jyWbD_Tp-EA", title="YOUTUBE")
    create_weather_widget(weather_data, title="WEATHER")
    while True:
        # When not in active listening mode, only listen for wake word
        eel.printToOutput("")
        
        # Add a small delay to prevent high CPU usage
        time.sleep(0.1)
        
        # Show processing state
        eel.printToOutput("Processing...")
        
        update_bottom_left("As you wish Sir!")

# Expose assistant name to JavaScript
@eel.expose
def get_assistant_name():
    """Return the assistant name from environment variable"""
    return environ['AssistantName']

# Update the process_text_input function
@eel.expose
def process_text_input(text):
    """Process text input from the UI"""
    print(f"Processing text input: {text}")  # Debug line
    try:
        # Show processing state in UI
        eel.printToOutput("Processing...")
        
        # Clear the "Processing..." message and update with the actual response
        eel.printToOutput(f"")
        
        # Update the UI with the response
        update_bottom_left(text)
        
        return text
    except Exception as e:
        error_message = f"Error processing input: {str(e)}"
        print(error_message)
        update_bottom_left(error_message)
        return error_message

@eel.expose
def printToOutput(text):
    """Print text to the output area"""
    print(f"Output: {text}")  # Debug line
    eel.updateOutput(text)    # Call the JavaScript updateOutput function

threading.Thread(target=main).start()
eel.start('index.html', size=(1920, 1080))