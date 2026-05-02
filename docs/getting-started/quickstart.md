# Quick Start

## 1. Initialise your project

```bash
rebuild init /path/to/my-service
```

This creates:

- `rebuild.yaml` — configuration file
- `.env` — environment variables (API keys, etc.)

## 2. Configure `rebuild.yaml`

```yaml
project:
  days: 14
  deploy:
    method: none          # or docker-compose, auto
    health_url: http://localhost:8000/health
    health_timeout: 60
  base_url: http://localhost:8000
  screenshots: false
```

## 3. Run your first walk

```bash
# Dry-run: walk history without deploying
rebuild walk /path/to/my-service --deploy none --days 7 --dry-run
```

With a running Docker Compose stack:

```bash
rebuild walk /path/to/my-service --deploy docker-compose --days 30
```

## 4. View the results

```bash
# Serve results on http://localhost:7821
rebuild serve --results-dir /path/to/my-service/.rebuild

# Or open the generated index.html directly
open /path/to/my-service/.rebuild/index.html
```

## 5. Analyse code quality

```bash
# Find duplicate code
rebuild analyze duplicates /path/to/my-service

# Build service dependency graph
rebuild analyze services /path/to/my-service

# Generate refactoring plan
rebuild refactor plan /path/to/my-service
```
