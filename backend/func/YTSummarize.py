import os
import re
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
from mtranslate import translate
from unisonai import BaseTool, Field

# Attempt to import UI function, but don't fail if it's not there
try:
    from ui.UI import create_text_widget
except ImportError:
    # Define a dummy function if the UI module is not available
    def create_text_widget(text, title):
        print(f"UI function not available. Would display '{title}'.")

# Load environment variables from a .env file
load_dotenv()

# Configure Google GenerativeAI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Error: Please set your GEMINI_API_KEY in the .env file")
    exit()

ytt_api = YouTubeTranscriptApi()

genai.configure(api_key=GEMINI_API_KEY)

def extract_video_id(youtube_url):
    """Extract video ID from different formats of YouTube URLs."""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)
    return None

def get_transcript(youtube_url):
    """Get transcript from a YouTube video using its URL."""
    try:
        video_id = extract_video_id(youtube_url)
        if not video_id:
            print(f"Error: Invalid YouTube URL or could not extract video ID from '{youtube_url}'")
            return None

        # Fetches transcript, preferring English or Hindi
        fetched_transcript = ytt_api.fetch(video_id)

        # is iterable
        for snippet in fetched_transcript:
            print(snippet.text)

        return " ".join(item.text for item in fetched_transcript)

    except Exception as e:
        print(f"Error getting transcript: {e}")
        return None

def generate_summary(transcript):
    """Generate a summary of the transcript using the Gemini API."""
    if not transcript:
        print("Cannot generate summary from an empty transcript.")
        return None
    try:
        prompt = (
            "Please provide a concise summary (maximum 250 words) of the following video transcript, "
            "focusing on the main points and key takeaways. Present the summary in clear, easy-to-understand paragraphs: "
        )
        model = genai.GenerativeModel("gemini-2.5-flash-lite") # Using a standard, robust model
        response = model.generate_content(prompt + transcript)
        return response.text
    except Exception as e:
        print(f"Error generating summary: {e}")
        return None

def yt_summarize(youtube_url: str):
    """
    Main function to orchestrate the YouTube video summarization process.
    
    Args:
        youtube_url (str): The full URL of the YouTube video to be summarized.
    """
    if not youtube_url or not youtube_url.strip():
        print("Error: Please provide a valid YouTube URL.")
        return

    print(f"\nProcessing YouTube video: {youtube_url}")
    print("Fetching transcript...")

    # 1. Get transcript from the video.
    transcript = get_transcript(youtube_url)
    if not transcript:
        print("Failed to fetch transcript. Cannot continue.")
        return

    # 2. Generate summary from the transcript.
    print("Generating summary...")
    summary = generate_summary(transcript)
    if not summary:
        print("Failed to generate summary.")
        return "Failed to generate summary."

    # 3. Translate the summary to English (if it's in another language).
    translated_summary = translate(summary, "en")

    # 4. Display the summary.
    print("\n--- Video Summary ---")
    print(translated_summary)
    print("---------------------\n")

    # 5. Optionally, display the summary in a custom UI widget.
    try:
        create_text_widget(translated_summary, "YouTube Video Summary")
    except Exception as e:
        print(f"Could not display summary in UI widget: {e}")
    return translated_summary

class YTSummarize(BaseTool):
    name = "YTSummarize"
    description = "Summarize a YouTube video from its URL"
    params = [Field("link", "The full URL of the YouTube video to be summarized")]

    def _run(self, link: str):
        return yt_summarize(link)


if __name__ == "__main__":
    # This block allows the script to be run directly for testing.
    url_input = input("Please enter a YouTube video URL to summarize: ")
    yt_summarize(url_input)