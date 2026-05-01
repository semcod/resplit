# rebuild

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Dependencies](#dependencies)
- [Test Contracts](#test-contracts)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `rebuild`
- **version**: `0.1.7`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, testql(2), app.doql.less, goal.yaml, project/(5 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: rebuild;
  version: 0.1.7;
}

dependencies {
  runtime: "typer>=0.12, rich>=13, gitpython>=3.1, httpx>=0.27, pyyaml>=6, pydantic>=2, deta>=0.1, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60";
  dev: "pytest>=8, pytest-cov, pytest-asyncio, ruff, mypy, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60";
}

interface[type="api"] {
  type: rest;
  framework: fastapi;
}

interface[type="cli"] {
  framework: argparse;
}
interface[type="cli"] page[name="rebuild"] {

}

deploy {
  target: pip;
}

environment[name="local"] {
  runtime: python;
  env_file: .env;
  python_version: >=3.10;
}
```

## Dependencies

### Runtime

```text markpact:deps python
typer>=0.12
rich>=13
gitpython>=3.1
httpx>=0.27
pyyaml>=6
pydantic>=2
deta>=0.1
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
```

### Development

```text markpact:deps python scope=dev
pytest>=8
pytest-cov
pytest-asyncio
ruff
mypy
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Cli (1)

**`CLI Command Tests`**

### Integration (1)

**`Auto-generated from Python Tests`**

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/resplit
# nodes: 0 | edges: 0 | modules: 0
# CC̄=0.0

HUBS[20]:

MODULES:

EDGES:
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 32f 5265L | md:11,yaml:10,shell:8,txt:1,toml:1,yml:1 | 2026-05-01
# CC̄=0.0 | critical:0/242 | dups:0 | cycles:0

HEALTH[0]: ok

REFACTOR[0]: none needed

PIPELINES[0]: none detected

LAYERS:
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-from-pytests.testql.toon.yaml    40L  0C    1m  CC=0.0    ←0
  │ generated-cli-tests.testql.toon.yaml    20L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! SUMR.md                    664L  0C   35m  CC=0.0    ←0
  │ !! SUMD.md                    645L  0C  103m  CC=0.0    ←0
  │ !! goal.yaml                  513L  0C    0m  CC=0.0    ←0
  │ README.md                  270L  0C    0m  CC=0.0    ←0
  │ PLAN.md                    198L  0C    0m  CC=0.0    ←0
  │ CHANGELOG.md               115L  0C    0m  CC=0.0    ←0
  │ pyproject.toml             100L  0C    0m  CC=0.0    ←0
  │ project.sh                  41L  0C    0m  CC=0.0    ←0
  │ tree.sh                      1L  0C    0m  CC=0.0    ←0
  │
  docs/                           CC̄=0.0    ←in:0  →out:0
  │ README.md                  344L  0C    1m  CC=0.0    ←0
  │
  project/                        CC̄=0.0    ←in:0  →out:0
  │ !! calls.yaml                 729L  0C    0m  CC=0.0    ←0
  │ context.md                 380L  0C    0m  CC=0.0    ←0
  │ README.md                  339L  0C    0m  CC=0.0    ←0
  │ map.toon.yaml              182L  0C  102m  CC=0.0    ←0
  │ calls.toon.yaml            153L  0C    0m  CC=0.0    ←0
  │ analysis.toon.yaml          78L  0C    0m  CC=0.0    ←0
  │ project.toon.yaml           52L  0C    0m  CC=0.0    ←0
  │ prompt.txt                  47L  0C    0m  CC=0.0    ←0
  │ evolution.toon.yaml         43L  0C    0m  CC=0.0    ←0
  │ duplication.toon.yaml        9L  0C    0m  CC=0.0    ←0
  │
  examples/                       CC̄=0.0    ←in:0  →out:0
  │ README.md                   61L  0C    0m  CC=0.0    ←0
  │ README.md                   54L  0C    0m  CC=0.0    ←0
  │ mock_results.sh             37L  0C    0m  CC=0.0    ←0
  │ README.md                   36L  0C    0m  CC=0.0    ←0
  │ run.sh                      30L  0C    0m  CC=0.0    ←0
  │ run.sh                      25L  0C    0m  CC=0.0    ←0
  │ run.sh                      18L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          15L  0C    0m  CC=0.0    ←0
  │ walk_dry_run.sh             13L  0C    0m  CC=0.0    ←0
  │ restore_endpoint.sh         13L  0C    0m  CC=0.0    ←0
  │

COUPLING: no cross-package imports detected

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 0 groups | 10f 1714L | 2026-05-01

SUMMARY:
  files_scanned: 10
  total_lines:   1714
  dup_groups:    0
  dup_fragments: 0
  saved_lines:   0
  scan_ms:       4488
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 242 func | 5f | 2026-05-01

NEXT[0]: no refactoring needed

RISKS[0]: none

METRICS-TARGET:
  CC̄:          0.0 → ≤0.0
  max-CC:      0 → ≤0
  god-modules: 0 → 0
  high-CC(≥15): 0 → ≤0
  hub-types:   0 → ≤0

PATTERNS (language parser shared logic):
  _extract_declarations() in base.py — unified extraction for:
    - TypeScript: interfaces, types, classes, functions, arrow funcs
    - PHP: namespaces, traits, classes, functions, includes
    - Ruby: modules, classes, methods, requires
    - C++: classes, structs, functions, #includes
    - C#: classes, interfaces, methods, usings
    - Java: classes, interfaces, methods, imports
    - Go: packages, functions, structs
    - Rust: modules, functions, traits, use statements

  Shared regex patterns per language:
    - import: language-specific import/require/using patterns
    - class: class/struct/trait declarations with inheritance
    - function: function/method signatures with visibility
    - brace_tracking: for C-family languages ({ })
    - end_keyword_tracking: for Ruby (module/class/def...end)

  Benefits:
    - Consistent extraction logic across all languages
    - Reduced code duplication (~70% reduction in parser LOC)
    - Easier maintenance: fix once, apply everywhere
    - Standardized FunctionInfo/ClassInfo models

HISTORY:
  prev CC̄=1.2 → now CC̄=0.0
```

## Intent

Historical deployment analysis — walk git history, deploy per day, test all endpoints, capture screenshots, restore working fragments
