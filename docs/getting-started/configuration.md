# Configuration

`rebuild` is configured via `rebuild.yaml` in the repository root.

## Full example

```yaml
project:
  days: 14
  deploy:
    method: none                          # none | docker-compose | auto | custom
    health_url: http://localhost:8000/health
    health_timeout: 120                   # seconds
    health_interval: 5
    health_verbose: false
    retry_attempts: 3
    retry_backoff_seconds: 2.0
    retry_backoff_multiplier: 2.0
    compose_file: docker-compose.yml
  output: .rebuild
  base_url: http://localhost:8000
  screenshots: false
  service: backend                        # docker-compose service name
  replay: false
  patch_dir: .rebuild/patches

  # Authentication
  auth:
    Authorization: "Bearer ${TOKEN}"
  login_url: http://localhost:8000/api/auth/login
  login_payload:
    username: admin
    password: secret

  # Test fixtures — substituted into {param} URL templates
  fixtures:
    user_id: "42"
    item_id: "1"

  # Per-endpoint request bodies
  test_bodies:
    "POST /api/items":
      name: test_item
      quantity: 1
```

## CLI overrides

Any `rebuild.yaml` value can be overridden on the command line:

```bash
rebuild walk . --days 7 --deploy none --health-url http://localhost:9000/health
```

CLI options always take precedence over `rebuild.yaml`.

## Validation

`rebuild.yaml` is validated using a Pydantic schema on every `walk` run.
Invalid configs abort with a clear error message:

```
✗ rebuild.yaml zawiera błędy:
  • project.deploy.method: invalid value 'ftp'; allowed: ['auto', 'custom', 'docker-compose', 'none']
```

You can also validate manually:

```python
from rebuild.infrastructure.config_schema import load_and_validate
from pathlib import Path

config, errors = load_and_validate(Path("rebuild.yaml"))
if errors:
    for e in errors:
        print(e)
```
