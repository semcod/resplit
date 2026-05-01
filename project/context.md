# System Architecture Analysis

## Overview

- **Project**: /home/tom/github/semcod/resplit
- **Primary Language**: md
- **Languages**: md: 11, yaml: 10, shell: 8, txt: 1, toml: 1
- **Analysis Mode**: static
- **Total Functions**: 242
- **Total Classes**: 0
- **Modules**: 32
- **Entry Points**: 242

## Architecture by Module

### SUMD
- **Functions**: 139
- **File**: `SUMD.md`

### project.map.toon
- **Functions**: 102
- **File**: `map.toon.yaml`

### SUMR
- **Functions**: 35
- **File**: `SUMR.md`

### testql-scenarios.generated-from-pytests.testql.toon
- **Functions**: 2
- **File**: `generated-from-pytests.testql.toon.yaml`

### docs.README
- **Functions**: 1
- **File**: `README.md`

## Key Entry Points

Main execution flows into the system:

### testql-scenarios.generated-from-pytests.testql.toon.all

### SUMR.detect_deploy_method

### SUMR._compose_file

### SUMR.start

### SUMR.stop

### SUMR._compose_up

### SUMR._compose_down

### SUMR._uvicorn_start

### SUMR._uvicorn_stop

### SUMR._wait_healthy

### SUMR.walk

### SUMR.restore

### SUMR.report

### SUMR.version

### SUMR.dashboard

### SUMR._attach_screenshots

### SUMR._print_day_summary

### SUMR._print_summary_table

### SUMR.scan_endpoints

### SUMR._scan_via_deta

### SUMR._ports_to_endpoints

### SUMR._scan_via_openapi

### SUMR._parse_openapi

### SUMR._scan_via_compose_labels

### SUMR._run_git

### SUMR.get_commit_for_day

### SUMR.iter_days

### SUMR.checkout

### SUMR.restore_head

### SUMR.days_with_commits

## Process Flows

Key execution flows identified:

### Flow 1: all
```
all [testql-scenarios.generated-from-pytests.testql.toon]
```

### Flow 2: detect_deploy_method
```
detect_deploy_method [SUMR]
```

### Flow 3: _compose_file
```
_compose_file [SUMR]
```

### Flow 4: start
```
start [SUMR]
```

### Flow 5: stop
```
stop [SUMR]
```

### Flow 6: _compose_up
```
_compose_up [SUMR]
```

### Flow 7: _compose_down
```
_compose_down [SUMR]
```

### Flow 8: _uvicorn_start
```
_uvicorn_start [SUMR]
```

### Flow 9: _uvicorn_stop
```
_uvicorn_stop [SUMR]
```

### Flow 10: _wait_healthy
```
_wait_healthy [SUMR]
```

## Data Transformation Functions

Key functions that process and transform data:

### SUMR._parse_openapi

### SUMD._parse_openapi

### SUMD._parse_testql_results

### SUMD.test_parse_openapi

### SUMD.test_get_commit_for_day_parses_output

### SUMD.test_parse_testql_results_ok

### SUMD.test_parse_testql_results_fail

### SUMD.test_parse_testql_results_missing_endpoint

### project.map.toon._parse_openapi

### project.map.toon._parse_testql_results

### project.map.toon.test_parse_openapi

### project.map.toon.test_get_commit_for_day_parses_output

### project.map.toon.test_parse_testql_results_ok

### project.map.toon.test_parse_testql_results_fail

### project.map.toon.test_parse_testql_results_missing_endpoint

## Public API Surface

Functions exposed as public API (no underscore prefix):

- `testql-scenarios.generated-from-pytests.testql.toon.all` - 0 calls
- `SUMR.detect_deploy_method` - 0 calls
- `SUMR.start` - 0 calls
- `SUMR.stop` - 0 calls
- `SUMR.walk` - 0 calls
- `SUMR.restore` - 0 calls
- `SUMR.report` - 0 calls
- `SUMR.version` - 0 calls
- `SUMR.dashboard` - 0 calls
- `SUMR.scan_endpoints` - 0 calls
- `SUMR.get_commit_for_day` - 0 calls
- `SUMR.iter_days` - 0 calls
- `SUMR.checkout` - 0 calls
- `SUMR.restore_head` - 0 calls
- `SUMR.days_with_commits` - 0 calls
- `SUMR.save_json` - 0 calls
- `SUMR.save_html` - 0 calls
- `SUMR.save_day` - 0 calls
- `SUMR.save_timeline_index` - 0 calls
- `docs.README.generate_readme` - 0 calls
- `SUMD.all` - 0 calls
- `SUMD.walk` - 0 calls
- `SUMD.restore` - 0 calls
- `SUMD.report` - 0 calls
- `SUMD.version` - 0 calls
- `SUMD.dashboard` - 0 calls
- `SUMD.get_cc_for_day` - 0 calls
- `SUMD.generate_dashboard` - 0 calls
- `SUMD.detect_deploy_method` - 0 calls
- `SUMD.start` - 0 calls
- `SUMD.stop` - 0 calls
- `SUMD.scan_endpoints` - 0 calls
- `SUMD.get_commit_for_day` - 0 calls
- `SUMD.iter_days` - 0 calls
- `SUMD.checkout` - 0 calls
- `SUMD.restore_head` - 0 calls
- `SUMD.days_with_commits` - 0 calls
- `SUMD.save_json` - 0 calls
- `SUMD.save_html` - 0 calls
- `SUMD.save_day` - 0 calls

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