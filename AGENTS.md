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
- **Single file**: ~2500 lines in `app.py` — Streamlit monolith with embedded HTML/JS.
- **Gemini model**: `gemini-2.5-flash`, temperature 0.8, max tokens 4096 (reading) / 2048 (chat).
- **Bilingual**: Hindi/English via `TRANSLATIONS` dict. Language switch triggers `st.rerun()`.
- **Caching**: `@st.cache_resource` wraps the GenAI client singleton.
- **Streaming**: All reads stream via `generate_content_stream()` with `yield`.
- **Structured output**: Pydantic `PalmReadingResponse` (validates + refusal guardrail).
- **Two-phase image upload**: `client.files.upload()` (JPEG) → `Part.from_bytes()` (JPEG) fallback.

## Hand Cropping (server-side, Python)
`crop_hand_image()` + `_detect_hand_bbox()` in `app.py`:
- **YCrCb skin segmentation** (Cr 133-173, Cb 77-127) — zero native deps
- **BFS flood-fill from image center** — isolates the palm from skin-coloured backgrounds
- **Tightens bbox** with 6% padding; limits tall boxes (arm) to 1.4× width
- **Weighted mask compositing** onto `(10,10,26)` dark background
- Falls back to PIL-only center-crop if no hand detected
- Logs bbox dimensions; stores debug overlay with green bbox to `session_state["_debug_bbox_img"]`

## Live Hand Scanner (client-side, browser JS)
Embedded in `render_live_scanner()` via `components.html`:
- CDN: `unpkg.com/@mediapipe/tasks-vision@0.10.3`
- **Use `.mjs` not `.js`** — version 0.10.3 renamed `vision_bundle.js` → `vision_bundle.mjs`. A 404 means the wrong extension was used.
- WASM path: same base + `/wasm`
- Hand landmarker model: float16, delegate GPU, max 2 hands, 1280×720 camera.
- **Auto-capture**: ~20 stable frames of an open palm (≥3 fingers extended) → captures JPEG frame via canvas → displays below live feed → sends back to Streamlit via `postMessage({type: 'streamlit:setComponentValue'})`.
- **Green glow bbox** drawn around each detected hand from landmark extents with 4% padding.

## Scanning animation
Also a `components.html` embed in `render_palm_scanning_animation()`. Animated overlay featuring bezier palm lines, mount labels, particles, and a progress bar.

## CI quirks
- Requires system deps: `libgl1-mesa-glx libglib2.0-0` (for OpenCV/MediaPipe on Linux runners).
- Installs `opencv-contrib-python<4.9` separately (version-pinned).
- `.streamlit/config.toml` is gitignored — production CORS/XSRF config lives there.
- `packages.txt` uses `libgl1` (not `libgl1-mesa-glx`) and `libglib2.0-0t64` (not `libglib2.0-0`) for Ubuntu 24.04.

## Devcontainer
Port 8501 forwarded, runs `streamlit run app.py --server.enableCORS false --server.enableXsrfProtection false`.

## Risks / gotchas
- **`st.components.v1.html` deprecated** — planned removal 2026-06-01. Both live scanner and scanning animation use it. When removed, need to migrate to `st.iframe` with `srcdoc` (may break `getUserMedia` camera access due to opaque-origin restrictions).
- **`.gitignore` excludes `.streamlit/config.toml` and `.streamlit/secrets.toml`** — if you add config there, agents won't see it in the repo.
- `docs/` contains business/strategy docs, not just architecture.
- `Pillow` used for image deserialization, `plotly` for any charts.
