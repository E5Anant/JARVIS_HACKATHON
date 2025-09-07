# Build & Integration Challenges

A concise log of the gnarly bits we hit building JARVIS and how we tackled them.

## Resolved challenges (fixed)

- Multi‑agent framework complexity (routing, tool schema drift, recursion)
	- Symptoms: Confusing tool dispatch, occasional double‑self errors, YAML/JSON param drift, and loops when agents messaged each other.
	- Fix: Standardized on UnisonAI `Single_Agent` instances in `backend/agents.py`; unified tool schema via `create_tools(...)`; robust param parsing with `_ensure_dict_params`; fuzzy agent name matching to reduce misroutes; corrected tool dispatch to avoid passing `self` twice; added `pass_result`/`send_message` flows; in `brain.py` normalized function‑call parsing and fed tool outputs back using `role="tool"` + `function_response`.

- Function‑call parsing and concurrency with Gemini
	- Symptoms: Mis‑unpacked `(name, args)` tuples; empty results dropped on the floor; blocking behavior.
	- Fix: Rewrote `handle_function_calls(...)` to unpack correctly; `execute_function(...)` branches UI vs backend tools; concurrent `asyncio.gather` across calls; guard empty results and loop until final text.

- UI thread safety with Eel
	- Symptoms: Cross‑thread UI updates froze the app.
	- Fix: All background threads post commands to `ui_update_queue`; only the main loop calls Eel. UI widgets (e.g., `create_text_widget`) are queued (`'create_widget'`) and handled centrally.

- Camera resource leaks and first‑frame black
	- Symptoms: Webcam remained locked; first capture black; crash on re‑open.
	- Fix: `VisionSystem.initialize_camera()` warm‑up and one‑time init; destructor releases camera; explicit error messages and recovery.

- Drag‑and‑drop file handling and preview leaks
	- Symptoms: Object URL leaks; UI/file queue out of sync for large drops.
	- Fix: Preview `Map` with URL revocation; backend signals front‑end to clear via `clearFrontendFileList`; thread‑safe `GLOBAL_FILE_QUEUE` with a lock.

- Packaging completeness with PyInstaller
	- Symptoms: Missing UI assets/hidden imports; icon errors.
	- Fix: Custom spec includes `ui`, `backend`, `history`, README; hidden imports for TTS/GenAI; temp favicon; frozen‑path UI resolution in `main.py`.