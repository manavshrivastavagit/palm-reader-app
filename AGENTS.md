# Hasthrekha — Agent Guide

## Run app
```bash
streamlit run app.py
```
App serves on port 8501. Requires `GEMINI_API_KEY` in `.env` or session state sidebar input.

## Tests
```bash
python -m pytest test_app.py -v --tb=short
```
Uses `pytest` (not `unittest` runner) despite `unittest.TestCase`. No typecheck or formatter configured — only flake8 lint in CI.

## Lint (CI)
```bash
flake8 app.py test_app.py --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 app.py test_app.py --count --max-line-length=140 --statistics --exit-zero
```

## Architecture
- **Single file**: all ~2000 lines in `app.py` — Streamlit monolith with embedded HTML/JS.
- **Gemini model**: `gemini-2.5-flash`, temperature 0.8, max tokens 4096 (reading) / 2048 (chat).
- **Bilingual**: Hindi/English via `TRANSLATIONS` dict. Language switch triggers `st.rerun()`.
- **Caching**: `@st.cache_resource` wraps the GenAI client singleton.
- **Streaming**: All reads stream via `generate_content_stream()` with `yield`.
- **Structured output**: Pydantic `PalmReadingResponse` (validates + refusal guardrail).

## MediaPipe (client-side)
Embedded in `render_live_scanner()` via `components.html`:
- CDN: `unpkg.com/@mediapipe/tasks-vision@0.10.3`
- **Use `.mjs` not `.js`** — version 0.10.3 renamed `vision_bundle.js` → `vision_bundle.mjs`. A 404 means the wrong extension was used.
- WASM path: same base + `/wasm`
- Hand landmarker model: float16, delegate GPU, max 2 hands, 1280×720 camera.

## Scanning animation
Also a `components.html` embed in `render_palm_scanning_animation()`. Animated overlay featuring bezier palm lines, mount labels, particles, and a progress bar.

## CI quirks
- Requires system deps: `libgl1-mesa-glx libglib2.0-0` (for OpenCV/MediaPipe on Linux runners).
- Installs `opencv-contrib-python<4.9` separately (version-pinned).
- `.streamlit/config.toml` is gitignored — production CORS/XSRF config lives there.

## Devcontainer
Port 8501 forwarded, runs `streamlit run app.py --server.enableCORS false --server.enableXsrfProtection false`.

## Risks / gotchas
- **`.gitignore` excludes `.streamlit/config.toml` and `.streamlit/secrets.toml`** — if you add config there, agents won't see it in the repo.
- `docs/` contains business/strategy docs, not just architecture.
- `Pillow` used for image deserialization, `plotly` for any charts.
