# rebuild.yaml Reference

Full field reference for `rebuild.yaml`.

## Schema

All fields are optional. A minimal valid config is just `project: {}`.

```yaml
project:
  days: <int ≥1>
  deploy:
    method: none | docker-compose | auto | custom
    health_url: <str>
    health_timeout: <int ≥1>          # seconds
    health_interval: <int ≥1>         # seconds between polls
    health_verbose: <bool>
    retry_attempts: <int ≥1>
    retry_backoff_seconds: <float ≥0>
    retry_backoff_multiplier: <float ≥1>
    compose_file: <str>               # path to docker-compose.yml
  output: <str>                       # or {dir: <str>}
  base_url: <str>
  screenshots: <bool>
  service: <str>                      # docker-compose service name
  replay: <bool>
  patch_dir: <str>

auth:
  <Header-Name>: <value>

login_url: <str>
login_payload:
  <key>: <value>

test_fixtures:
  <param_name>: <value>

test_bodies:
  "METHOD /path":
    <key>: <value>
```

## Field descriptions

### `project.days`
Number of days of git history to walk. Default: `30`.

### `project.deploy.method`
How to deploy each commit:

| Value | Behaviour |
|---|---|
| `none` | Don't deploy — test against already-running stack |
| `docker-compose` | `docker compose up --build` per commit |
| `auto` | Auto-detect based on repo contents |
| `custom` | Run `deploy.sh` in repo root |

### `project.deploy.health_url`
URL polled to determine if the service is ready. Default: `http://localhost:8000/health`.

### `project.deploy.health_timeout`
Maximum seconds to wait for health check to pass. Default: `60`.

### `project.auth`
HTTP headers added to every endpoint request. Can use `${ENV_VAR}` substitution.

### `project.test_fixtures`
Key-value pairs substituted into `{param}` placeholders in endpoint paths.

### `project.test_bodies`
Per-endpoint JSON bodies for `POST`/`PUT`/`PATCH` requests. Key format: `"METHOD /path"`.
