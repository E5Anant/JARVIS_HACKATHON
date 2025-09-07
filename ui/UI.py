import eel
import random
import os
import base64

widget_counter = 0

def get_next_widget_id():
    global widget_counter
    widget_counter += 1
    return f'widget_{widget_counter}'

@eel.expose
def create_text_widget(text, title="INFORMATION"):
    """Create a text widget with the given content"""
    widget_id = get_next_widget_id()
    # Random position within viewport
    x = random.randint(50, 800)
    y = random.randint(50, 400)
    eel.createWidget(widget_id, title, 'text', text, x, y)
    return widget_id

@eel.expose
def create_video_widget(video_path, title="VIDEO"):
    widget_id = get_next_widget_id()
    x = random.randint(50, 800)
    y = random.randint(50, 400)
    eel.createWidget(widget_id, title, 'video', video_path, x, y)
    return widget_id

@eel.expose
def update_bottom_left(text):
    """
    Updates the content of the bottom-left output area in the UI.

    Args:
        text (str): The text to display in the bottom-left output.
    """
    eel.spawn(eel.updateBottomLeftOutput(text))  # Use eel.spawn for thread safety

@eel.expose
def create_image_widget(image_path, title="IMAGE"):
    widget_id = get_next_widget_id()
    x = random.randint(50, 800)
    y = random.randint(50, 400)

    if os.path.exists(image_path):  # Check if path is local
        with open(image_path, "rb") as img_file:
            b64_encoded_image = base64.b64encode(img_file.read()).decode('utf-8')
            # Determine mime type from extension or use a default
            mime_type = "image/png" # Default
            if image_path.lower().endswith((".jpg", ".jpeg")):
                mime_type = "image/jpeg"
            elif image_path.lower().endswith(".gif"):
                mime_type = "image/gif"
            elif image_path.lower().endswith(".webp"):
                mime_type = "image/webp"

            data_url = f"data:{mime_type};base64,{b64_encoded_image}"
            eel.createWidget(widget_id, title, 'image', data_url, x, y)  # Use data URL
    elif image_path.startswith("http"):  # Check if it's a URL
        eel.createWidget(widget_id, title, 'image', image_path, x, y) # Use the URL directly
    else:
        print(f"Error: Invalid image path or URL: {image_path}")
        # Create a text widget with an error message
        eel.createWidget(widget_id, "Error", "text", f"Error: Invalid image path or URL: {image_path}", x, y)

    return widget_id

@eel.expose
def create_weather_widget(weather_data, title="WEATHER"):
    widget_id = get_next_widget_id()
    x = random.randint(50, 800)
    y = random.randint(50, 400)
    eel.createWidget(widget_id, title, 'weather', weather_data, x, y)
    return widget_id