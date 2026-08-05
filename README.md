# caspyan

A lightweight **CAS mock server** for test scenarios.


## Quick start

```bash
uv run caspyan
```

Server starts on `http://localhost:8080`.

## Usage

Point your CAS client to:

```
http://localhost:8080/cas/login?service=https://your-app.example.com
```

### Authentication

The mock server accepts any credentials where **username equals password**. For obvious reasons, this disqualifies it from use outside development testing.

| Username | Password | Result |
|----------|----------|--------|
| `john` | `john` | Success |
| `john` | `wrong` | 401 |
| `john` | `fail` | 401 |
| _(empty)_ | anything | 401 |

### Endpoints

| Path | Method | Description |
|------|--------|-------------|
| `/cas/login` | GET | Login form, or redirect with ticket if already authenticated |
| `/cas/login` | POST | Submit credentials |
| `/cas/logout` | GET/POST | Logout page / perform logout |
| `/cas/serviceValidate` | GET | CAS 2.0 ticket validation (XML) |
| `/cas/proxyValidate` | GET | CAS 2.0 proxy ticket validation (XML) |
| `/cas/p3/serviceValidate` | GET | CAS 3.0 ticket validation (XML) |
| `/cas/p3/proxyValidate` | GET | CAS 3.0 proxy ticket validation (XML) |

### CAS protocol flow

```
App ──► GET /cas/login?service={url}
         └─► Login form (if not authenticated)
         └─► 302 {url}?ticket=ST-... (if already authenticated)

App ──► POST /cas/login?service={url}
         └─► 302 /cas/login?service={url} (on success)

App ──► GET /cas/serviceValidate?ticket=ST-...&service={url}
         └─► XML success/failure response
```

## Attribute release

Set the `ATTRIBUTES_JSON_URL` environment variable to a JSON file URL to release user attributes.

```json
{
  "DEFAULT": {
    "attributes": {
      "affiliation": "employee",
      "groupMembership": "valid-user"
    }
  },
  "john": {
    "inherit": "DEFAULT",
    "attributes": {
      "uid": 1,
      "displayName": "John Doe",
      "groupMembership": ["admin", "power-user"]
    }
  }
}
```

Each user entry can `"inherit"` from another entry to avoid repetition.

### DEFAULT fallback and merge controls

Two environment variables adjust how the `DEFAULT` entry interacts with other users.

| Variable | Default | Description |
|----------|---------|-------------|
| `CAS_ATTRIBUTES_DEFAULT_FALLBACK` | `false` | When `true`, users not found in the attributes file receive the `DEFAULT` entry's attributes automatically |
| `CAS_ATTRIBUTES_MERGE_DEFAULT` | `false` | When `true`, listed users get the `DEFAULT` entry's attributes as a baseline, with their own attributes overriding where keys conflict |

**Example with both enabled** (`CAS_ATTRIBUTES_DEFAULT_FALLBACK=true`, `CAS_ATTRIBUTES_MERGE_DEFAULT=true`):

```json
{
  "DEFAULT": {
    "attributes": {
      "affiliation": "employee",
      "groupMembership": "valid-user"
    }
  },
  "jane": {
    "attributes": {
      "affiliation": "faculty"
    }
  }
}
```

- `bob` (not listed) → `affiliation=employee`, `groupMembership=valid-user` (fallback)
- `jane` (listed) → `affiliation=faculty`, `groupMembership=valid-user` (merged, override)

## Docker

```bash
docker build -t caspyan .
docker run -dp 8080:8080 caspyan
```

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8080` | Listen port |
| `LOG_LEVEL` | `info` | Uvicorn log level |
| `ATTRIBUTES_JSON_URL` | _(none)_ | URL to JSON attributes file |
| `CAS_ATTRIBUTES_DEFAULT_FALLBACK` | `false` | Give unlisted users the `DEFAULT` entry's attributes |
| `CAS_ATTRIBUTES_MERGE_DEFAULT` | `false` | Merge `DEFAULT` attributes into listed users' attributes |

## Development

```bash
uv sync          # install deps
uv run ruff check src/ tests/   # lint
uv run ruff format src/ tests/  # format
uv run pytest    # run tests
```
