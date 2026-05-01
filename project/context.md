# System Architecture Analysis

## Overview

- **Project**: /home/tom/github/semcod/resplit
- **Primary Language**: md
- **Languages**: md: 13, yaml: 10, shell: 8, toml: 1, yml: 1
- **Analysis Mode**: static
- **Total Functions**: 183
- **Total Classes**: 0
- **Modules**: 36
- **Entry Points**: 183

## Architecture by Module

### SUMD
- **Functions**: 96
- **File**: `SUMD.md`

### project.map.toon
- **Functions**: 94
- **File**: `map.toon.yaml`

### testql-scenarios.generated-from-pytests.testql.toon
- **Functions**: 2
- **File**: `generated-from-pytests.testql.toon.yaml`

### docs.README
- **Functions**: 1
- **File**: `README.md`

## Key Entry Points

Main execution flows into the system:

### testql-scenarios.generated-from-pytests.testql.toon.all

### docs.README.generate_readme

### project.map.toon.walk

### project.map.toon.restore

### project.map.toon.report

### project.map.toon.dashboard

### project.map.toon.tui

### project.map.toon.version

### project.map.toon.duplicates

### project.map.toon.services

### project.map.toon.truth

### project.map.toon.plan

### project.map.toon._print_summary_table

### project.map.toon.get_cc_for_day

### project.map.toon._extract_avg_cc

### project.map.toon.generate_dashboard

### project.map.toon._render_html

### project.map.toon._load_day_results

### project.map.toon._endpoint_diff

### project.map.toon._health_bar

### project.map.toon._calc_health

### project.map.toon.launch_tui

### project.map.toon._config

### project.map.toon.test_detect_docker_compose_yml

### project.map.toon.test_detect_docker_compose_yaml

### project.map.toon.test_detect_uvicorn_via_server_py

### project.map.toon.test_detect_uvicorn_via_backend_server_py

### project.map.toon.test_detect_none_fallback

### project.map.toon.test_start_dry_run_skips_deploy

### project.map.toon.test_start_none_method_returns_true

## Process Flows

Key execution flows identified:

### Flow 1: all
```
all [testql-scenarios.generated-from-pytests.testql.toon]
```

### Flow 2: generate_readme
```
generate_readme [docs.README]
```

### Flow 3: walk
```
walk [project.map.toon]
```

### Flow 4: restore
```
restore [project.map.toon]
```

### Flow 5: report
```
report [project.map.toon]
```

### Flow 6: dashboard
```
dashboard [project.map.toon]
```

### Flow 7: tui
```
tui [project.map.toon]
```

### Flow 8: version
```
version [project.map.toon]
```

### Flow 9: duplicates
```
duplicates [project.map.toon]
```

### Flow 10: services
```
services [project.map.toon]
```

## Data Transformation Functions

Key functions that process and transform data:

### project.map.toon.test_run_processes_all_days

### project.map.toon.test_parse_openapi_returns_endpoints

### project.map.toon.test_parse_openapi_ignores_unknown_methods

### project.map.toon.test_parse_openapi_empty_paths

### project.map.toon.test_testql_strategy_parse_ok

### SUMD.test_run_processes_all_days

### SUMD.test_parse_openapi_returns_endpoints

### SUMD.test_parse_openapi_ignores_unknown_methods

### SUMD.test_parse_openapi_empty_paths

### SUMD.test_testql_strategy_parse_ok

## Public API Surface

Functions exposed as public API (no underscore prefix):

- `testql-scenarios.generated-from-pytests.testql.toon.all` - 0 calls
- `docs.README.generate_readme` - 0 calls
- `project.map.toon.walk` - 0 calls
- `project.map.toon.restore` - 0 calls
- `project.map.toon.report` - 0 calls
- `project.map.toon.dashboard` - 0 calls
- `project.map.toon.tui` - 0 calls
- `project.map.toon.version` - 0 calls
- `project.map.toon.duplicates` - 0 calls
- `project.map.toon.services` - 0 calls
- `project.map.toon.truth` - 0 calls
- `project.map.toon.plan` - 0 calls
- `project.map.toon.get_cc_for_day` - 0 calls
- `project.map.toon.generate_dashboard` - 0 calls
- `project.map.toon.launch_tui` - 0 calls
- `project.map.toon.test_detect_docker_compose_yml` - 0 calls
- `project.map.toon.test_detect_docker_compose_yaml` - 0 calls
- `project.map.toon.test_detect_uvicorn_via_server_py` - 0 calls
- `project.map.toon.test_detect_uvicorn_via_backend_server_py` - 0 calls
- `project.map.toon.test_detect_none_fallback` - 0 calls
- `project.map.toon.test_start_dry_run_skips_deploy` - 0 calls
- `project.map.toon.test_start_none_method_returns_true` - 0 calls
- `project.map.toon.test_stop_dry_run_skips` - 0 calls
- `project.map.toon.test_stop_none_method_skips` - 0 calls
- `project.map.toon.test_execute_delegates_to_start` - 0 calls
- `project.map.toon.test_get_commit_for_day_ok` - 0 calls
- `project.map.toon.test_get_commit_for_day_none` - 0 calls
- `project.map.toon.test_days_with_commits` - 0 calls
- `project.map.toon.test_load_history_empty_dir` - 0 calls
- `project.map.toon.test_load_history_no_results_json` - 0 calls
- `project.map.toon.test_load_history_single_day` - 0 calls
- `project.map.toon.test_load_history_multiple_days_sorted` - 0 calls
- `project.map.toon.test_load_history_health_pct` - 0 calls
- `project.map.toon.test_load_history_skips_invalid_dir_name` - 0 calls
- `project.map.toon.test_load_history_with_commit` - 0 calls
- `project.map.toon.test_load_history_status_timeout` - 0 calls
- `project.map.toon.test_load_history_testql_passed` - 0 calls
- `project.map.toon.test_endpoint_url` - 0 calls
- `project.map.toon.test_endpoint_url_strips_trailing_slash` - 0 calls
- `project.map.toon.test_endpoint_slug` - 0 calls

## System Interactions

How components interact:

```mermaid
graph TD
```

## Reverse Engineering Guidelines

1. **Entry Points**: Start analysis from the entry points listed above
2. **Core Logic**: Focus on classes with many methods
3. **Data Flow**: Follow data transformation functions
4. **Process Flows**: Use the flow diagrams for execution paths
5. **API Surface**: Public API functions reveal the interface

## Context for LLM

Maintain the identified architectural patterns and public API surface when suggesting changes.