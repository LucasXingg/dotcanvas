# AGENTS.md

## Cursor Cloud specific instructions

DotCanvas is a lightweight canvas editor for the "Dot." e-ink device. It has two parts:

- Backend: FastAPI app in `server.py` (Python 3.12, managed with `uv`), run via `uvicorn`. It renders 296x152 PNG previews with Pillow/cairosvg and runs a scheduling daemon (APScheduler). System libs for cairosvg (cairo/pango/gdk-pixbuf/libffi) are preinstalled on the base image.
- Frontend: Vite + React SPA in `frontend/` (Node), served under the `/ui` base path.

Layout split:
- `canvas/` holds **only** user canvas modules (`*.py`).
- Framework (base canvas, views, template, manager, `install_package`) lives in `src/canvas_runtime/`.

The startup update script already runs `uv sync` (backend deps into `.venv`) and `npm install` in `frontend/`. Standard run/build commands live in `README.md` and `frontend/package.json`; prefer those. Notes below are non-obvious gotchas.

### Running the services
- Backend (dev, hot reload): `source .venv/bin/activate && uvicorn server:app --host 0.0.0.0 --port 8000 --reload`
- Frontend build (needed to serve the UI through the backend): `cd frontend && npm run build` — outputs `frontend/dist/` (gitignored). The backend serves the built SPA at `http://localhost:8000/ui/daemon`.
- Frontend dev server (HMR for UI shell): `cd frontend && npm run dev` → `http://localhost:5173/ui/`.

### Non-obvious gotchas
- The Vite dev server (`:5173`) does NOT proxy API calls. The React app fetches relative paths like `/canvases`, `/config`, so those requests hit `:5173` and 404. To exercise the full app end-to-end (canvas editing, preview, daemon, config), run `npm run build` and use the backend-served UI at `http://localhost:8000/ui/...`. The `:5173` dev server is only useful for iterating on non-API UI.
- `configs/config.yaml` is gitignored. Prefer `cp configs/config-example.yaml configs/config.yaml` for local edits, but an empty/missing file is fine too: `ServercConfig` auto-seeds `config.yaml` (and `config-example.yaml`) from an embedded template — important when Docker mounts an empty host `configs/` over `/app/configs`.
- Canvas definitions are Python modules written to `canvas/*.py` at runtime and are gitignored (except the demo canvases). Creating/editing a canvas in the UI writes files to disk; live preview only refreshes after saving. User canvases import framework via `from src.canvas_runtime.base_canvas import _BaseCanvas`.
- There is no automated test suite and no configured linter (ESLint is a listed frontend dep but has no config or `lint` script). Validate changes by running the app and rendering previews.
- Canvas views can install extra Python packages at runtime via `install_package(...)` into a gitignored `user_site/` directory; `uv` venvs omit pip, so the package manager bootstraps pip via `ensurepip` on first use.
