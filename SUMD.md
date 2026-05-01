# rebuild

Historical deployment analysis — walk git history, deploy per day, test all endpoints, capture screenshots, restore working fragments

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Interfaces](#interfaces)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [Deployment](#deployment)
- [Release Management (`goal.yaml`)](#release-management-goalyaml)
- [Code Analysis](#code-analysis)
- [Test Contracts](#test-contracts)
- [Intent](#intent)

## Metadata

- **name**: `rebuild`
- **version**: `0.1.7`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, testql(2), app.doql.less, goal.yaml, project/(2 analysis files)

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

## Interfaces

### CLI Entry Points

- `rebuild`

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
  name: rebuild
  version: 0.1.7
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

## Deployment

```bash markpact:run
pip install rebuild

# development install
pip install -e .[dev]
```

## Release Management (`goal.yaml`)

- **versioning**: `semver`
- **commits**: `conventional` scope=`rebuild`
- **changelog**: `keep-a-changelog`
- **build strategies**: `python`, `nodejs`, `rust`
- **version files**: `VERSION`, `pyproject.toml:version`, `rebuild/__init__.py:__version__`

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# resplit | 29f 2716L | python:20,shell:8,less:1 | 2026-05-01
# stats: 102 func | 9 cls | 29 mod | CC̄=3.8 | critical:2 | cycles:0
# alerts[5]: CC walk=15; CC report=13; CC _scan_via_compose_labels=9; CC save_html=9; CC extract_endpoint=9
# hotspots[5]: walk fan=30; report fan=22; dashboard fan=18; _scan_via_compose_labels fan=13; _batch_playwright fan=12
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[29]:
  app.doql.less,34
  examples/01-dry-run-walk/run.sh,19
  examples/02-docker-compose-project/run.sh,26
  examples/03-restore-endpoint/mock_results.sh,38
  examples/03-restore-endpoint/run.sh,31
  examples/restore_endpoint.sh,14
  examples/walk_dry_run.sh,14
  project.sh,41
  rebuild/__init__.py,11
  rebuild/cli.py,366
  rebuild/dashboard.py,189
  rebuild/deployer.py,155
  rebuild/endpoint_scanner.py,165
  rebuild/git_walker.py,132
  rebuild/models.py,110
  rebuild/reporter.py,236
  rebuild/restorer.py,188
  rebuild/screenshotter.py,172
  rebuild/tester.py,188
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
  rebuild/__init__.py:
  rebuild/cli.py:
    e: walk,restore,report,version,dashboard,_attach_screenshots,_print_day_summary,_print_summary_table
    walk(repo;days;date_from;date_to;output;deploy;health_url;base_url;screenshots;dry_run)
    restore(endpoint;repo;output;results_dir)
    report(results_dir)
    version()
    dashboard(results_dir;repo)
    _attach_screenshots(result;day_dir)
    _print_day_summary(result)
    _print_summary_table(results)
  rebuild/dashboard.py:
    e: get_cc_for_day,_extract_avg_cc,generate_dashboard,_render_html
    get_cc_for_day(repo;day)
    _extract_avg_cc(data)
    generate_dashboard(results;output_dir;repo)
    _render_html(days;health;cc;total_days)
  rebuild/deployer.py:
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
  rebuild/endpoint_scanner.py:
    e: scan_endpoints,_scan_via_deta,_ports_to_endpoints,_scan_via_openapi,_parse_openapi,_scan_via_compose_labels
    scan_endpoints(repo;config)
    _scan_via_deta(repo;config)
    _ports_to_endpoints(data;base_url)
    _scan_via_openapi(base_url)
    _parse_openapi(spec;base_url)
    _scan_via_compose_labels(repo;config)
  rebuild/git_walker.py:
    e: _run_git,get_commit_for_day,iter_days,checkout,restore_head,days_with_commits
    _run_git(args;cwd)
    get_commit_for_day(repo;day;earliest)
    iter_days(config)
    checkout(repo;sha)
    restore_head(repo)
    days_with_commits(config)
  rebuild/models.py:
    e: DeployMethod,EndpointStatus,CommitInfo,Endpoint,EndpointResult,DayResult,WalkConfig
    DeployMethod:
    EndpointStatus:
    CommitInfo:
    Endpoint: url(0),slug(0)
    EndpointResult:
    DayResult: ok_count(0),fail_count(0),health_pct(0)
    WalkConfig:
  rebuild/reporter.py:
    e: save_json,_status_badge,_screenshot_html,save_html,save_day,save_timeline_index
    save_json(result)
    _status_badge(status)
    _screenshot_html(r;day_dir)
    save_html(result)
    save_day(result)
    save_timeline_index(results;output_dir)
  rebuild/restorer.py:
    e: find_last_working_day,extract_endpoint,_find_backend_files,_is_page_endpoint,_write_readme
    find_last_working_day(endpoint_path;results_dir)
    extract_endpoint(repo;endpoint_path;working_day;target)
    _find_backend_files(repo;endpoint_path)
    _is_page_endpoint(path)
    _write_readme(target;endpoint_path;working_day;backend_files)
  rebuild/screenshotter.py:
    e: take_screenshot,take_screenshots_batch,_playwright_shot,_batch_playwright,screenshot_endpoint,ScreenshotConfig,ScreenshotResult
    ScreenshotConfig:
    ScreenshotResult:
    take_screenshot(url;filename;cfg)
    take_screenshots_batch(urls;cfg)
    _playwright_shot(url;path;cfg)
    _batch_playwright(urls;cfg)
    screenshot_endpoint(url;slug;screenshots_dir)
  rebuild/tester.py:
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

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Cli (1)

**`CLI Command Tests`**

### Integration (1)

**`Auto-generated from Python Tests`**

## Intent

Historical deployment analysis — walk git history, deploy per day, test all endpoints, capture screenshots, restore working fragments
