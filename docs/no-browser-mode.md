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
* All management endpoints that back the browser UI (canvas editing, logs, daemon control,
  configuration, and token CRUD) return `403 Forbidden`.
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

## Managing tokens without the UI

Because the `/tokens` endpoints are disabled in no-browser mode, create or revoke API tokens
directly on the server. The `TokenStore` utility used by the application can be executed from the
command line:

```bash
uv run python - <<'PY'
from src.token_store import TokenStore

store = TokenStore()
token, record = store.create_token(name="automation")
print("Token:", token)
print("Metadata:", record)
PY
```

The script prints the new token (copy it immediately) and its metadata. To revoke a token call
`store.delete_token("token-id")` in a similar one-off script or edit `configs/tokens.json`
manually.

## Security considerations for headless deployments

Running DotCanvas without the browser requires the same diligence as any other API-only service:

* **Protect network access.** Restrict inbound traffic with a firewall or reverse proxy and use
  HTTPS when exposing the API to the internet.
* **Secure configuration volumes.** The `configs/` directory contains the Dot API key and token
  database—mount it with least-privilege permissions.
* **Rotate credentials.** Revoke unused tokens promptly and change the Dot API key if you suspect
  compromise.
* **Monitor logs.** Cloud platforms can forward the FastAPI logs to a managed logging service for
  auditing failed or unexpected requests.

## Returning to the full UI

Unset the environment variable (or set it to `0`/`false`) and restart the server to restore the
browser-based management console.
