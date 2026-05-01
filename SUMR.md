# rebuild

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Dependencies](#dependencies)
- [Source Map](#source-map)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `rebuild`
- **version**: `0.1.0`
- **python_requires**: `>=3.10`
- **license**: {'text': 'Apache-2.0'}
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, testql(2), app.doql.less, src(10 mod), project/(5 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: rebuild;
  version: 0.1.0;
}

dependencies {
  runtime: "typer>=0.12, rich>=13, gitpython>=3.1, httpx>=0.27, pyyaml>=6, pydantic>=2, deta>=0.1";
  dev: "pytest>=8, pytest-cov, pytest-asyncio, ruff, mypy";
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

### Source Modules

- `rebuild.cli`
- `rebuild.dashboard`
- `rebuild.deployer`
- `rebuild.endpoint_scanner`
- `rebuild.git_walker`
- `rebuild.models`
- `rebuild.reporter`
- `rebuild.restorer`
- `rebuild.screenshotter`
- `rebuild.tester`

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
```

### Development

```text markpact:deps python scope=dev
pytest>=8
pytest-cov
pytest-asyncio
ruff
mypy
```

## Source Map

*Top 5 modules by symbol density — signatures for LLM orientation.*

### `rebuild.deployer` (`rebuild/deployer.py`)

```python
def detect_deploy_method(repo)  # CC=5, fan=1
def _compose_file(repo, config)  # CC=4, fan=2
def start(repo, config)  # CC=5, fan=3
def stop(repo, config)  # CC=5, fan=2
def _compose_up(repo, config)  # CC=2, fan=5
def _compose_down(repo, config)  # CC=2, fan=4
def _uvicorn_start(repo, config)  # CC=3, fan=4
def _uvicorn_stop()  # CC=3, fan=3
def _wait_healthy(config)  # CC=4, fan=4
```

### `rebuild.cli` (`rebuild/cli.py`)

```python
def walk(repo, days, date_from, date_to, output, deploy, health_url, base_url, screenshots, dry_run)  # CC=15, fan=30 ⚠
def restore(endpoint, repo, output, results_dir)  # CC=2, fan=10
def report(results_dir)  # CC=13, fan=22 ⚠
def version()  # CC=1, fan=2
def dashboard(results_dir, repo)  # CC=6, fan=18
def _attach_screenshots(result, day_dir)  # CC=4, fan=2
def _print_day_summary(result)  # CC=3, fan=1
def _print_summary_table(results)  # CC=6, fan=7
```

### `rebuild.endpoint_scanner` (`rebuild/endpoint_scanner.py`)

```python
def scan_endpoints(repo, config)  # CC=8, fan=7
def _scan_via_deta(repo, config)  # CC=3, fan=4
def _ports_to_endpoints(data, base_url)  # CC=5, fan=3
def _scan_via_openapi(base_url)  # CC=4, fan=4
def _parse_openapi(spec, base_url)  # CC=4, fan=5
def _scan_via_compose_labels(repo, config)  # CC=9, fan=13
```

### `rebuild.git_walker` (`rebuild/git_walker.py`)

```python
def _run_git(args, cwd)  # CC=1, fan=2
def get_commit_for_day(repo, day, earliest)  # CC=7, fan=8
def iter_days(config)  # CC=4, fan=3
def checkout(repo, sha)  # CC=1, fan=1
def restore_head(repo)  # CC=4, fan=1
def days_with_commits(config)  # CC=3, fan=1
```

### `rebuild.reporter` (`rebuild/reporter.py`)

```python
def save_json(result)  # CC=6, fan=6
def _status_badge(status)  # CC=1, fan=1
def _screenshot_html(r, day_dir)  # CC=3, fan=2
def save_html(result)  # CC=9, fan=6
def save_day(result)  # CC=1, fan=2
def save_timeline_index(results, output_dir)  # CC=8, fan=7
```

## Call Graph

*51 nodes · 43 edges · 10 modules · CC̄=1.2*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `report` *(in rebuild.cli)* | 13 ⚠ | 0 | 31 | **31** |
| `dashboard` *(in rebuild.cli)* | 6 | 0 | 22 | **22** |
| `extract_endpoint` *(in rebuild.restorer)* | 9 | 0 | 19 | **19** |
| `_run_http_probe` *(in rebuild.tester)* | 6 | 4 | 12 | **16** |
| `restore` *(in rebuild.cli)* | 2 | 0 | 16 | **16** |
| `_batch_playwright` *(in rebuild.screenshotter)* | 5 | 1 | 15 | **16** |
| `_parse_testql_results` *(in rebuild.tester)* | 6 | 1 | 15 | **16** |
| `_scan_via_compose_labels` *(in rebuild.endpoint_scanner)* | 9 | 1 | 14 | **15** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/rebuild
# nodes: 51 | edges: 43 | modules: 10
# CC̄=1.2

HUBS[20]:
  rebuild.cli.report
    CC=13  in:0  out:31  total:31
  rebuild.cli.dashboard
    CC=6  in:0  out:22  total:22
  rebuild.restorer.extract_endpoint
    CC=9  in:0  out:19  total:19
  rebuild.tester._run_http_probe
    CC=6  in:4  out:12  total:16
  rebuild.cli.restore
    CC=2  in:0  out:16  total:16
  rebuild.screenshotter._batch_playwright
    CC=5  in:1  out:15  total:16
  rebuild.tester._parse_testql_results
    CC=6  in:1  out:15  total:16
  rebuild.endpoint_scanner._scan_via_compose_labels
    CC=9  in:1  out:14  total:15
  rebuild.reporter.save_timeline_index
    CC=8  in:2  out:8  total:10
  rebuild.screenshotter.take_screenshot
    CC=5  in:1  out:9  total:10
  rebuild.dashboard.generate_dashboard
    CC=5  in:1  out:9  total:10
  rebuild.reporter.save_json
    CC=6  in:1  out:9  total:10
  rebuild.endpoint_scanner.scan_endpoints
    CC=8  in:1  out:9  total:10
  rebuild.tester._run_via_testql
    CC=5  in:1  out:9  total:10
  rebuild.endpoint_scanner._parse_openapi
    CC=4  in:1  out:8  total:9
  rebuild.git_walker.get_commit_for_day
    CC=7  in:1  out:8  total:9
  rebuild.screenshotter._playwright_shot
    CC=1  in:1  out:7  total:8
  rebuild.reporter.save_html
    CC=9  in:1  out:7  total:8
  rebuild.restorer._find_backend_files
    CC=7  in:1  out:7  total:8
  rebuild.deployer._wait_healthy
    CC=4  in:2  out:6  total:8

MODULES:
  project.map.toon  [2 funcs]
    extract_endpoint  CC=0  out:0
    find_last_working_day  CC=0  out:0
  rebuild.cli  [4 funcs]
    _attach_screenshots  CC=4  out:2
    dashboard  CC=6  out:22
    report  CC=13  out:31
    restore  CC=2  out:16
  rebuild.dashboard  [4 funcs]
    _extract_avg_cc  CC=5  out:6
    _render_html  CC=5  out:4
    generate_dashboard  CC=5  out:9
    get_cc_for_day  CC=3  out:5
  rebuild.deployer  [8 funcs]
    _compose_down  CC=2  out:4
    _compose_file  CC=4  out:3
    _compose_up  CC=2  out:6
    _uvicorn_start  CC=3  out:5
    _uvicorn_stop  CC=3  out:3
    _wait_healthy  CC=4  out:6
    start  CC=5  out:3
    stop  CC=5  out:2
  rebuild.endpoint_scanner  [6 funcs]
    _parse_openapi  CC=4  out:8
    _ports_to_endpoints  CC=5  out:6
    _scan_via_compose_labels  CC=9  out:14
    _scan_via_deta  CC=3  out:4
    _scan_via_openapi  CC=4  out:4
    scan_endpoints  CC=8  out:9
  rebuild.git_walker  [6 funcs]
    _run_git  CC=1  out:2
    checkout  CC=1  out:1
    days_with_commits  CC=3  out:1
    get_commit_for_day  CC=7  out:8
    iter_days  CC=4  out:4
    restore_head  CC=4  out:2
  rebuild.reporter  [6 funcs]
    _screenshot_html  CC=3  out:2
    _status_badge  CC=1  out:1
    save_day  CC=1  out:2
    save_html  CC=9  out:7
    save_json  CC=6  out:9
    save_timeline_index  CC=8  out:8
  rebuild.restorer  [4 funcs]
    _find_backend_files  CC=7  out:7
    _is_page_endpoint  CC=2  out:0
    _write_readme  CC=4  out:4
    extract_endpoint  CC=9  out:19
  rebuild.screenshotter  [5 funcs]
    _batch_playwright  CC=5  out:15
    _playwright_shot  CC=1  out:7
    screenshot_endpoint  CC=2  out:2
    take_screenshot  CC=5  out:9
    take_screenshots_batch  CC=5  out:5
  rebuild.tester  [6 funcs]
    _fallback_all_timeout  CC=2  out:1
    _parse_testql_results  CC=6  out:15
    _run_http_probe  CC=6  out:12
    _run_via_testql  CC=5  out:9
    _testql_available  CC=2  out:1
    run_tests  CC=4  out:4

EDGES:
  rebuild.git_walker.get_commit_for_day → rebuild.git_walker._run_git
  rebuild.git_walker.iter_days → rebuild.git_walker.get_commit_for_day
  rebuild.git_walker.checkout → rebuild.git_walker._run_git
  rebuild.git_walker.restore_head → rebuild.git_walker._run_git
  rebuild.git_walker.days_with_commits → rebuild.git_walker.iter_days
  rebuild.reporter.save_html → rebuild.reporter._screenshot_html
  rebuild.reporter.save_html → rebuild.reporter._status_badge
  rebuild.reporter.save_day → rebuild.reporter.save_json
  rebuild.reporter.save_day → rebuild.reporter.save_html
  rebuild.deployer.start → rebuild.deployer._compose_up
  rebuild.deployer.start → rebuild.deployer._uvicorn_start
  rebuild.deployer.stop → rebuild.deployer._compose_down
  rebuild.deployer.stop → rebuild.deployer._uvicorn_stop
  rebuild.deployer._compose_up → rebuild.deployer._compose_file
  rebuild.deployer._compose_up → rebuild.deployer._wait_healthy
  rebuild.deployer._compose_down → rebuild.deployer._compose_file
  rebuild.deployer._uvicorn_start → rebuild.deployer._wait_healthy
  rebuild.endpoint_scanner.scan_endpoints → rebuild.endpoint_scanner._scan_via_deta
  rebuild.endpoint_scanner.scan_endpoints → rebuild.endpoint_scanner._scan_via_openapi
  rebuild.endpoint_scanner.scan_endpoints → rebuild.endpoint_scanner._scan_via_compose_labels
  rebuild.endpoint_scanner._scan_via_deta → rebuild.endpoint_scanner._ports_to_endpoints
  rebuild.endpoint_scanner._scan_via_openapi → rebuild.endpoint_scanner._parse_openapi
  rebuild.tester.run_tests → rebuild.tester._run_http_probe
  rebuild.tester.run_tests → rebuild.tester._testql_available
  rebuild.tester.run_tests → rebuild.tester._run_via_testql
  rebuild.tester._run_via_testql → rebuild.tester._parse_testql_results
  rebuild.tester._run_via_testql → rebuild.tester._run_http_probe
  rebuild.tester._run_via_testql → rebuild.tester._fallback_all_timeout
  rebuild.tester._parse_testql_results → rebuild.tester._run_http_probe
  rebuild.dashboard.get_cc_for_day → rebuild.dashboard._extract_avg_cc
  rebuild.dashboard.generate_dashboard → rebuild.dashboard._render_html
  rebuild.dashboard.generate_dashboard → rebuild.dashboard.get_cc_for_day
  rebuild.restorer.extract_endpoint → rebuild.restorer._find_backend_files
  rebuild.restorer.extract_endpoint → rebuild.restorer._write_readme
  rebuild.restorer.extract_endpoint → rebuild.restorer._is_page_endpoint
  rebuild.cli.restore → project.map.toon.find_last_working_day
  rebuild.cli.restore → project.map.toon.extract_endpoint
  rebuild.cli.report → rebuild.reporter.save_timeline_index
  rebuild.cli.dashboard → rebuild.dashboard.generate_dashboard
  rebuild.cli._attach_screenshots → rebuild.screenshotter.screenshot_endpoint
  rebuild.screenshotter.take_screenshot → rebuild.screenshotter._playwright_shot
  rebuild.screenshotter.take_screenshots_batch → rebuild.screenshotter._batch_playwright
  rebuild.screenshotter.screenshot_endpoint → rebuild.screenshotter.take_screenshot
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
# code2llm call graph | /home/tom/github/semcod/rebuild
# nodes: 51 | edges: 43 | modules: 10
# CC̄=1.2

HUBS[20]:
  rebuild.cli.report
    CC=13  in:0  out:31  total:31
  rebuild.cli.dashboard
    CC=6  in:0  out:22  total:22
  rebuild.restorer.extract_endpoint
    CC=9  in:0  out:19  total:19
  rebuild.tester._run_http_probe
    CC=6  in:4  out:12  total:16
  rebuild.cli.restore
    CC=2  in:0  out:16  total:16
  rebuild.screenshotter._batch_playwright
    CC=5  in:1  out:15  total:16
  rebuild.tester._parse_testql_results
    CC=6  in:1  out:15  total:16
  rebuild.endpoint_scanner._scan_via_compose_labels
    CC=9  in:1  out:14  total:15
  rebuild.reporter.save_timeline_index
    CC=8  in:2  out:8  total:10
  rebuild.screenshotter.take_screenshot
    CC=5  in:1  out:9  total:10
  rebuild.dashboard.generate_dashboard
    CC=5  in:1  out:9  total:10
  rebuild.reporter.save_json
    CC=6  in:1  out:9  total:10
  rebuild.endpoint_scanner.scan_endpoints
    CC=8  in:1  out:9  total:10
  rebuild.tester._run_via_testql
    CC=5  in:1  out:9  total:10
  rebuild.endpoint_scanner._parse_openapi
    CC=4  in:1  out:8  total:9
  rebuild.git_walker.get_commit_for_day
    CC=7  in:1  out:8  total:9
  rebuild.screenshotter._playwright_shot
    CC=1  in:1  out:7  total:8
  rebuild.reporter.save_html
    CC=9  in:1  out:7  total:8
  rebuild.restorer._find_backend_files
    CC=7  in:1  out:7  total:8
  rebuild.deployer._wait_healthy
    CC=4  in:2  out:6  total:8

MODULES:
  project.map.toon  [2 funcs]
    extract_endpoint  CC=0  out:0
    find_last_working_day  CC=0  out:0
  rebuild.cli  [4 funcs]
    _attach_screenshots  CC=4  out:2
    dashboard  CC=6  out:22
    report  CC=13  out:31
    restore  CC=2  out:16
  rebuild.dashboard  [4 funcs]
    _extract_avg_cc  CC=5  out:6
    _render_html  CC=5  out:4
    generate_dashboard  CC=5  out:9
    get_cc_for_day  CC=3  out:5
  rebuild.deployer  [8 funcs]
    _compose_down  CC=2  out:4
    _compose_file  CC=4  out:3
    _compose_up  CC=2  out:6
    _uvicorn_start  CC=3  out:5
    _uvicorn_stop  CC=3  out:3
    _wait_healthy  CC=4  out:6
    start  CC=5  out:3
    stop  CC=5  out:2
  rebuild.endpoint_scanner  [6 funcs]
    _parse_openapi  CC=4  out:8
    _ports_to_endpoints  CC=5  out:6
    _scan_via_compose_labels  CC=9  out:14
    _scan_via_deta  CC=3  out:4
    _scan_via_openapi  CC=4  out:4
    scan_endpoints  CC=8  out:9
  rebuild.git_walker  [6 funcs]
    _run_git  CC=1  out:2
    checkout  CC=1  out:1
    days_with_commits  CC=3  out:1
    get_commit_for_day  CC=7  out:8
    iter_days  CC=4  out:4
    restore_head  CC=4  out:2
  rebuild.reporter  [6 funcs]
    _screenshot_html  CC=3  out:2
    _status_badge  CC=1  out:1
    save_day  CC=1  out:2
    save_html  CC=9  out:7
    save_json  CC=6  out:9
    save_timeline_index  CC=8  out:8
  rebuild.restorer  [4 funcs]
    _find_backend_files  CC=7  out:7
    _is_page_endpoint  CC=2  out:0
    _write_readme  CC=4  out:4
    extract_endpoint  CC=9  out:19
  rebuild.screenshotter  [5 funcs]
    _batch_playwright  CC=5  out:15
    _playwright_shot  CC=1  out:7
    screenshot_endpoint  CC=2  out:2
    take_screenshot  CC=5  out:9
    take_screenshots_batch  CC=5  out:5
  rebuild.tester  [6 funcs]
    _fallback_all_timeout  CC=2  out:1
    _parse_testql_results  CC=6  out:15
    _run_http_probe  CC=6  out:12
    _run_via_testql  CC=5  out:9
    _testql_available  CC=2  out:1
    run_tests  CC=4  out:4

EDGES:
  rebuild.git_walker.get_commit_for_day → rebuild.git_walker._run_git
  rebuild.git_walker.iter_days → rebuild.git_walker.get_commit_for_day
  rebuild.git_walker.checkout → rebuild.git_walker._run_git
  rebuild.git_walker.restore_head → rebuild.git_walker._run_git
  rebuild.git_walker.days_with_commits → rebuild.git_walker.iter_days
  rebuild.reporter.save_html → rebuild.reporter._screenshot_html
  rebuild.reporter.save_html → rebuild.reporter._status_badge
  rebuild.reporter.save_day → rebuild.reporter.save_json
  rebuild.reporter.save_day → rebuild.reporter.save_html
  rebuild.deployer.start → rebuild.deployer._compose_up
  rebuild.deployer.start → rebuild.deployer._uvicorn_start
  rebuild.deployer.stop → rebuild.deployer._compose_down
  rebuild.deployer.stop → rebuild.deployer._uvicorn_stop
  rebuild.deployer._compose_up → rebuild.deployer._compose_file
  rebuild.deployer._compose_up → rebuild.deployer._wait_healthy
  rebuild.deployer._compose_down → rebuild.deployer._compose_file
  rebuild.deployer._uvicorn_start → rebuild.deployer._wait_healthy
  rebuild.endpoint_scanner.scan_endpoints → rebuild.endpoint_scanner._scan_via_deta
  rebuild.endpoint_scanner.scan_endpoints → rebuild.endpoint_scanner._scan_via_openapi
  rebuild.endpoint_scanner.scan_endpoints → rebuild.endpoint_scanner._scan_via_compose_labels
  rebuild.endpoint_scanner._scan_via_deta → rebuild.endpoint_scanner._ports_to_endpoints
  rebuild.endpoint_scanner._scan_via_openapi → rebuild.endpoint_scanner._parse_openapi
  rebuild.tester.run_tests → rebuild.tester._run_http_probe
  rebuild.tester.run_tests → rebuild.tester._testql_available
  rebuild.tester.run_tests → rebuild.tester._run_via_testql
  rebuild.tester._run_via_testql → rebuild.tester._parse_testql_results
  rebuild.tester._run_via_testql → rebuild.tester._run_http_probe
  rebuild.tester._run_via_testql → rebuild.tester._fallback_all_timeout
  rebuild.tester._parse_testql_results → rebuild.tester._run_http_probe
  rebuild.dashboard.get_cc_for_day → rebuild.dashboard._extract_avg_cc
  rebuild.dashboard.generate_dashboard → rebuild.dashboard._render_html
  rebuild.dashboard.generate_dashboard → rebuild.dashboard.get_cc_for_day
  rebuild.restorer.extract_endpoint → rebuild.restorer._find_backend_files
  rebuild.restorer.extract_endpoint → rebuild.restorer._write_readme
  rebuild.restorer.extract_endpoint → rebuild.restorer._is_page_endpoint
  rebuild.cli.restore → project.map.toon.find_last_working_day
  rebuild.cli.restore → project.map.toon.extract_endpoint
  rebuild.cli.report → rebuild.reporter.save_timeline_index
  rebuild.cli.dashboard → rebuild.dashboard.generate_dashboard
  rebuild.cli._attach_screenshots → rebuild.screenshotter.screenshot_endpoint
  rebuild.screenshotter.take_screenshot → rebuild.screenshotter._playwright_shot
  rebuild.screenshotter.take_screenshots_batch → rebuild.screenshotter._batch_playwright
  rebuild.screenshotter.screenshot_endpoint → rebuild.screenshotter.take_screenshot
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 34f 6604L | python:11,yaml:10,md:7,shell:4,txt:1,toml:1 | 2026-05-01
# CC̄=1.2 | critical:1/221 | dups:0 | cycles:0

HEALTH[1]:
  🟡 CC    walk CC=15 (limit:15)

REFACTOR[1]:
  1. split 1 high-CC methods  (CC>15)

PIPELINES[8]:
  [1] Src [find_last_working_day]: find_last_working_day
      PURITY: 100% pure
  [2] Src [extract_endpoint]: extract_endpoint → _find_backend_files
      PURITY: 100% pure
  [3] Src [walk]: walk → days_with_commits → iter_days → get_commit_for_day → ...(1 more)
      PURITY: 100% pure
  [4] Src [restore]: restore → find_last_working_day
      PURITY: 100% pure
  [5] Src [report]: report → save_timeline_index
      PURITY: 100% pure

LAYERS:
  rebuild/                        CC̄=4.6    ←in:0  →out:2
  │ !! cli                        365L  0C    8m  CC=15     ←0
  │ reporter                   235L  0C    6m  CC=9      ←1
  │ dashboard                  188L  0C    4m  CC=5      ←1
  │ tester                     187L  0C    6m  CC=6      ←1
  │ restorer                   187L  0C    5m  CC=9      ←0
  │ screenshotter              171L  2C    5m  CC=5      ←1
  │ endpoint_scanner           164L  0C    6m  CC=9      ←1
  │ deployer                   154L  0C    9m  CC=5      ←1
  │ git_walker                 131L  0C    6m  CC=7      ←1
  │ models                     109L  7C    0m  CC=0.0    ←0
  │ __init__                    10L  0C    0m  CC=0.0    ←0
  │
  docs/                           CC̄=0.0    ←in:0  →out:0
  │ README.md                  247L  0C    1m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-from-pytests.testql.toon.yaml    40L  0C    1m  CC=0.0    ←0
  │ generated-cli-tests.testql.toon.yaml    20L  0C    0m  CC=0.0    ←0
  │
  project/                        CC̄=0.0    ←in:0  →out:0
  │ !! calls.yaml                 759L  0C    0m  CC=0.0    ←0
  │ context.md                 381L  0C    0m  CC=0.0    ←0
  │ README.md                  339L  0C    0m  CC=0.0    ←0
  │ duplication.toon.yaml      313L  0C    0m  CC=0.0    ←0
  │ map.toon.yaml              190L  0C   64m  CC=0.0    ←1
  │ calls.toon.yaml            179L  0C    0m  CC=0.0    ←0
  │ analysis.toon.yaml          64L  0C    0m  CC=0.0    ←0
  │ project.toon.yaml           52L  0C    0m  CC=0.0    ←0
  │ prompt.txt                  49L  0C    0m  CC=0.0    ←0
  │ evolution.toon.yaml         39L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! SUMR.md                    999L  0C   35m  CC=0.0    ←0
  │ !! SUMD.md                    676L  0C   65m  CC=0.0    ←0
  │ PLAN.md                    198L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              65L  0C    0m  CC=0.0    ←0
  │ project.sh                  41L  0C    0m  CC=0.0    ←0
  │ tree.sh                      1L  0C    0m  CC=0.0    ←0
  │ README.md                    1L  0C    0m  CC=0.0    ←0
  │
  examples/                       CC̄=0.0    ←in:0  →out:0
  │ rebuild.yaml                24L  0C    0m  CC=0.0    ←0
  │ walk_dry_run.sh             13L  0C    0m  CC=0.0    ←0
  │ restore_endpoint.sh         13L  0C    0m  CC=0.0    ←0
  │

COUPLING:
               project.map      rebuild
  project.map           ──           ←2
      rebuild            2           ──
  CYCLES: none

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
  scan_ms:       3011
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 221 func | 14f | 2026-05-01

NEXT[1] (ranked by impact):
  [1] !  SPLIT-FUNC      walk  CC=15  fan=30
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 450


RISKS[0]: none

METRICS-TARGET:
  CC̄:          1.2 → ≤0.8
  max-CC:      15 → ≤7
  god-modules: 0 → 0
  high-CC(≥15): 1 → ≤0
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
  prev CC̄=4.8 → now CC̄=1.2
```

## Intent

Historical deployment analysis — walk git history, deploy per day, test all endpoints, capture screenshots, restore working fragments
