# JARVIS‑IV

A voice‑first, screen‑aware personal AI with a sci‑fi UI, dry wit, and useful tools. It listens, thinks, talks back, sees your screen, automates apps, searches the web, summarizes YouTube, and pops sleek hologram widgets for results.

If you like assistants that are helpful, fast, and just a little sarcastic, welcome home.


## Highlights

- Voice in, voice out: Speech‑to‑Text and Text‑to‑Speech with resilient fallbacks
- Beautiful Eel web UI: floating “widgets” for text, images, video, and weather
- Drag & drop files into the chat; they’re sent to the model in‑context
- Multi‑agent brains (UnisonAI): AI Expert, System Automator, Web Crawler, Vision
- Vision tool: capture current screen or webcam and ask questions about it
- System automation: open/close apps, web flows, inputs via a controller
- Web research: Google and DuckDuckGo with concise, source‑linked results
- YouTube summarize: fetch transcript and generate a clean summary
- Nano banana 🍌 powered image generation
- Pack as an app: PyInstaller build script produces a distributable


## What you can use it for

- Hands‑free Q&A and research with quick on‑screen widgets
- “Open Notepad, then search for X, then paste results” type automations
- Summarize a YouTube lecture and drop the notes on your screen
- “What’s on my screen?” or “what’s that object on my desk?” via screen/camera
- Rapid prototyping with tool‑calling: image gen, web search, weather, etc.
- Presentations/assistive overlays with movable, resizable widgets


## Under the hood (architecture)

- UI runtime: Eel (HTML/CSS/JS) in `ui/` with widgets driven by `ui/script.js`
- App runtime: `main.py` orchestrates STT/TTS, Eel, queues, worker threads
- Reasoning core: `brain.py` uses Google Generative AI (Gemini) with tool calling
- Agents & tools: `backend/agents.py`, `backend/func/` (automation, web, etc.)
- Vision: `backend/vision.py` – capture screen/camera, send to Gemini Vision
- Widgets from Python: `ui/UI.py` exposes `create_text_widget`, image/video, weather
- Tool schemas: `tools.py` enumerates callable tools for the model


## Personality and tone (with sarcasm)

- Personality: concise, confident, a touch of dry sarcasm. Think “I did the thing, also your tabs are chaos.”
- Sarcasm: tasteful and light by default; it teases, not attacks. No rudeness.
- Examples:
  - “Opened Chrome. Again. Because we totally didn’t have enough Chrome already.”
  - “Sure, I’ll summarize the 2‑hour video you didn’t watch.”
  - “Your screen has 17 icons fighting for attention. Minimalism is a lifestyle.”
- Safety: no harmful, hateful, or explicit content. Sarcasm stays PG and professional.
- Tuning: edit `backend/prompts/base.md` and the prompts under `backend/prompts/` to adjust voice. You can also set a custom assistant display name via `.env`.


## Quick start (Windows)

Prereqs: Python 3.10+ (3.12 works great), a mic, internet (for Gemini & TTS), and Chrome for browser automations.
1) Create your .env

```powershell
python setup_env.py
```

You’ll be prompted for:
- GEMINI_API_KEY (get one at https://aistudio.google.com/app/apikey)
- UserName, Age (for personalization)
- AssistantName (e.g., JARVIS)
- ELEVENLABS_API_KEY

2) Run

```powershell
python main.py
```

The sci‑fi UI opens. Speak when it says “Listening…”, or click the chat bubble and type. Drag & drop files onto the chat bubble to attach them.


## Using the features

- Voice and text
  - Talk to it. Or type in the bottom‑right chat bubble and hit Enter.
  - Results show in the bottom‑left log and as floating widgets.

- Vision
  - Ask: “What’s on my screen?” or “Summarize the error window”.
  - The agent can capture your screen or switch to camera mode when needed.

- Web research
  - “Research the latest Mixtral updates and show sources.”
  - Results include titles, blurbs, and URLs; it can also show images.

- System automation
  - “Open Notepad.” “Close Spotify.”
  - If direct open fails, it’ll try the official site or search.

- YouTube summarize
  - “Summarize https://youtu.be/VIDEOID in 250 words.”
  - Transcript → summary → optional on‑screen widget.

- Widgets
  - Right‑click any widget to close it. Drag by the header. Resize from bottom‑right.


## Configuration

- .env created by `setup_env.py` (saved in project root):
  - GEMINI_API_KEY
  - UserName, Age
  - AssistantName
- Optional environment for browser automation (fallbacks exist):
  - CHROME_INSTANCE_PATH, USER_DATA_DIR, PROFILE_DIRECTORY
- Logging: console log from `main.py` (threaded init + robust error handling)


## Toolbelt (selected)

- AI_Expert, System_Automator, Web_Crawler (see `backend/agents.py`)
- VisionTool (screen/camera → Gemini Vision)
- WebSearchTool (Google/DDG) → concise, source‑linked text
- OpenAppTool / CloseAppTool (desktop apps)
- YTSummarize (pull transcript + Gemini summary)
- Weather, time, location, and more under `backend/func/`


## Build as a standalone app

```powershell
python build_executable.py
```

- Output in `dist/JARVIS-IV/`
- Includes UI, backend, history, and README


## Troubleshooting

- STT microphone issues
  - Check mic permissions. If PortAudio/PyAudio errors: reinstall audio drivers.
- TTS (Edge TTS) / (ElevenLabs)
  - Requires internet. Check firewall/proxy if voice output is silent.
- Eel UI isn’t loading
  - Ensure `ui/` exists next to `main.py`. The app logs the resolved UI path.
- Vision
  - `opencv-python` needs a working webcam for camera mode. Screen capture uses `pyautogui`; disable “secure screen capture” apps if screenshots are blank.


## File map (orientation)

- `main.py` – entry point; starts Eel, STT/TTS, worker threads, UI loop
- `brain.py` – Gemini model, tool calling, and execution plumbing
- `ui/` – `index.html`, `style.css`, `script.js` (widgets, drag‑drop, chat)
- `ui/UI.py` – Python helpers to create widgets from backend
- `backend/` – agents, tools, prompts, and vision system
- `tools.py` – tool schemas exposed to the model
- `setup_env.py` – interactive .env creator
- `build_executable.py` – PyInstaller builder


## Keep or dial the sarcasm

- Default tone is crisp with a wink. If your boss is allergic to jokes:
  - Edit `backend/prompts/base.md` and system prompts to “professional only”.
  - Change `AssistantName` in `.env` to alter the vibe on the UI.


## Privacy & safety

- Local app with optional network calls (Gemini, search, TTS). No secrets are exfiltrated unless you provide them. Only use automations you trust.
- The assistant avoids harmful/hateful/explicit content. Sarcasm stays respectful.


## Credits

- Eel for the hybrid UI, Edge TTS for fast voices
- Google Generative AI (Gemini) for reasoning and vision, image generation (nano banana 🍌)
- UnisonAI for the agent/tool framework
- Selenium, DuckDuckGo/Google search, OpenCV, PyAutoGUI and friends
- ElevenLabs for advanced TTS capabilities and film accurate voices
- You, for trying it out and giving feedback!


––
Made with a helpful attitude and just enough sarcasm to keep things interesting.


