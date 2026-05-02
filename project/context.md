# System Architecture Analysis

## Overview

- **Project**: /home/tom/github/semcod/resplit
- **Primary Language**: md
- **Languages**: md: 33, yaml: 17, txt: 10, json: 9, shell: 8
- **Analysis Mode**: static
- **Total Functions**: 3250
- **Total Classes**: 2
- **Modules**: 91
- **Entry Points**: 3236

## Architecture by Module

### SUMD
- **Functions**: 61714
- **File**: `SUMD.md`

### scripts.bump_version
- **Functions**: 10
- **File**: `bump_version.py`

### restored_c2004_health.api-health.backend.modules.connect-config-network.api.main
- **Functions**: 9
- **File**: `main.py`

### restored_c2004_health.api-health.backend.modules.connect-id-user-list.api.main
- **Functions**: 9
- **File**: `main.py`

### restored_c2004_health.api-health.backend.modules.connect-manager-library.api.main
- **Functions**: 9
- **File**: `main.py`

### restored_c2004_health.api-health.backend.modules.connect-reports-month.api.main
- **Functions**: 9
- **File**: `main.py`

### examples.09-mvp-protocol.README
- **Functions**: 5
- **File**: `README.md`

### examples.08-nlp-commands.README
- **Functions**: 4
- **File**: `README.md`

### docs.guide.plugins
- **Functions**: 3
- **Classes**: 2
- **File**: `plugins.md`

### Makefile
- **Functions**: 2
- **File**: `Makefile`

### testql-scenarios.generated-from-pytests.testql.toon
- **Functions**: 2
- **File**: `generated-from-pytests.testql.toon.yaml`

### docs.getting-started.configuration
- **Functions**: 1
- **File**: `configuration.md`

### docs.README
- **Functions**: 1
- **File**: `README.md`

## Key Entry Points

Main execution flows into the system:

### scripts.bump_version.main
- **Calls**: argparse.ArgumentParser, parser.add_argument, parser.add_argument, parser.add_argument, parser.parse_args, scripts.bump_version.read_version, scripts.bump_version.bump, Makefile.print

### restored_c2004_health.api-health.backend.modules.connect-config-network.api.main.serve_ui
- **Calls**: app.get, FileResponse, HTTPException, filename.endswith, file_path.exists, Path, Path

### restored_c2004_health.api-health.backend.modules.connect-config-network.api.main.serve_model
- **Calls**: app.get, FileResponse, HTTPException, filename.endswith, file_path.exists, Path, Path

### restored_c2004_health.api-health.backend.modules.connect-id-user-list.api.main.serve_ui
- **Calls**: app.get, FileResponse, HTTPException, filename.endswith, file_path.exists, Path, Path

### restored_c2004_health.api-health.backend.modules.connect-id-user-list.api.main.serve_model
- **Calls**: app.get, FileResponse, HTTPException, filename.endswith, file_path.exists, Path, Path

### restored_c2004_health.api-health.backend.modules.connect-manager-library.api.main.serve_ui
- **Calls**: app.get, FileResponse, HTTPException, filename.endswith, file_path.exists, Path, Path

### restored_c2004_health.api-health.backend.modules.connect-manager-library.api.main.serve_model
- **Calls**: app.get, FileResponse, HTTPException, filename.endswith, file_path.exists, Path, Path

### restored_c2004_health.api-health.backend.modules.connect-reports-month.api.main.serve_ui
- **Calls**: app.get, FileResponse, HTTPException, filename.endswith, file_path.exists, Path, Path

### restored_c2004_health.api-health.backend.modules.connect-reports-month.api.main.serve_model
- **Calls**: app.get, FileResponse, HTTPException, filename.endswith, file_path.exists, Path, Path

### restored_c2004_health.api-health.backend.modules.connect-config-network.api.main.get_manifest
- **Calls**: app.get, PlainTextResponse, MANIFEST_PATH.exists, HTTPException, MANIFEST_PATH.read_text

### restored_c2004_health.api-health.backend.modules.connect-config-network.api.main.list_models
- **Calls**: app.get, model_dir.exists, Path, model_dir.iterdir, f.is_file

### restored_c2004_health.api-health.backend.modules.connect-id-user-list.api.main.get_manifest
- **Calls**: app.get, PlainTextResponse, MANIFEST_PATH.exists, HTTPException, MANIFEST_PATH.read_text

### restored_c2004_health.api-health.backend.modules.connect-id-user-list.api.main.list_models
- **Calls**: app.get, model_dir.exists, Path, model_dir.iterdir, f.is_file

### restored_c2004_health.api-health.backend.modules.connect-manager-library.api.main.get_manifest
- **Calls**: app.get, PlainTextResponse, MANIFEST_PATH.exists, HTTPException, MANIFEST_PATH.read_text

### restored_c2004_health.api-health.backend.modules.connect-manager-library.api.main.list_models
- **Calls**: app.get, model_dir.exists, Path, model_dir.iterdir, f.is_file

