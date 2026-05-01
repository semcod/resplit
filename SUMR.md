# rebuild

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Workflows](#workflows)
- [Dependencies](#dependencies)
- [Test Contracts](#test-contracts)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `rebuild`
- **version**: `0.1.9`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, Makefile, testql(2), app.doql.less, goal.yaml, project/(5 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: rebuild;
  version: 0.1.9;
}

dependencies {
  runtime: "typer>=0.12, rich>=13, gitpython>=3.1, httpx>=0.27, pyyaml>=6, pydantic>=2, deta>=0.1, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60";
  dev: "pytest>=8, pytest-cov, pytest-asyncio, ruff, mypy, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60";
}

interface[type="cli"] {
  framework: argparse;
}
interface[type="cli"] page[name="rebuild"] {

}

workflow[name="install"] {
  trigger: manual;
  step-1: run cmd=pip install -e ".[dev]";
}

workflow[name="install-tui"] {
  trigger: manual;
  step-1: run cmd=pip install -e ".[dev,tui]";
}

workflow[name="install-full"] {
  trigger: manual;
  step-1: run cmd=pip install -e ".[dev,tui,screenshots]";
  step-2: run cmd=playwright install chromium;
}

workflow[name="test"] {
  trigger: manual;
  step-1: run cmd=python -m pytest tests/ -q;
}

workflow[name="test-v"] {
  trigger: manual;
  step-1: run cmd=python -m pytest tests/ -v;
}

workflow[name="lint"] {
  trigger: manual;
  step-1: run cmd=ruff check rebuild/ tests/;
}

workflow[name="fmt"] {
  trigger: manual;
  step-1: run cmd=ruff format rebuild/ tests/;
}

workflow[name="check"] {
  trigger: manual;
  step-1: depend target=lint;
  step-2: depend target=test;
}

workflow[name="tui"] {
  trigger: manual;
  step-1: run cmd=rebuild tui;
}

workflow[name="walk-dry"] {
  trigger: manual;
  step-1: run cmd=rebuild walk . --days 30 --dry-run --no-screenshots;
}

workflow[name="dashboard"] {
  trigger: manual;
  step-1: run cmd=rebuild dashboard --repo .;
}

workflow[name="build"] {
  trigger: manual;
  step-1: run cmd=python -m build;
}

workflow[name="clean"] {
  trigger: manual;
  step-1: run cmd=find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true;
  step-2: run cmd=find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true;
  step-3: run cmd=rm -rf dist/ build/;
}

deploy {
  target: makefile;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: .env;
  python_version: >=3.10;
}
```

## Workflows

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
# code2llm | 36f 3931L | md:13,yaml:10,shell:8,toml:1,yml:1,txt:1 | 2026-05-01
# CC̄=0.0 | critical:0/183 | dups:0 | cycles:0

HEALTH[0]: ok

REFACTOR[0]: none needed

PIPELINES[0]: none detected

LAYERS:
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-from-pytests.testql.toon.yaml    40L  0C    1m  CC=0.0    ←0
  │ generated-cli-tests.testql.toon.yaml    20L  0C    0m  CC=0.0    ←0
  │
  docs/                           CC̄=0.0    ←in:0  →out:0
  │ README.md                  365L  0C    1m  CC=0.0    ←0
  │ architecture.md             45L  0C    0m  CC=0.0    ←0
  │
  project/                        CC̄=0.0    ←in:0  →out:0
  │ README.md                  339L  0C    0m  CC=0.0    ←0
  │ map.toon.yaml              258L  0C   90m  CC=0.0    ←0
  │ context.md                 237L  0C    0m  CC=0.0    ←0
  │ calls.yaml                 197L  0C    0m  CC=0.0    ←0
  │ analysis.toon.yaml          65L  0C    0m  CC=0.0    ←0
  │ prompt.txt                  47L  0C    0m  CC=0.0    ←0
  │ evolution.toon.yaml         44L  0C    0m  CC=0.0    ←0
  │ project.toon.yaml           29L  0C    0m  CC=0.0    ←0
  │ calls.toon.yaml              9L  0C    0m  CC=0.0    ←0
  │ duplication.toon.yaml        9L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! SUMD.md                    566L  0C   91m  CC=0.0    ←0
  │ !! goal.yaml                  513L  0C    0m  CC=0.0    ←0
  │ SUMR.md                    330L  0C    0m  CC=0.0    ←0
  │ PLAN.md                    198L  0C    0m  CC=0.0    ←0
  │ README.md                  118L  0C    0m  CC=0.0    ←0
  │ pyproject.toml             103L  0C    0m  CC=0.0    ←0
  │ project.sh                  41L  0C    0m  CC=0.0    ←0
  │ CHANGELOG.md                33L  0C    0m  CC=0.0    ←0
  │ TODO.md                     22L  0C    0m  CC=0.0    ←0
  │ tree.sh                      1L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │
  examples/                       CC̄=0.0    ←in:0  →out:0
  │ README.md                   61L  0C    0m  CC=0.0    ←0
  │ README.md                   54L  0C    0m  CC=0.0    ←0
  │ mock_results.sh             37L  0C    0m  CC=0.0    ←0
  │ README.md                   36L  0C    0m  CC=0.0    ←0
  │ run.sh                      32L  0C    0m  CC=0.0    ←0
  │ run.sh                      21L  0C    0m  CC=0.0    ←0
  │ run.sh                      20L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          15L  0C    0m  CC=0.0    ←0
  │ walk_dry_run.sh             13L  0C    0m  CC=0.0    ←0
  │ restore_endpoint.sh         13L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │
  ── zero ──
     Makefile                                  0L
     examples/Makefile                         0L

COUPLING: no cross-package imports detected

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 0 groups | 31f 3211L | 2026-05-01

SUMMARY:
  files_scanned: 31
  total_lines:   3211
  dup_groups:    0
  dup_fragments: 0
  saved_lines:   0
  scan_ms:       4374
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 183 func | 4f | 2026-05-01

NEXT[1] (ranked by impact):
  [1] !! SPLIT           rebuild/interfaces/tui.py
      WHY: 926L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0


RISKS[1]:
  ⚠ Splitting rebuild/interfaces/tui.py may break 0 import paths

METRICS-TARGET:
  CC̄:          0.0 → ≤0.0
  max-CC:      0 → ≤0
  god-modules: 1 → 0
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
  prev CC̄=0.0 → now CC̄=0.0
```

## Intent

Historical deployment analysis — walk git history, deploy per day, test all endpoints, capture screenshots, restore working fragments
