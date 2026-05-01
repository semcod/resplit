# resplit

Historical deployment analysis — walk git history, deploy per day, test all endpoints, capture screenshots, restore working fragments

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Interfaces](#interfaces)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [Deployment](#deployment)
- [Code Analysis](#code-analysis)
- [Source Map](#source-map)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Intent](#intent)

## Metadata

- **name**: `resplit`
- **version**: `0.1.0`
- **python_requires**: `>=3.10`
- **license**: {'text': 'Apache-2.0'}
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, testql(2), app.doql.less, src(10 mod), project/(2 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: resplit;
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
interface[type="cli"] page[name="resplit"] {

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

- `resplit.cli`
- `resplit.dashboard`
- `resplit.deployer`
- `resplit.endpoint_scanner`
- `resplit.git_walker`
- `resplit.models`
- `resplit.reporter`
- `resplit.restorer`
- `resplit.screenshotter`
- `resplit.tester`

## Interfaces

### CLI Entry Points

- `resplit`

### testql Scenarios

#### `testql-scenarios/generated-cli-tests.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-cli-tests.testql.toon.yaml
# SCENARIO: CLI Command Tests
# TYPE: cli
# GENERATED: true

CONFIG[2]{key, value}:
  cli_command, python -m resplit
  timeout_ms, 10000

# Test 1: CLI help command
SHELL "python -m resplit --help" 5000
ASSERT_EXIT_CODE 0
ASSERT_STDOUT_CONTAINS "usage"

# Test 2: CLI version command
SHELL "python -m resplit --version" 5000
ASSERT_EXIT_CODE 0

# Test 3: CLI main workflow (dry-run)
SHELL "python -m resplit --help" 10000
ASSERT_EXIT_CODE 0
```

#### `testql-scenarios/generated-from-pytests.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-from-pytests.testql.toon.yaml
# SCENARIO: Auto-generated from Python Tests
# TYPE: integration
# GENERATED: true

CONFIG[2]{key, value}:
  base_url, ${api_url:-http://localhost:8101}
  timeout_ms, 10000

# Converted 30 assertions from pytest
ASSERT[30]{field, operator, expected}:
  len(endpoints), ==, 3
  len(endpoints), ==, 3
  all(e.service, ==, "backend" for e in endpoints)
  len(endpoints), ==, 1
  endpoints[0].path, ==, "/api"
  endpoints[0].service, ==, "backend"
  len(data), ==, 1
  data[0].status, ==, "ok"
  data[0].http_status, ==, 200
  ep.url, ==, "http://localhost:8003/api/health"
  ep.url, ==, "http://localhost:8003/api/health"
  ep.slug, ==, "GET_api_health"
  result.ok_count, ==, 2
  result.fail_count, ==, 2
  result.health_pct, ==, 50.0
  len(endpoints), ==, 3
  len(endpoints), ==, 3
  all(e.service, ==, "backend" for e in endpoints)
  len(endpoints), ==, 1
  endpoints[0].path, ==, "/api"
  endpoints[0].service, ==, "backend"
  len(data), ==, 1
  data[0].status, ==, "ok"
  data[0].http_status, ==, 200
  ep.url, ==, "http://localhost:8003/api/health"
  ep.url, ==, "http://localhost:8003/api/health"
  ep.slug, ==, "GET_api_health"
  result.ok_count, ==, 2
  result.fail_count, ==, 2
  result.health_pct, ==, 50.0
```

## Configuration

```yaml
project:
  name: resplit
  version: 0.1.0
  env: local
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
```

### Development

```text markpact:deps python scope=dev
pytest>=8
pytest-cov
pytest-asyncio
ruff
mypy
```

## Deployment

```bash markpact:run
pip install resplit

# development install
pip install -e .[dev]
```

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# resplit | 25f 2602L | python:20,shell:4,less:1 | 2026-05-01
# stats: 102 func | 9 cls | 25 mod | CC̄=3.8 | critical:2 | cycles:0
# alerts[5]: CC walk=15; CC report=13; CC _scan_via_compose_labels=9; CC save_html=9; CC extract_endpoint=9
# hotspots[5]: walk fan=30; report fan=22; dashboard fan=18; _scan_via_compose_labels fan=13; _batch_playwright fan=12
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[25]:
  app.doql.less,34
  examples/restore_endpoint.sh,14
  examples/walk_dry_run.sh,14
  project.sh,41
  resplit/__init__.py,11
  resplit/cli.py,366
  resplit/dashboard.py,189
  resplit/deployer.py,155
  resplit/endpoint_scanner.py,165
  resplit/git_walker.py,132
  resplit/models.py,110
  resplit/reporter.py,236
  resplit/restorer.py,188
  resplit/screenshotter.py,172
  resplit/tester.py,188
  tests/__init__.py,1
  tests/test_deployer.py,37
  tests/test_endpoint_scanner.py,72
  tests/test_git_walker.py,51
  tests/test_models.py,71
  tests/test_reporter.py,78
  tests/test_restorer.py,47
  tests/test_screenshotter.py,99
  tests/test_tester.py,129
  tree.sh,2
D:
  resplit/__init__.py:
  resplit/cli.py:
    e: walk,restore,report,version,dashboard,_attach_screenshots,_print_day_summary,_print_summary_table
    walk(repo;days;date_from;date_to;output;deploy;health_url;base_url;screenshots;dry_run)
    restore(endpoint;repo;output;results_dir)
    report(results_dir)
    version()
    dashboard(results_dir;repo)
    _attach_screenshots(result;day_dir)
    _print_day_summary(result)
    _print_summary_table(results)
  resplit/dashboard.py:
    e: get_cc_for_day,_extract_avg_cc,generate_dashboard,_render_html
    get_cc_for_day(repo;day)
    _extract_avg_cc(data)
    generate_dashboard(results;output_dir;repo)
    _render_html(days;health;cc;total_days)
  resplit/deployer.py:
    e: detect_deploy_method,_compose_file,start,stop,_compose_up,_compose_down,_uvicorn_start,_uvicorn_stop,_wait_healthy
    detect_deploy_method(repo)
    _compose_file(repo;config)
    start(repo;config)
    stop(repo;config)
    _compose_up(repo;config)
    _compose_down(repo;config)
    _uvicorn_start(repo;config)
    _uvicorn_stop()
    _wait_healthy(config)
  resplit/endpoint_scanner.py:
    e: scan_endpoints,_scan_via_deta,_ports_to_endpoints,_scan_via_openapi,_parse_openapi,_scan_via_compose_labels
    scan_endpoints(repo;config)
    _scan_via_deta(repo;config)
    _ports_to_endpoints(data;base_url)
    _scan_via_openapi(base_url)
    _parse_openapi(spec;base_url)
    _scan_via_compose_labels(repo;config)
  resplit/git_walker.py:
    e: _run_git,get_commit_for_day,iter_days,checkout,restore_head,days_with_commits
    _run_git(args;cwd)
    get_commit_for_day(repo;day;earliest)
    iter_days(config)
    checkout(repo;sha)
    restore_head(repo)
    days_with_commits(config)
  resplit/models.py:
    e: DeployMethod,EndpointStatus,CommitInfo,Endpoint,EndpointResult,DayResult,WalkConfig
    DeployMethod:
    EndpointStatus:
    CommitInfo:
    Endpoint: url(0),slug(0)
    EndpointResult:
    DayResult: ok_count(0),fail_count(0),health_pct(0)
    WalkConfig:
  resplit/reporter.py:
    e: save_json,_status_badge,_screenshot_html,save_html,save_day,save_timeline_index
    save_json(result)
    _status_badge(status)
    _screenshot_html(r;day_dir)
    save_html(result)
    save_day(result)
    save_timeline_index(results;output_dir)
  resplit/restorer.py:
    e: find_last_working_day,extract_endpoint,_find_backend_files,_is_page_endpoint,_write_readme
    find_last_working_day(endpoint_path;results_dir)
    extract_endpoint(repo;endpoint_path;working_day;target)
    _find_backend_files(repo;endpoint_path)
    _is_page_endpoint(path)
    _write_readme(target;endpoint_path;working_day;backend_files)
  resplit/screenshotter.py:
    e: take_screenshot,take_screenshots_batch,_playwright_shot,_batch_playwright,screenshot_endpoint,ScreenshotConfig,ScreenshotResult
    ScreenshotConfig:
    ScreenshotResult:
    take_screenshot(url;filename;cfg)
    take_screenshots_batch(urls;cfg)
    _playwright_shot(url;path;cfg)
    _batch_playwright(urls;cfg)
    screenshot_endpoint(url;slug;screenshots_dir)
  resplit/tester.py:
    e: run_tests,_testql_available,_run_via_testql,_parse_testql_results,_run_http_probe,_fallback_all_timeout
    run_tests(endpoints;config;day_dir)
    _testql_available()
    _run_via_testql(endpoints;config;day_dir)
    _parse_testql_results(results_path;endpoints;config)
    _run_http_probe(endpoints;config)
    _fallback_all_timeout(endpoints)
  tests/__init__.py:
  tests/test_deployer.py:
    e: test_detect_docker_compose_yml,test_detect_docker_compose_yaml,test_detect_uvicorn_server,test_detect_uvicorn_backend_server,test_detect_none
    test_detect_docker_compose_yml(tmp_path)
    test_detect_docker_compose_yaml(tmp_path)
    test_detect_uvicorn_server(tmp_path)
    test_detect_uvicorn_backend_server(tmp_path)
    test_detect_none(tmp_path)
  tests/test_endpoint_scanner.py:
    e: test_parse_openapi,test_ports_to_endpoints,test_scan_via_compose_labels,test_scan_endpoints_minimal_fallback
    test_parse_openapi()
    test_ports_to_endpoints()
    test_scan_via_compose_labels(tmp_path)
    test_scan_endpoints_minimal_fallback(tmp_path)
  tests/test_git_walker.py:
    e: test_get_commit_for_day_parses_output,test_get_commit_for_day_no_output,test_get_commit_for_day_git_error,test_days_with_commits_filters_none
    test_get_commit_for_day_parses_output()
    test_get_commit_for_day_no_output()
    test_get_commit_for_day_git_error()
    test_days_with_commits_filters_none()
  tests/test_models.py:
    e: test_endpoint_url,test_endpoint_url_strips_trailing_slash,test_endpoint_slug,test_day_result_health_pct_empty,test_day_result_health_pct,test_walk_config_defaults
    test_endpoint_url()
    test_endpoint_url_strips_trailing_slash()
    test_endpoint_slug()
    test_day_result_health_pct_empty()
    test_day_result_health_pct()
    test_walk_config_defaults()
  tests/test_reporter.py:
    e: _make_result,test_save_json_creates_files,test_save_json_results_content,test_save_html_creates_report,test_save_timeline_index
    _make_result(tmp_path)
    test_save_json_creates_files(tmp_path)
    test_save_json_results_content(tmp_path)
    test_save_html_creates_report(tmp_path)
    test_save_timeline_index(tmp_path)
  tests/test_restorer.py:
    e: _make_results_dir,test_find_last_working_day_found,test_find_last_working_day_not_found,test_find_backend_files,test_is_page_endpoint
    _make_results_dir(tmp_path;day;endpoint;status)
    test_find_last_working_day_found(tmp_path)
    test_find_last_working_day_not_found(tmp_path)
    test_find_backend_files(tmp_path)
    test_is_page_endpoint()
  tests/test_screenshotter.py:
    e: test_take_screenshot_playwright_not_installed,test_take_screenshot_success,test_take_screenshot_retry_then_succeed,test_take_screenshot_all_retries_fail,test_screenshot_endpoint_returns_path_on_success,test_screenshot_endpoint_returns_none_on_failure,test_take_screenshots_batch_playwright_missing
    test_take_screenshot_playwright_not_installed(tmp_path)
    test_take_screenshot_success(tmp_path)
    test_take_screenshot_retry_then_succeed(tmp_path)
    test_take_screenshot_all_retries_fail(tmp_path)
    test_screenshot_endpoint_returns_path_on_success(tmp_path)
    test_screenshot_endpoint_returns_none_on_failure(tmp_path)
    test_take_screenshots_batch_playwright_missing(tmp_path)
  tests/test_tester.py:
    e: _ep,test_testql_available_missing,test_testql_available_ok,test_parse_testql_results_ok,test_parse_testql_results_fail,test_parse_testql_results_missing_endpoint,test_run_http_probe_skip_non_get,test_run_http_probe_ok,test_run_http_probe_timeout,test_run_tests_uses_http_probe_when_no_testql_dir,test_fallback_all_timeout
    _ep(path;method)
    test_testql_available_missing()
    test_testql_available_ok()
    test_parse_testql_results_ok(tmp_path)
    test_parse_testql_results_fail(tmp_path)
    test_parse_testql_results_missing_endpoint(tmp_path)
    test_run_http_probe_skip_non_get()
    test_run_http_probe_ok()
    test_run_http_probe_timeout()
    test_run_tests_uses_http_probe_when_no_testql_dir(tmp_path)
    test_fallback_all_timeout()
```

## Source Map

*Top 5 modules by symbol density — signatures for LLM orientation.*

### `resplit.deployer` (`resplit/deployer.py`)

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

### `resplit.cli` (`resplit/cli.py`)

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

### `resplit.endpoint_scanner` (`resplit/endpoint_scanner.py`)

```python
def scan_endpoints(repo, config)  # CC=8, fan=7
def _scan_via_deta(repo, config)  # CC=3, fan=4
def _ports_to_endpoints(data, base_url)  # CC=5, fan=3
def _scan_via_openapi(base_url)  # CC=4, fan=4
def _parse_openapi(spec, base_url)  # CC=4, fan=5
def _scan_via_compose_labels(repo, config)  # CC=9, fan=13
```

### `resplit.git_walker` (`resplit/git_walker.py`)

```python
def _run_git(args, cwd)  # CC=1, fan=2
def get_commit_for_day(repo, day, earliest)  # CC=7, fan=8
def iter_days(config)  # CC=4, fan=3
def checkout(repo, sha)  # CC=1, fan=1
def restore_head(repo)  # CC=4, fan=1
def days_with_commits(config)  # CC=3, fan=1
```

### `resplit.reporter` (`resplit/reporter.py`)

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
| `report` *(in resplit.cli)* | 13 ⚠ | 0 | 31 | **31** |
| `dashboard` *(in resplit.cli)* | 6 | 0 | 22 | **22** |
| `extract_endpoint` *(in resplit.restorer)* | 9 | 0 | 19 | **19** |
| `_run_http_probe` *(in resplit.tester)* | 6 | 4 | 12 | **16** |
| `restore` *(in resplit.cli)* | 2 | 0 | 16 | **16** |
| `_batch_playwright` *(in resplit.screenshotter)* | 5 | 1 | 15 | **16** |
| `_parse_testql_results` *(in resplit.tester)* | 6 | 1 | 15 | **16** |
| `_scan_via_compose_labels` *(in resplit.endpoint_scanner)* | 9 | 1 | 14 | **15** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/resplit
# nodes: 51 | edges: 43 | modules: 10
# CC̄=1.2

HUBS[20]:
  resplit.cli.report
    CC=13  in:0  out:31  total:31
  resplit.cli.dashboard
    CC=6  in:0  out:22  total:22
  resplit.restorer.extract_endpoint
    CC=9  in:0  out:19  total:19
  resplit.tester._run_http_probe
    CC=6  in:4  out:12  total:16
  resplit.cli.restore
    CC=2  in:0  out:16  total:16
  resplit.screenshotter._batch_playwright
    CC=5  in:1  out:15  total:16
  resplit.tester._parse_testql_results
    CC=6  in:1  out:15  total:16
  resplit.endpoint_scanner._scan_via_compose_labels
    CC=9  in:1  out:14  total:15
  resplit.reporter.save_timeline_index
    CC=8  in:2  out:8  total:10
  resplit.screenshotter.take_screenshot
    CC=5  in:1  out:9  total:10
  resplit.dashboard.generate_dashboard
    CC=5  in:1  out:9  total:10
  resplit.reporter.save_json
    CC=6  in:1  out:9  total:10
  resplit.endpoint_scanner.scan_endpoints
    CC=8  in:1  out:9  total:10
  resplit.tester._run_via_testql
    CC=5  in:1  out:9  total:10
  resplit.endpoint_scanner._parse_openapi
    CC=4  in:1  out:8  total:9
  resplit.git_walker.get_commit_for_day
    CC=7  in:1  out:8  total:9
  resplit.screenshotter._playwright_shot
    CC=1  in:1  out:7  total:8
  resplit.reporter.save_html
    CC=9  in:1  out:7  total:8
  resplit.restorer._find_backend_files
    CC=7  in:1  out:7  total:8
  resplit.deployer._wait_healthy
    CC=4  in:2  out:6  total:8

MODULES:
  project.map.toon  [2 funcs]
    extract_endpoint  CC=0  out:0
    find_last_working_day  CC=0  out:0
  resplit.cli  [4 funcs]
    _attach_screenshots  CC=4  out:2
    dashboard  CC=6  out:22
    report  CC=13  out:31
    restore  CC=2  out:16
  resplit.dashboard  [4 funcs]
    _extract_avg_cc  CC=5  out:6
    _render_html  CC=5  out:4
    generate_dashboard  CC=5  out:9
    get_cc_for_day  CC=3  out:5
  resplit.deployer  [8 funcs]
    _compose_down  CC=2  out:4
    _compose_file  CC=4  out:3
    _compose_up  CC=2  out:6
    _uvicorn_start  CC=3  out:5
    _uvicorn_stop  CC=3  out:3
    _wait_healthy  CC=4  out:6
    start  CC=5  out:3
    stop  CC=5  out:2
  resplit.endpoint_scanner  [6 funcs]
    _parse_openapi  CC=4  out:8
    _ports_to_endpoints  CC=5  out:6
    _scan_via_compose_labels  CC=9  out:14
    _scan_via_deta  CC=3  out:4
    _scan_via_openapi  CC=4  out:4
    scan_endpoints  CC=8  out:9
  resplit.git_walker  [6 funcs]
    _run_git  CC=1  out:2
    checkout  CC=1  out:1
    days_with_commits  CC=3  out:1
    get_commit_for_day  CC=7  out:8
    iter_days  CC=4  out:4
    restore_head  CC=4  out:2
  resplit.reporter  [6 funcs]
    _screenshot_html  CC=3  out:2
    _status_badge  CC=1  out:1
    save_day  CC=1  out:2
    save_html  CC=9  out:7
    save_json  CC=6  out:9
    save_timeline_index  CC=8  out:8
  resplit.restorer  [4 funcs]
    _find_backend_files  CC=7  out:7
    _is_page_endpoint  CC=2  out:0
    _write_readme  CC=4  out:4
    extract_endpoint  CC=9  out:19
  resplit.screenshotter  [5 funcs]
    _batch_playwright  CC=5  out:15
    _playwright_shot  CC=1  out:7
    screenshot_endpoint  CC=2  out:2
    take_screenshot  CC=5  out:9
    take_screenshots_batch  CC=5  out:5
  resplit.tester  [6 funcs]
    _fallback_all_timeout  CC=2  out:1
    _parse_testql_results  CC=6  out:15
    _run_http_probe  CC=6  out:12
    _run_via_testql  CC=5  out:9
    _testql_available  CC=2  out:1
    run_tests  CC=4  out:4

EDGES:
  resplit.git_walker.get_commit_for_day → resplit.git_walker._run_git
  resplit.git_walker.iter_days → resplit.git_walker.get_commit_for_day
  resplit.git_walker.checkout → resplit.git_walker._run_git
  resplit.git_walker.restore_head → resplit.git_walker._run_git
  resplit.git_walker.days_with_commits → resplit.git_walker.iter_days
  resplit.reporter.save_html → resplit.reporter._screenshot_html
  resplit.reporter.save_html → resplit.reporter._status_badge
  resplit.reporter.save_day → resplit.reporter.save_json
  resplit.reporter.save_day → resplit.reporter.save_html
  resplit.deployer.start → resplit.deployer._compose_up
  resplit.deployer.start → resplit.deployer._uvicorn_start
  resplit.deployer.stop → resplit.deployer._compose_down
  resplit.deployer.stop → resplit.deployer._uvicorn_stop
  resplit.deployer._compose_up → resplit.deployer._compose_file
  resplit.deployer._compose_up → resplit.deployer._wait_healthy
  resplit.deployer._compose_down → resplit.deployer._compose_file
  resplit.deployer._uvicorn_start → resplit.deployer._wait_healthy
  resplit.endpoint_scanner.scan_endpoints → resplit.endpoint_scanner._scan_via_deta
  resplit.endpoint_scanner.scan_endpoints → resplit.endpoint_scanner._scan_via_openapi
  resplit.endpoint_scanner.scan_endpoints → resplit.endpoint_scanner._scan_via_compose_labels
  resplit.endpoint_scanner._scan_via_deta → resplit.endpoint_scanner._ports_to_endpoints
  resplit.endpoint_scanner._scan_via_openapi → resplit.endpoint_scanner._parse_openapi
  resplit.tester.run_tests → resplit.tester._run_http_probe
  resplit.tester.run_tests → resplit.tester._testql_available
  resplit.tester.run_tests → resplit.tester._run_via_testql
  resplit.tester._run_via_testql → resplit.tester._parse_testql_results
  resplit.tester._run_via_testql → resplit.tester._run_http_probe
  resplit.tester._run_via_testql → resplit.tester._fallback_all_timeout
  resplit.tester._parse_testql_results → resplit.tester._run_http_probe
  resplit.dashboard.get_cc_for_day → resplit.dashboard._extract_avg_cc
  resplit.dashboard.generate_dashboard → resplit.dashboard._render_html
  resplit.dashboard.generate_dashboard → resplit.dashboard.get_cc_for_day
  resplit.restorer.extract_endpoint → resplit.restorer._find_backend_files
  resplit.restorer.extract_endpoint → resplit.restorer._write_readme
  resplit.restorer.extract_endpoint → resplit.restorer._is_page_endpoint
  resplit.cli.restore → project.map.toon.find_last_working_day
  resplit.cli.restore → project.map.toon.extract_endpoint
  resplit.cli.report → resplit.reporter.save_timeline_index
  resplit.cli.dashboard → resplit.dashboard.generate_dashboard
  resplit.cli._attach_screenshots → resplit.screenshotter.screenshot_endpoint
  resplit.screenshotter.take_screenshot → resplit.screenshotter._playwright_shot
  resplit.screenshotter.take_screenshots_batch → resplit.screenshotter._batch_playwright
  resplit.screenshotter.screenshot_endpoint → resplit.screenshotter.take_screenshot
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Cli (1)

**`CLI Command Tests`**

### Integration (1)

**`Auto-generated from Python Tests`**

## Intent

Historical deployment analysis — walk git history, deploy per day, test all endpoints, capture screenshots, restore working fragments
