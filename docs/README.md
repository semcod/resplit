<!-- code2docs:start --># resplit

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.10-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-240-green)
> **240** functions | **9** classes | **34** files | CC̄ = 4.6

> Auto-generated project documentation from source code analysis.

**Author:** Tom Sapletta  
**License:** Apache-2.0[(LICENSE)](./LICENSE)  
**Repository:** [https://github.com/semcod/resplit](https://github.com/semcod/resplit)

## Installation

### From PyPI

```bash
pip install resplit
```

### From Source

```bash
git clone https://github.com/semcod/resplit
cd resplit
pip install -e .
```

### Optional Extras

```bash
pip install resplit[screenshots]    # screenshots features
pip install resplit[full]    # full features
pip install resplit[dev]    # development tools
```

## Quick Start

### CLI Usage

```bash
# Generate full documentation for your project
resplit ./my-project

# Only regenerate README
resplit ./my-project --readme-only

# Preview what would be generated (no file writes)
resplit ./my-project --dry-run

# Check documentation health
resplit check ./my-project

# Sync — regenerate only changed modules
resplit sync ./my-project
```

### Python API

```python
from resplit import generate_readme, generate_docs, Code2DocsConfig

# Quick: generate README
generate_readme("./my-project")

# Full: generate all documentation
config = Code2DocsConfig(project_name="mylib", verbose=True)
docs = generate_docs("./my-project", config=config)
```




## Architecture

```
resplit/
├── SUMR
├── SUMD
├── PLAN
├── pyproject
├── tree
├── project
├── README
    ├── README
    ├── walk_dry_run
    ├── resplit
    ├── restore_endpoint
        ├── toon
            ├── toon
            ├── toon
    ├── tester
    ├── dashboard
    ├── cli
    ├── restorer
    ├── git_walker
    ├── reporter
    ├── deployer
├── resplit/
    ├── models
    ├── screenshotter
    ├── endpoint_scanner
    ├── prompt
        ├── toon
    ├── context
        ├── toon
        ├── toon
        ├── toon
    ├── README
    ├── calls
        ├── toon
```

## API Overview

### Classes

- **`DeployMethod`** — —
- **`EndpointStatus`** — —
- **`CommitInfo`** — —
- **`Endpoint`** — —
- **`EndpointResult`** — —
- **`DayResult`** — —
- **`WalkConfig`** — —
- **`ScreenshotConfig`** — —
- **`ScreenshotResult`** — —

### Functions

- `detect_deploy_method()` — —
- `start()` — —
- `stop()` — —
- `walk()` — —
- `restore()` — —
- `report()` — —
- `version()` — —
- `scan_endpoints()` — —
- `get_commit_for_day()` — —
- `iter_days()` — —
- `checkout()` — —
- `restore_head()` — —
- `days_with_commits()` — —
- `save_json()` — —
- `save_html()` — —
- `save_day()` — —
- `save_timeline_index()` — —
- `all()` — —
- `walk()` — —
- `restore()` — —
- `report()` — —
- `version()` — —
- `detect_deploy_method()` — —
- `start()` — —
- `stop()` — —
- `scan_endpoints()` — —
- `get_commit_for_day()` — —
- `iter_days()` — —
- `checkout()` — —
- `restore_head()` — —
- `days_with_commits()` — —
- `save_json()` — —
- `save_html()` — —
- `save_day()` — —
- `save_timeline_index()` — —
- `find_last_working_day()` — —
- `extract_endpoint()` — —
- `test_detect_docker_compose_yml()` — —
- `test_detect_docker_compose_yaml()` — —
- `test_detect_uvicorn_server()` — —
- `test_detect_uvicorn_backend_server()` — —
- `test_detect_none()` — —
- `test_parse_openapi()` — —
- `test_ports_to_endpoints()` — —
- `test_scan_via_compose_labels()` — —
- `test_scan_endpoints_minimal_fallback()` — —
- `test_get_commit_for_day_parses_output()` — —
- `test_get_commit_for_day_no_output()` — —
- `test_get_commit_for_day_git_error()` — —
- `test_days_with_commits_filters_none()` — —
- `test_endpoint_url()` — —
- `test_endpoint_url_strips_trailing_slash()` — —
- `test_endpoint_slug()` — —
- `test_day_result_health_pct_empty()` — —
- `test_day_result_health_pct()` — —
- `test_walk_config_defaults()` — —
- `test_save_json_creates_files()` — —
- `test_save_json_results_content()` — —
- `test_save_html_creates_report()` — —
- `test_save_timeline_index()` — —
- `generate_readme()` — —
- `all()` — —
- `run_tests(endpoints, config, day_dir)` — Testuje listę endpointów.
- `get_cc_for_day(repo, day)` — Wywołuje `toon <repo> --format json` i zwraca średnie CC dla danego dnia.
- `generate_dashboard(results, output_dir, repo)` — Generuje dashboard.html w output_dir.
- `walk(repo, days, date_from, date_to)` — Przejdź historię git dzień po dniu, deployuj i testuj endpointy.
- `restore(endpoint, repo, output, results_dir)` — Przywróć działający endpoint jako izolowany projekt.
- `report(results_dir)` — Wygeneruj zbiorczy raport z istniejących wyników.
- `version()` — Pokaż wersję resplit.
- `dashboard(results_dir, repo)` — Wygeneruj dashboard porównawczy: timeline health% + CC.
- `find_last_working_day(endpoint_path, results_dir)` — Przeszukuje wyniki walk i zwraca ostatni dzień,
- `extract_endpoint(repo, endpoint_path, working_day, target)` — Wyodrębnia endpoint do izolowanego projektu.
- `get_commit_for_day(repo, day, earliest)` — Zwraca CommitInfo dla danego dnia.
- `iter_days(config)` — Generator: (day, CommitInfo|None) dla każdego dnia w przedziale.
- `checkout(repo, sha)` — Checkout konkretnego commitu (detached HEAD).
- `restore_head(repo)` — Wróć do HEAD (np. main/master po zakończeniu walk).
- `days_with_commits(config)` — Zwraca tylko dni, które mają przynajmniej jeden commit.
- `save_json(result)` — —
- `save_html(result)` — —
- `save_day(result)` — Zapisuje pełny raport dnia: JSON + HTML.
- `save_timeline_index(results, output_dir)` — Generuje .resplit/index.html z timelineą wszystkich dni.
- `detect_deploy_method(repo)` — Automatycznie wykrywa metodę deployu na podstawie plików w repo.
- `start(repo, config)` — Uruchamia usługę. Zwraca True jeśli sukces.
- `stop(repo, config)` — Zatrzymuje usługę.
- `take_screenshot(url, filename, cfg)` — Robi screenshot URL i zapisuje do cfg.output_dir/filename.
- `take_screenshots_batch(urls, cfg)` — Batch screenshots. urls = [(url, filename), ...].
- `screenshot_endpoint(url, slug, screenshots_dir)` — Uproszczony wrapper używany przez cli.py walk.
- `scan_endpoints(repo, config)` — Zwraca listę Endpoint wykrytych dla danego commitu/deployu.
- `walk()` — —
- `restore()` — —
- `report()` — —
- `version()` — —
- `dashboard()` — —
- `save_json()` — —
- `save_html()` — —
- `save_day()` — —
- `save_timeline_index()` — —
- `scan_endpoints()` — —
- `find_last_working_day()` — —
- `extract_endpoint()` — —
- `get_commit_for_day()` — —
- `iter_days()` — —
- `checkout()` — —
- `restore_head()` — —
- `days_with_commits()` — —
- `run_tests()` — —
- `detect_deploy_method()` — —
- `start()` — —
- `stop()` — —
- `get_cc_for_day()` — —
- `generate_dashboard()` — —
- `take_screenshot()` — —
- `take_screenshots_batch()` — —
- `screenshot_endpoint()` — —
- `generate_readme()` — —
- `all()` — —
- `test_detect_docker_compose_yml()` — —
- `test_detect_docker_compose_yaml()` — —
- `test_detect_uvicorn_server()` — —
- `test_detect_uvicorn_backend_server()` — —
- `test_detect_none()` — —
- `test_parse_openapi()` — —
- `test_ports_to_endpoints()` — —
- `test_scan_via_compose_labels()` — —
- `test_scan_endpoints_minimal_fallback()` — —
- `test_get_commit_for_day_parses_output()` — —
- `test_get_commit_for_day_no_output()` — —
- `test_get_commit_for_day_git_error()` — —
- `test_days_with_commits_filters_none()` — —
- `test_endpoint_url()` — —
- `test_endpoint_url_strips_trailing_slash()` — —
- `test_endpoint_slug()` — —
- `test_day_result_health_pct_empty()` — —
- `test_day_result_health_pct()` — —
- `test_walk_config_defaults()` — —
- `test_save_json_creates_files()` — —
- `test_save_json_results_content()` — —
- `test_save_html_creates_report()` — —
- `test_save_timeline_index()` — —


## Project Structure

📄 `PLAN`
📄 `README`
📄 `SUMD` (141 functions)
📄 `SUMR` (35 functions)
📄 `docs.README` (1 functions)
📄 `examples.resplit`
📄 `examples.restore_endpoint`
📄 `examples.walk_dry_run`
📄 `project`
📄 `project.README`
📄 `project.analysis.toon`
📄 `project.calls`
📄 `project.calls.toon`
📄 `project.context`
📄 `project.duplication.toon`
📄 `project.evolution.toon`
📄 `project.map.toon` (338 functions)
📄 `project.project.toon`
📄 `project.prompt`
📄 `pyproject`
📦 `resplit`
📄 `resplit.cli` (8 functions)
📄 `resplit.dashboard` (4 functions)
📄 `resplit.deployer` (9 functions)
📄 `resplit.endpoint_scanner` (6 functions)
📄 `resplit.git_walker` (6 functions)
📄 `resplit.models` (7 classes)
📄 `resplit.reporter` (6 functions)
📄 `resplit.restorer` (5 functions)
📄 `resplit.screenshotter` (5 functions, 2 classes)
📄 `resplit.tester` (6 functions)
📄 `testql-scenarios.generated-cli-tests.testql.toon`
📄 `testql-scenarios.generated-from-pytests.testql.toon` (2 functions)
📄 `tree`

## Requirements

- Python >= >=3.10
- typer >=0.12- rich >=13- gitpython >=3.1- httpx >=0.27- pyyaml >=6- pydantic >=2- deta >=0.1

## Contributing

**Contributors:**
- Tom Sapletta <tom-sapletta-com@users.noreply.github.com>
- Tom Softreck <tom@sapletta.com>

We welcome contributions! Open an issue or pull request to get started.
### Development Setup

```bash
# Clone the repository
git clone https://github.com/semcod/resplit
cd resplit

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## Documentation

- 💡 [Examples](./examples) — Usage examples and code samples

### Generated Files

| Output | Description | Link |
|--------|-------------|------|
| `README.md` | Project overview (this file) | — |
| `examples` | Usage examples and code samples | [View](./examples) |

<!-- code2docs:end -->