import urllib
import requests
from pywhatkit import playonyt
from ui.UI import create_video_widget, create_text_widget

def play_youtube(query):
    print("Searching YouTube...")
    """
    Searches YouTube for the given query and returns the URL of the first video result.

    Args:
        search_query: The search query string.

    Returns:
        The URL of the first video result, or None if no results are found or an error occurs.
    """
    try:
        # Encode the search query for URL use
        encoded_search_query = urllib.parse.quote(query)

        # Construct the YouTube search URL
        search_url = f"https://www.youtube.com/results?search_query={encoded_search_query}"

        # Make the request to YouTube
        response = requests.get(search_url)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        # Extract the video URL from the HTML response (improved parsing)
        start_index = response.text.find('{"url":"/watch?v=')
        if start_index == -1:
            return None  # No video found

        end_index = response.text.find('"', start_index + len('{"url":"/watch?v='))
        if end_index == -1:
            return None # Invalid HTML structure


        video_id = response.text[start_index + len('{"url":"/watch?v='):end_index]
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        try:
            print("Playing video... via widget")
            create_video_widget(video_url, "Youtube")
        except Exception as e:
            print(e)
            print("Playing video... via pywhatkit")
            playonyt(query)
    except Exception:
        try:
            create_text_widget("No video found", "Error")
        except Exception:
            print("No video found")
    return f"Video is playing on query: {query}"
    

