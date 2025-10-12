# DotCanvas API System

DotCanvas exposes a small HTTP API for automation workflows. This document describes how to
create and manage API tokens and how to interact with the automation endpoints.

## Authentication

All public automation endpoints require a **Bearer token**. Tokens are managed from the new
**API Tokens** page in the web console (`/ui/tokens`) or by calling the `/tokens` REST
endpoints documented below. Each token is shown **only once** when it is created—store it in a
safe place.

Include the token in the `Authorization` header of every API call:

```http
Authorization: Bearer <token-value>
```

If the token is missing, malformed, or revoked, the server responds with `401 Unauthorized` and
a `WWW-Authenticate: Bearer` header.

## Token management endpoints

| Method & Path        | Description                                     |
| ------------------- | ----------------------------------------------- |
| `GET /tokens`       | List active tokens (id, label, preview, created) |
| `POST /tokens`      | Create a new token (returns the token **once**)  |
| `DELETE /tokens/{id}` | Revoke a token by id                             |

### Create a token

```bash
curl -X POST http://localhost:8000/tokens \
  -H 'Content-Type: application/json' \
  -d '{"name": "build pipeline"}'
```

Successful responses include the plain token and a summary record:

```json
{
  "token": "uGW4R2...", 
  "record": {
    "id": "ab12cd34",
    "name": "build pipeline",
    "preview": "uGW4…8fzQ",
    "created_at": "2024-05-19T11:27:45Z"
  }
}
```

### List tokens

```bash
curl http://localhost:8000/tokens
```

The server returns the saved metadata for every token. The raw secret is **never** exposed
again.

### Revoke a token

```bash
curl -X DELETE http://localhost:8000/tokens/ab12cd34
```

If the token exists the response is `{ "status": "deleted" }`. Attempting to delete a missing
id returns `404 Not Found`.

## Automation endpoints

All automation endpoints require a valid Bearer token.

### Trigger schedules by name

```
POST /api/schedules/trigger
```

Request body:

```json
{
  "schedule_name": "morning-update",
  "params_override": {
    "date": "2024-05-19"
  }
}
```

The server reloads the configuration, finds every configured schedule whose `name` matches the
payload (across all devices—even if the schedule is disabled), renders the associated canvas,
and pushes it to the configured device(s). Any key/value pairs inside `params_override` are
merged into the stored schedule params before rendering. A successful response contains one
entry per triggered schedule including execution status, duration, and the next scheduled run:

```json
{
  "triggered": 2,
  "results": [
    {
      "task_name": "morning-update",
      "device_name": "Desk display",
      "device_id": "device-01",
      "canvas_id": "daily_overview",
      "triggered_at": "2024-05-19T11:42:12.345678",
      "status": "success",
      "duration": 1.82,
      "next_run": "2024-05-19T12:00:00"
    },
    { "task_name": "morning-update", "status": "error", "error": "..." }
  ]
}
```

If no schedules share the provided name the API returns `404`.

### Send a canvas to a specific device

```
POST /api/devices/send-canvas
```

Request body:

```json
{
  "device_name": "Office frame",
  "canvas_id": "daily_overview",
  "params": {
    "refresh": true
  }
}
```

The server validates that the named device exists, renders the requested canvas with the
optional `params`, and pushes the resulting image to the device. The response mirrors the single
execution result from the schedule trigger endpoint.

A missing device name yields `404 Not Found`. If the DotCanvas configuration does not contain a
Dot. API key the server returns `400 Bad Request`.

## Manual triggers from the configuration editor

The configuration editor now includes a **Run now** button for every saved schedule. Clicking
it calls the internal `/config/schedules/trigger` endpoint (no Bearer token required inside the
console) and runs that specific schedule immediately, using its stored params.

## Error handling

* `400 Bad Request` – malformed payloads, missing API key, or validation failures.
* `401 Unauthorized` – missing or invalid Bearer token.
* `404 Not Found` – unknown token id, device, or schedule name.
* `503 Service Unavailable` – token store could not be loaded.

Errors include a `detail` field describing the problem.
