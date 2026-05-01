<!-- code2docs:start --># resplit

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.10-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-185-green)
> **185** functions | **0** classes | **36** files | CC̄ = 0.0

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
pip install resplit[tui]    # tui features
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
├── Makefile
├── SUMD
├── PLAN
├── pyproject
├── tree
├── TODO
├── CHANGELOG
├── project
├── README
    ├── architecture
    ├── README
    ├── walk_dry_run
    ├── Makefile
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
    ├── prompt
        ├── toon
            ├── toon
            ├── toon
    ├── calls
    ├── README
    ├── context
        ├── toon
        ├── toon
        ├── toon
        ├── toon
```

## API Overview

### Functions

- `all()` — —
- `walk()` — —
- `restore()` — —
- `report()` — —
- `dashboard()` — —
- `tui()` — —
- `version()` — —
- `duplicates()` — —
- `services()` — —
- `truth()` — —
- `plan()` — —
- `get_cc_for_day()` — —
- `generate_dashboard()` — —
- `launch_tui()` — —
- `test_detect_docker_compose_yml()` — —
- `test_detect_docker_compose_yaml()` — —
- `test_detect_uvicorn_via_server_py()` — —
- `test_detect_uvicorn_via_backend_server_py()` — —
- `test_detect_none_fallback()` — —
- `test_start_dry_run_skips_deploy()` — —
- `test_start_none_method_returns_true()` — —
- `test_stop_dry_run_skips()` — —
- `test_stop_none_method_skips()` — —
- `test_execute_delegates_to_start()` — —
- `test_get_commit_for_day_ok()` — —
- `test_get_commit_for_day_none()` — —
- `test_days_with_commits()` — —
- `test_load_history_empty_dir()` — —
- `test_load_history_no_results_json()` — —
- `test_load_history_single_day()` — —
- `test_load_history_multiple_days_sorted()` — —
- `test_load_history_health_pct()` — —
- `test_load_history_skips_invalid_dir_name()` — —
- `test_load_history_with_commit()` — —
- `test_load_history_status_timeout()` — —
- `test_load_history_testql_passed()` — —
- `test_endpoint_url()` — —
- `test_endpoint_url_strips_trailing_slash()` — —
- `test_endpoint_slug()` — —
- `test_day_result_health_pct_empty()` — —
- `test_day_result_health_pct()` — —
- `test_walk_config_defaults()` — —
- `test_run_returns_empty_when_no_commits()` — —
- `test_run_day_dry_run_skips_checkout()` — —
- `test_run_day_returns_day_result()` — —
- `test_run_day_deploy_failure_skips_scan()` — —
- `test_run_day_stop_always_called()` — —
- `test_run_processes_all_days()` — —
- `test_save_json_creates_results_file()` — —
- `test_save_json_creates_endpoints_file()` — —
- `test_save_json_writes_commit_txt()` — —
- `test_save_json_no_output_dir_skips()` — —
- `test_save_json_testql_passed_field()` — —
- `test_save_html_creates_report_file()` — —
- `test_save_html_contains_health_pct()` — —
- `test_save_timeline_index_creates_index()` — —
- `test_save_timeline_index_multiple_days_sorted()` — —
- `test_find_last_working_day_found()` — —
- `test_find_last_working_day_picks_most_recent()` — —
- `test_find_last_working_day_none_when_always_fail()` — —
- `test_find_last_working_day_missing_dir()` — —
- `test_find_last_working_day_ignores_other_endpoints()` — —
- `test_find_last_working_day_skips_invalid_dirs()` — —
- `test_execute_returns_date()` — —
- `test_parse_openapi_returns_endpoints()` — —
- `test_parse_openapi_ignores_unknown_methods()` — —
- `test_parse_openapi_empty_paths()` — —
- `test_scan_via_compose_labels_finds_traefik_prefix()` — —
- `test_scan_via_compose_labels_no_compose_file()` — —
- `test_scan_via_compose_labels_dict_labels()` — —
- `test_ports_to_endpoints()` — —
- `test_ports_to_endpoints_no_services()` — —
- `test_execute_falls_back_to_health()` — —
- `test_execute_deta_takes_priority()` — —
- `test_execute_deduplicates_openapi_vs_deta()` — —
- `test_http_probe_ok()` — —
- `test_http_probe_timeout()` — —
- `test_testql_strategy_parse_ok()` — —
- `test_test_service_delegates_to_strategy()` — —
- `generate_readme()` — —
- `all()` — —
- `all()` — —
- `generate_readme()` — —
- `walk()` — —
- `restore()` — —
- `report()` — —
- `dashboard()` — —
- `tui()` — —
- `version()` — —
- `duplicates()` — —
- `services()` — —
- `truth()` — —
- `plan()` — —
- `get_cc_for_day()` — —
- `generate_dashboard()` — —
- `launch_tui()` — —
- `test_detect_docker_compose_yml()` — —
- `test_detect_docker_compose_yaml()` — —
- `test_detect_uvicorn_via_server_py()` — —
- `test_detect_uvicorn_via_backend_server_py()` — —
- `test_detect_none_fallback()` — —
- `test_start_dry_run_skips_deploy()` — —
- `test_start_none_method_returns_true()` — —
- `test_stop_dry_run_skips()` — —
- `test_stop_none_method_skips()` — —
- `test_execute_delegates_to_start()` — —
- `test_get_commit_for_day_ok()` — —
- `test_get_commit_for_day_none()` — —
- `test_days_with_commits()` — —
- `test_load_history_empty_dir()` — —
- `test_load_history_no_results_json()` — —
- `test_load_history_single_day()` — —
- `test_load_history_multiple_days_sorted()` — —
- `test_load_history_health_pct()` — —
- `test_load_history_skips_invalid_dir_name()` — —
- `test_load_history_with_commit()` — —
- `test_load_history_status_timeout()` — —
- `test_load_history_testql_passed()` — —
- `test_endpoint_url()` — —
- `test_endpoint_url_strips_trailing_slash()` — —
- `test_endpoint_slug()` — —
- `test_day_result_health_pct_empty()` — —
- `test_day_result_health_pct()` — —
- `test_walk_config_defaults()` — —
- `test_run_returns_empty_when_no_commits()` — —
- `test_run_day_dry_run_skips_checkout()` — —
- `test_run_day_returns_day_result()` — —
- `test_run_day_deploy_failure_skips_scan()` — —
- `test_run_day_stop_always_called()` — —
- `test_run_processes_all_days()` — —
- `test_save_json_creates_results_file()` — —
- `test_save_json_creates_endpoints_file()` — —
- `test_save_json_writes_commit_txt()` — —
- `test_save_json_no_output_dir_skips()` — —
- `test_save_json_testql_passed_field()` — —
- `test_save_html_creates_report_file()` — —
- `test_save_html_contains_health_pct()` — —
- `test_save_timeline_index_creates_index()` — —
- `test_save_timeline_index_multiple_days_sorted()` — —
- `test_find_last_working_day_found()` — —
- `test_find_last_working_day_picks_most_recent()` — —
- `test_find_last_working_day_none_when_always_fail()` — —
- `test_find_last_working_day_missing_dir()` — —
- `test_find_last_working_day_ignores_other_endpoints()` — —
- `test_find_last_working_day_skips_invalid_dirs()` — —
- `test_execute_returns_date()` — —
- `test_parse_openapi_returns_endpoints()` — —
- `test_parse_openapi_ignores_unknown_methods()` — —
- `test_parse_openapi_empty_paths()` — —
- `test_scan_via_compose_labels_finds_traefik_prefix()` — —
- `test_scan_via_compose_labels_no_compose_file()` — —
- `test_scan_via_compose_labels_dict_labels()` — —
- `test_ports_to_endpoints()` — —
- `test_ports_to_endpoints_no_services()` — —
- `test_execute_falls_back_to_health()` — —
- `test_execute_deta_takes_priority()` — —
- `test_execute_deduplicates_openapi_vs_deta()` — —
- `test_http_probe_ok()` — —
- `test_http_probe_timeout()` — —
- `test_testql_strategy_parse_ok()` — —
- `test_test_service_delegates_to_strategy()` — —


## Project Structure

📄 `CHANGELOG`
📄 `Makefile`
📄 `PLAN`
📄 `README`
📄 `SUMD` (96 functions)
📄 `SUMR`
📄 `TODO`
📄 `docs.README` (1 functions)
📄 `docs.architecture`
📄 `examples.01-dry-run-walk.README`
📄 `examples.01-dry-run-walk.run`
📄 `examples.02-docker-compose-project.README`
📄 `examples.02-docker-compose-project.docker-compose`
📄 `examples.02-docker-compose-project.run`
📄 `examples.03-restore-endpoint.README`
📄 `examples.03-restore-endpoint.mock_results`
📄 `examples.03-restore-endpoint.run`
📄 `examples.Makefile`
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
📄 `project.map.toon` (193 functions)
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

- 🏛️ [Architecture](./docs/architecture.md) — Architecture with diagrams
- 💡 [Examples](./examples) — Usage examples and code samples

### Generated Files

| Output | Description | Link |
|--------|-------------|------|
| `README.md` | Project overview (this file) | — |
| `docs/architecture.md` | Architecture with diagrams | [View](./docs/architecture.md) |
| `examples` | Usage examples and code samples | [View](./examples) |

<!-- code2docs:end -->