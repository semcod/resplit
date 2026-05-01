<!-- code2docs:start --># resplit

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.10-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-244-green)
> **244** functions | **0** classes | **32** files | CC̄ = 0.0

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
├── goal
├── SUMD
├── PLAN
├── pyproject
├── tree
├── CHANGELOG
├── project
├── README
    ├── README
    ├── walk_dry_run
    ├── restore_endpoint
        ├── run
        ├── mock_results
        ├── README
        ├── run
        ├── docker-compose
        ├── README
        ├── run
        ├── README
        ├── toon
            ├── toon
            ├── toon
    ├── context
    ├── prompt
        ├── toon
    ├── calls
        ├── toon
        ├── toon
        ├── toon
    ├── README
        ├── toon
```

## API Overview

### Functions

- `detect_deploy_method()` — —
- `start()` — —
- `stop()` — —
- `walk()` — —
- `restore()` — —
- `report()` — —
- `version()` — —
- `dashboard()` — —
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
- `dashboard()` — —
- `get_cc_for_day()` — —
- `generate_dashboard()` — —
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
- `take_screenshot()` — —
- `take_screenshots_batch()` — —
- `screenshot_endpoint()` — —
- `run_tests()` — —
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
- `test_find_last_working_day_found()` — —
- `test_find_last_working_day_not_found()` — —
- `test_find_backend_files()` — —
- `test_is_page_endpoint()` — —
- `test_take_screenshot_playwright_not_installed()` — —
- `test_take_screenshot_success()` — —
- `test_take_screenshot_retry_then_succeed()` — —
- `test_take_screenshot_all_retries_fail()` — —
- `test_screenshot_endpoint_returns_path_on_success()` — —
- `test_screenshot_endpoint_returns_none_on_failure()` — —
- `test_take_screenshots_batch_playwright_missing()` — —
- `test_testql_available_missing()` — —
- `test_testql_available_ok()` — —
- `test_parse_testql_results_ok()` — —
- `test_parse_testql_results_fail()` — —
- `test_parse_testql_results_missing_endpoint()` — —
- `test_run_http_probe_skip_non_get()` — —
- `test_run_http_probe_ok()` — —
- `test_run_http_probe_timeout()` — —
- `test_run_tests_uses_http_probe_when_no_testql_dir()` — —
- `test_fallback_all_timeout()` — —
- `generate_readme()` — —
- `all()` — —
- `all()` — —
- `detect_deploy_method()` — —
- `start()` — —
- `stop()` — —
- `walk()` — —
- `restore()` — —
- `report()` — —
- `version()` — —
- `dashboard()` — —
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
- `generate_readme()` — —
- `get_cc_for_day()` — —
- `generate_dashboard()` — —
- `find_last_working_day()` — —
- `extract_endpoint()` — —
- `take_screenshot()` — —
- `take_screenshots_batch()` — —
- `screenshot_endpoint()` — —
- `run_tests()` — —
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
- `test_find_last_working_day_found()` — —
- `test_find_last_working_day_not_found()` — —
- `test_find_backend_files()` — —
- `test_is_page_endpoint()` — —
- `test_take_screenshot_playwright_not_installed()` — —
- `test_take_screenshot_success()` — —
- `test_take_screenshot_retry_then_succeed()` — —
- `test_take_screenshot_all_retries_fail()` — —
- `test_screenshot_endpoint_returns_path_on_success()` — —
- `test_screenshot_endpoint_returns_none_on_failure()` — —
- `test_take_screenshots_batch_playwright_missing()` — —
- `test_testql_available_missing()` — —
- `test_testql_available_ok()` — —
- `test_parse_testql_results_ok()` — —
- `test_parse_testql_results_fail()` — —
- `test_parse_testql_results_missing_endpoint()` — —
- `test_run_http_probe_skip_non_get()` — —
- `test_run_http_probe_ok()` — —
- `test_run_http_probe_timeout()` — —
- `test_run_tests_uses_http_probe_when_no_testql_dir()` — —
- `test_fallback_all_timeout()` — —


## Project Structure

📄 `CHANGELOG`
📄 `PLAN`
📄 `README`
📄 `SUMD` (139 functions)
📄 `SUMR` (35 functions)
📄 `docs.README` (1 functions)
📄 `examples.01-dry-run-walk.README`
📄 `examples.01-dry-run-walk.run`
📄 `examples.02-docker-compose-project.README`
📄 `examples.02-docker-compose-project.docker-compose`
📄 `examples.02-docker-compose-project.run`
📄 `examples.03-restore-endpoint.README`
📄 `examples.03-restore-endpoint.mock_results`
📄 `examples.03-restore-endpoint.run`
📄 `examples.restore_endpoint`
📄 `examples.walk_dry_run`
📄 `goal`
📄 `project`
📄 `project.README`
📄 `project.analysis.toon`
📄 `project.calls`
📄 `project.calls.toon`
📄 `project.context`
📄 `project.duplication.toon`
📄 `project.evolution.toon`
📄 `project.map.toon` (279 functions)
📄 `project.project.toon`
📄 `project.prompt`
📄 `pyproject`
📄 `testql-scenarios.generated-cli-tests.testql.toon`
📄 `testql-scenarios.generated-from-pytests.testql.toon` (2 functions)
📄 `tree`

## Requirements

- Python >= >=3.10
- typer >=0.12- rich >=13- gitpython >=3.1- httpx >=0.27- pyyaml >=6- pydantic >=2- deta >=0.1- goal >=2.1.0- costs >=0.1.20- pfix >=0.1.60

## Contributing

**Contributors:**
- Tom Softreck <tom@sapletta.com>
- Tom Sapletta <tom-sapletta-com@users.noreply.github.com>

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