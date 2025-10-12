# No-browser mode

DotCanvas can run in an API-only mode, which disables the embedded web interface and serves
only the automation endpoints. This mode is suitable for headless or cloud deployments where
the admin UI is unnecessary.

## Enabling no-browser mode

Set the `DOTCANVAS_NO_BROWSER` environment variable to a truthy value before starting the
FastAPI application or the Docker container. Valid values are `1`, `true`, `yes`, or `on`
(case-insensitive).

### Local uvicorn example

```bash
export DOTCANVAS_NO_BROWSER=1
uvicorn server:app --host 0.0.0.0 --port 8000
```

With the variable enabled:

* Static frontend assets are not mounted.
* `/`, `/ui`, and `/ui/*` routes return an informative JSON response or `404`.
* The OpenAPI docs (`/docs`) and automation endpoints remain available.

### Docker example

```bash
docker run -d \
  -e DOTCANVAS_NO_BROWSER=1 \
  -p 8000:8000 \
  -v $(pwd)/configs:/app/configs \
  -v $(pwd)/canvas:/app/canvas \
  ghcr.io/lucasxingg/dotcanvas:latest
```

When the container starts it logs `Running in no-browser mode; frontend routes are disabled.`
and the landing page at `http://localhost:8000/` returns a short JSON message that points to the
OpenAPI documentation.

## Returning to the full UI

Unset the environment variable (or set it to `0`/`false`) and restart the server to restore the
browser-based management console.
