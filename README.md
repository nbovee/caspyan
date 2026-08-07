# caspyan

A lightweight **CAS mock server** for test scenarios.

## Quick start

```bash
docker pull nbovee/caspyan
docker run -dp 8080:8080 nbovee/caspyan
```

Point your app to:

```
http://localhost:8080/cas/login?service=http://your-app.example.com
```

## Details

The mock server accepts any credentials where **username equals password**. For obvious reasons, this disqualifies it from use outside development testing.

| Username  | Password | Result  |
| --------- | -------- | ------- |
| `john`    | `john`   | Success |
| `john`    | `wrong`  | 401     |
| `john`    | `fail`   | 401     |
| _(empty)_ | anything | 401     |

Environment variables:

| Variable                          | Default   | Description                                                 |
| --------------------------------- | --------- | ----------------------------------------------------------- |
| `HOST`                            | `0.0.0.0` | Bind address                                                |
| `PORT`                            | `8080`    | Listen port                                                 |
| `LOG_LEVEL`                       | `info`    | Uvicorn log level                                           |
| `ATTRIBUTES_JSON_URL`             | _(none)_  | URL to JSON attributes file                                 |
| `CAS_ATTRIBUTES_DEFAULT_FALLBACK` | `false`   | Return `DEFAULT` dict instead of empty for an unlisted user |
| `CAS_ATTRIBUTES_MERGE_DEFAULT`    | `false`   | Update `DEFAULT` dict with user' and return                 |

Set the `ATTRIBUTES_JSON_URL` environment variable to a JSON file URL to provide user attributes.

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

### Endpoints

| Path                      | Method   | Description                                                  |
| ------------------------- | -------- | ------------------------------------------------------------ |
| `/cas/login`              | GET      | Login form, or redirect with ticket if already authenticated |
| `/cas/login`              | POST     | Submit credentials                                           |
| `/cas/logout`             | GET/POST | Logout page / perform logout                                 |
| `/cas/serviceValidate`    | GET      | CAS 2.0 ticket validation (XML)                              |
| `/cas/proxyValidate`      | GET      | CAS 2.0 proxy ticket validation (XML)                        |
| `/cas/p3/serviceValidate` | GET      | CAS 3.0 ticket validation (XML)                              |
| `/cas/p3/proxyValidate`   | GET      | CAS 3.0 proxy ticket validation (XML)                        |