### restored_c2004_health.api-health.backend.modules.connect-reports-month.api.main.get_manifest
- **Calls**: app.get, PlainTextResponse, MANIFEST_PATH.exists, HTTPException, MANIFEST_PATH.read_text

### restored_c2004_health.api-health.backend.modules.connect-reports-month.api.main.list_models
- **Calls**: app.get, model_dir.exists, Path, model_dir.iterdir, f.is_file

### restored_c2004_health.api-health.backend.modules.connect-config-network.api.main.index
- **Calls**: app.get, HTMLResponse, restored_c2004_health.api-health.backend.modules.connect-config-network.api.main._index_html

### restored_c2004_health.api-health.backend.modules.connect-config-network.api.main.module_index
- **Calls**: app.get, HTMLResponse, restored_c2004_health.api-health.backend.modules.connect-config-network.api.main._index_html

### restored_c2004_health.api-health.backend.modules.connect-id-user-list.api.main.index
- **Calls**: app.get, HTMLResponse, restored_c2004_health.api-health.backend.modules.connect-id-user-list.api.main._index_html

### restored_c2004_health.api-health.backend.modules.connect-id-user-list.api.main.module_index
- **Calls**: app.get, HTMLResponse, restored_c2004_health.api-health.backend.modules.connect-id-user-list.api.main._index_html

### restored_c2004_health.api-health.backend.modules.connect-manager-library.api.main.index
- **Calls**: app.get, HTMLResponse, restored_c2004_health.api-health.backend.modules.connect-manager-library.api.main._index_html

### restored_c2004_health.api-health.backend.modules.connect-manager-library.api.main.module_index
- **Calls**: app.get, HTMLResponse, restored_c2004_health.api-health.backend.modules.connect-manager-library.api.main._index_html

### restored_c2004_health.api-health.backend.modules.connect-reports-month.api.main.index
- **Calls**: app.get, HTMLResponse, restored_c2004_health.api-health.backend.modules.connect-reports-month.api.main._index_html

### restored_c2004_health.api-health.backend.modules.connect-reports-month.api.main.module_index
- **Calls**: app.get, HTMLResponse, restored_c2004_health.api-health.backend.modules.connect-reports-month.api.main._index_html

### restored_c2004_health.api-health.backend.modules.connect-config-network.api.main.health
- **Calls**: app.get

### restored_c2004_health.api-health.backend.modules.connect-config-network.api.main.list_pages
- **Calls**: app.get

### restored_c2004_health.api-health.backend.modules.connect-id-user-list.api.main.health
- **Calls**: app.get

### restored_c2004_health.api-health.backend.modules.connect-id-user-list.api.main.list_pages
- **Calls**: app.get

### restored_c2004_health.api-health.backend.modules.connect-manager-library.api.main.health
- **Calls**: app.get

## Process Flows

Key execution flows identified:

### Flow 1: main
```
main [scripts.bump_version]
```

### Flow 2: serve_ui
```
serve_ui [restored_c2004_health.api-health.backend.modules.connect-config-network.api.main]
```

### Flow 3: serve_model
```
serve_model [restored_c2004_health.api-health.backend.modules.connect-config-network.api.main]
```

### Flow 4: get_manifest
```
get_manifest [restored_c2004_health.api-health.backend.modules.connect-config-network.api.main]
```

### Flow 5: list_models
```
list_models [restored_c2004_health.api-health.backend.modules.connect-config-network.api.main]
```

### Flow 6: index
```
index [restored_c2004_health.api-health.backend.modules.connect-config-network.api.main]
  └─> _index_html
```

### Flow 7: module_index
```
module_index [restored_c2004_health.api-health.backend.modules.connect-config-network.api.main]
  └─> _index_html
```

## Key Classes

### docs.guide.plugins.SecurityScanner
- **Methods**: 0

### docs.guide.plugins.SlackReporter
- **Methods**: 0

## Data Transformation Functions

Key functions that process and transform data:

### SUMD._parse_numeric

### SUMD.parse_date

### SUMD.parse_xml_protocol

### SUMD._process_output_var

### SUMD._process_param_var

### SUMD._process_op_var

### SUMD._process_output_keys

### SUMD._process_param_conditions

### SUMD._process_alarms

### SUMD._process_steps

### SUMD._process_tasks

### SUMD._process_goal

### SUMD._process_scenario_data

### SUMD._parse_content

### SUMD._parse_units_list

### SUMD._process_scenarios

### SUMD._process_out_entity

### SUMD._process_op_entity

### SUMD._process_prm_entity

### SUMD._process_output_tasks

### SUMD._process_parameter_conditions

### SUMD._convert_else_step

### SUMD._process_goal_steps

### SUMD._process_scenario

### SUMD._process_message_step

## Public API Surface

Functions exposed as public API (no underscore prefix):

