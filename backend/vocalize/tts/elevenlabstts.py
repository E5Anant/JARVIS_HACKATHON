# example.py
import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play
from io import BytesIO


load_dotenv()

elevenlabs = ElevenLabs(
  api_key=os.getenv("ELEVENLABS_API_KEY"),
)

def ElevenLabsPaulTTS(text: str):
    voice = elevenlabs.voices.ivc.create(
    name="JARVIS",
    # Replace with the paths to your audio files.
    # The more files you add, the better the clone will be.
    files=[BytesIO(open(f"{os.getcwd()}/wavs/audio18.wav", "rb").read())]
  )
    audio = elevenlabs.text_to_speech.convert(
        text=text,
        voice_id=voice.voice_id,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    play(audio)
    print()
    print(f"Jarvis: {text}")

def ElevenLabsTTS(text: str, voice_id: str = "EtsjFhqOd0YWASYxlmIg"):
    audio = elevenlabs.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    play(audio)
    print()
    print(f"Jarvis: {text}")

if __name__ == "__main__":
    ElevenLabsTTS("Hello, I am Jarvis, your personal AI assistant.", voice_id="EtsjFhqOd0YWASYxlmIg")