- `scripts.bump_version.main` - 20 calls
- `scripts.bump_version.categorize_commits` - 15 calls
- `scripts.bump_version.build_new_section` - 14 calls
- `scripts.bump_version.update_changelog` - 14 calls
- `restored_c2004_health.api-health.backend.modules.connect-config-network.api.main.serve_ui` - 7 calls
- `restored_c2004_health.api-health.backend.modules.connect-config-network.api.main.serve_model` - 7 calls
- `restored_c2004_health.api-health.backend.modules.connect-id-user-list.api.main.serve_ui` - 7 calls
- `restored_c2004_health.api-health.backend.modules.connect-id-user-list.api.main.serve_model` - 7 calls
- `restored_c2004_health.api-health.backend.modules.connect-manager-library.api.main.serve_ui` - 7 calls
- `restored_c2004_health.api-health.backend.modules.connect-manager-library.api.main.serve_model` - 7 calls
- `restored_c2004_health.api-health.backend.modules.connect-reports-month.api.main.serve_ui` - 7 calls
- `restored_c2004_health.api-health.backend.modules.connect-reports-month.api.main.serve_model` - 7 calls
- `scripts.bump_version.bump` - 7 calls
- `scripts.bump_version.get_git_log_since_last_tag` - 7 calls
- `scripts.bump_version.update_init` - 6 calls
- `scripts.bump_version.update_pyproject` - 6 calls
- `scripts.bump_version.collect_unreleased_entries` - 6 calls
- `restored_c2004_health.api-health.backend.modules.connect-config-network.api.main.get_manifest` - 5 calls
- `restored_c2004_health.api-health.backend.modules.connect-config-network.api.main.list_models` - 5 calls
- `restored_c2004_health.api-health.backend.modules.connect-id-user-list.api.main.get_manifest` - 5 calls
- `restored_c2004_health.api-health.backend.modules.connect-id-user-list.api.main.list_models` - 5 calls
- `restored_c2004_health.api-health.backend.modules.connect-manager-library.api.main.get_manifest` - 5 calls
- `restored_c2004_health.api-health.backend.modules.connect-manager-library.api.main.list_models` - 5 calls
- `restored_c2004_health.api-health.backend.modules.connect-reports-month.api.main.get_manifest` - 5 calls
- `restored_c2004_health.api-health.backend.modules.connect-reports-month.api.main.list_models` - 5 calls
- `scripts.bump_version.read_version` - 4 calls
- `restored_c2004_health.api-health.backend.modules.connect-config-network.api.main.index` - 3 calls
- `restored_c2004_health.api-health.backend.modules.connect-config-network.api.main.module_index` - 3 calls
- `restored_c2004_health.api-health.backend.modules.connect-id-user-list.api.main.index` - 3 calls
- `restored_c2004_health.api-health.backend.modules.connect-id-user-list.api.main.module_index` - 3 calls
- `restored_c2004_health.api-health.backend.modules.connect-manager-library.api.main.index` - 3 calls
- `restored_c2004_health.api-health.backend.modules.connect-manager-library.api.main.module_index` - 3 calls
- `restored_c2004_health.api-health.backend.modules.connect-reports-month.api.main.index` - 3 calls
- `restored_c2004_health.api-health.backend.modules.connect-reports-month.api.main.module_index` - 3 calls
- `restored_c2004_health.api-health.backend.modules.connect-config-network.api.main.health` - 1 calls
- `restored_c2004_health.api-health.backend.modules.connect-config-network.api.main.list_pages` - 1 calls
- `restored_c2004_health.api-health.backend.modules.connect-id-user-list.api.main.health` - 1 calls
- `restored_c2004_health.api-health.backend.modules.connect-id-user-list.api.main.list_pages` - 1 calls
- `restored_c2004_health.api-health.backend.modules.connect-manager-library.api.main.health` - 1 calls
- `restored_c2004_health.api-health.backend.modules.connect-manager-library.api.main.list_pages` - 1 calls

## System Interactions

How components interact:

```mermaid
graph TD
    main --> ArgumentParser
    main --> add_argument
    main --> parse_args
    serve_ui --> get
    serve_ui --> FileResponse
    serve_ui --> HTTPException
    serve_ui --> endswith
    serve_ui --> exists
    serve_model --> get
    serve_model --> FileResponse
    serve_model --> HTTPException
    serve_model --> endswith
    serve_model --> exists
    get_manifest --> get
    get_manifest --> PlainTextResponse
    get_manifest --> exists
    get_manifest --> HTTPException
    get_manifest --> read_text
    list_models --> get
    list_models --> exists
    list_models --> Path
    list_models --> iterdir
    list_models --> is_file
```

## Reverse Engineering Guidelines

1. **Entry Points**: Start analysis from the entry points listed above
2. **Core Logic**: Focus on classes with many methods
3. **Data Flow**: Follow data transformation functions
4. **Process Flows**: Use the flow diagrams for execution paths
5. **API Surface**: Public API functions reveal the interface

## Context for LLM

Maintain the identified architectural patterns and public API surface when suggesting changes.