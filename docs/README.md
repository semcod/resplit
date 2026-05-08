<!-- code2docs:start --># rebuild

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.11-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-620-green)
> **620** functions | **161** classes | **176** files | CC̄ = 3.4

> Auto-generated project documentation from source code analysis.

**Author:** Tom Sapletta  
**License:** Apache-2.0[(LICENSE)](./LICENSE)  
**Repository:** [https://github.com/semcod/resplit](https://github.com/semcod/resplit)

## Installation

### From PyPI

```bash
pip install rebuild
```

### From Source

```bash
git clone https://github.com/semcod/resplit
cd rebuild
pip install -e .
```

### Optional Extras

```bash
pip install rebuild[screenshots]    # screenshots features
pip install rebuild[tui]    # tui features
pip install rebuild[semantic]    # semantic features
pip install rebuild[watch]    # file watcher (watchdog)
pip install rebuild[api]    # api features
pip install rebuild[full]    # full features
pip install rebuild[dev]    # development tools
```

## Quick Start

### CLI Usage

```bash
# Generate full documentation for your project
rebuild ./my-project

# Only regenerate README
rebuild ./my-project --readme-only

# Preview what would be generated (no file writes)
rebuild ./my-project --dry-run

# Check documentation health
rebuild check ./my-project

# Sync — regenerate only changed modules
rebuild sync ./my-project
```

### Python API

```python
from rebuild import generate_readme, generate_docs, Code2DocsConfig

# Quick: generate README
generate_readme("./my-project")

# Full: generate all documentation
config = Code2DocsConfig(project_name="mylib", verbose=True)
docs = generate_docs("./my-project", config=config)
```




## Architecture

```
rebuild/
├── mkdocs
├── goal
├── rebuild/
├── infra-map
├── Makefile
├── PLAN
    ├── example
    ├── pre-commit-config
├── pyqual
├── ANALYSIS
├── pyproject
├── tree
├── TODO
├── CHANGELOG
├── Dockerfile
├── project
├── README
    ├── case_study_c2004
    ├── changelog
    ├── usage
    ├── c2004
    ├── index
    ├── mutation_testing
    ├── benchmarks
    ├── architecture
    ├── README
        ├── plugins
        ├── auto-pr
        ├── walk
        ├── analyze
        ├── refactor
        ├── installation
        ├── quickstart
        ├── configuration
        ├── cli
        ├── config
    ├── rebuild
    ├── walk_dry_run
    ├── Makefile
    ├── restore_endpoint
        ├── run
        ├── rebuild
        ├── mock_results
        ├── README
        ├── README
        ├── README
        ├── run
        ├── rebuild
        ├── docker-compose
        ├── README
        ├── circleci
        ├── github-actions
        ├── gitlab-ci
        ├── README
        ├── run
        ├── rebuild
        ├── README
        ├── pipeline
        ├── README
        ├── README
                        ├── main
                        ├── main
                        ├── main
                        ├── main
            ├── docker-compose
            ├── Dockerfile
    ├── benchmark_scanner_cache
    ├── bump_version
    ├── run_c2004_full
    ├── run_mutation_tests
            ├── toon
            ├── toon
    ├── __main__
        ├── shell_adapter
        ├── config_schema
        ├── config_template
        ├── config_loader
    ├── infrastructure/
        ├── http_adapter
        ├── event_bus
        ├── event_store
        ├── vector_search
        ├── git_truth_analyzer
        ├── duplication_engine
        ├── service_similarity
        ├── graph_exporter
        ├── service_graph
        ├── accelerated_pipeline
        ├── base_pipeline
        ├── pipeline
            ├── analyze_commands
            ├── base
            ├── snapshot_commands
        ├── commands/
            ├── walk_commands
            ├── restore_service
            ├── endpoint_trend_service
            ├── smart_test_selector
            ├── tui_data_service
            ├── summary_service
            ├── base
            ├── accelerator_deploy
            ├── pr_service
            ├── history_service
            ├── git_service
            ├── patcher_service
            ├── deploy_strategy
            ├── regression_service
            ├── deploy_service
            ├── reporter_service
            ├── llm_service
            ├── screenshot_service
            ├── nlp_service
            ├── worktree_manager
            ├── scanner_service
            ├── db_snapshot_manager
            ├── parallel_test_engine
            ├── event_service
            ├── override_service
            ├── notification_service
                ├── timeline_html
                ├── summary_export
                ├── reporter
            ├── reporting/
                ├── chart_builder
                ├── formatters
                ├── _html_assets
                ├── day_html
            ├── base
            ├── walk_queries
        ├── queries/
        ├── base
        ├── registry
    ├── plugins/
        ├── dashboard
        ├── cli
        ├── evolution_viz
            ├── analyze_command
            ├── helpers
            ├── walk_command
            ├── refactor_command
            ├── watch_command
            ├── app
        ├── tui/
            ├── compat
                ├── history_screen
                ├── restore_screen
                ├── walk_screens
                ├── project_screen
                ├── help_screen
                ├── endpoint_screens
            ├── app
        ├── api/
            ├── metrics
        ├── events/
        ├── commit
        ├── context
        ├── timeline
        ├── mvp_protocol
        ├── dsl
        ├── models
        ├── dsl_v2
        ├── endpoint
        ├── day_result
            ├── domain_events
        ├── recommendation_engine
        ├── refactor_executor
```

## API Overview

### Classes

- **`ShellAdapter`** — Adapter for shell command execution.
- **`DeployConfig`** — —
- **`OutputConfig`** — —
- **`AuthConfig`** — —
- **`ProjectConfig`** — —
- **`RebuildConfig`** — Root model for rebuild.yaml.
- **`ConfigSchemaValidator`** — Drop-in pydantic-based replacement for ConfigLoader.validate().
- **`ConfigLoader`** — Loader for rebuild.yaml configuration files.
- **`HttpAdapter`** — Adapter for HTTP requests.
- **`EventBus`** — Publish/subscribe event bus.
- **`EventStore`** — Append-only SQLite event store.
- **`VectorSearchHit`** — —
- **`VectorSearchIndex`** — SQLite-backed vector index for semantic lookup of code fragments.
- **`FunctionQuality`** — —
- **`GitTruthAnalyzer`** — Analyzes code evolution and identifies the 'best' versions of functions.
- **`CodeFragment`** — —
- **`DuplicateGroup`** — —
- **`DuplicationEngine`** — Engine for detecting structural and semantic duplication in codebases.
- **`ServiceSimilarity`** — —
- **`ServiceSimilarityAnalyzer`** — Analyzer for detecting overlapping responsibilities between services.
- **`GraphExporter`** — Exports ServiceGraph to an interactive D3.js HTML visualization.
- **`ServiceNode`** — —
- **`ServiceGraphBuilder`** — Builds a dependency graph of services within the application layer.
- **`CrossRepoDependency`** — —
- **`CrossRepoCloneGroup`** — —
- **`MultiRepoReport`** — —
- **`MultiRepoAnalyzer`** — Analyze cross-repo dependencies and shared structural code clones.
- **`AcceleratedPipeline`** — Ultra-fast pipeline using:
- **`BasePipeline`** — Shared infrastructure for Pipeline and AcceleratedPipeline.
- **`Pipeline`** — Orchestrates the analysis process (Command).
- **`AnalyzeCommand`** — Trigger codebase analysis.
- **`AnalyzeCommandResult`** — Result of an AnalyzeCommand.
- **`NotifyCommand`** — Send a webhook notification.
- **`NotifyCommandResult`** — Result of a NotifyCommand.
- **`Command`** — Base class for all CQRS commands (write side).
- **`CommandResult`** — Base class for all command results.
- **`CommandHandler`** — Handle a single Command type and return a CommandResult.
- **`CommandBus`** — Dispatch Commands to registered handlers.
- **`CreateSnapshotCommand`** — Create a DB snapshot.
- **`CreateSnapshotCommandResult`** — Result of CreateSnapshotCommand.
- **`PruneSnapshotsCommand`** — Prune old snapshots using LRU policy.
- **`PruneSnapshotsCommandResult`** — Result of PruneSnapshotsCommand.
- **`WalkCommand`** — Trigger a historical walk of a git repository.
- **`WalkCommandResult`** — Result of a WalkCommand.
- **`RestoreService`** — Service for restoring a working endpoint from git history.
- **`EndpointTrendPoint`** — A single chronological point in an endpoint-count trend.
- **`ChangedModule`** — Information about a changed module/file.
- **`TestSelection`** — Result of test selection process.
- **`SmartTestSelector`** — Selectively runs tests based on git diff analysis.
- **`TUIDataService`** — Service for TUI data operations - loads results, calculates metrics, computes diffs.
- **`RefactorSuggestion`** — A single refactor suggestion.
- **`SummaryResult`** — Result of AI summary generation.
- **`SummaryService`** — Service for generating AI summaries and refactor suggestions from analysis results.
- **`Service`** — Standard interface for all application services.
- **`AcceleratorDeployService`** — 10x faster deployment using:
- **`Platform`** — Git platform for PR operations.
- **`PRConfig`** — Configuration for creating a pull/merge request.
- **`PRResult`** — Result of PR creation.
- **`PRService`** — Service for creating pull/merge requests on GitHub/GitLab.
- **`HistoryService`** — Service for loading and managing historical scan results from disk.
- **`GitService`** — Service for interacting with Git repositories and history.
- **`PatcherService`** — Service for patching files in the repo clone.
- **`DeployStrategy`** — Protocol for deployment strategies.
- **`HealthTrendPoint`** — A single chronological point in a health-pct trend.
- **`DeployService`** — Service for managing the lifecycle of the service being analyzed.
- **`LLMService`** — Service for interacting with LLMs via LiteLLM.
- **`ScreenshotConfig`** — —
- **`ScreenshotService`** — Service for capturing screenshots of endpoints.
- **`Intent`** — Intents for natural language commands.
- **`NLPCommand`** — Parsed natural language command.
- **`NLPService`** — Service for parsing natural language commands into DSL/CLI commands.
- **`WorktreeInfo`** — Information about a git worktree.
- **`WorktreeManager`** — Manages git worktrees for ultra-fast branch/commit switching.
- **`ScannerService`** — Service for discovering API endpoints in a repository.
- **`SnapshotInfo`** — Metadata about a database snapshot.
- **`DBSnapshotManager`** — Manages database snapshots for instant state restore.
- **`EndpointDependency`** — Defines endpoint dependency relationship.
- **`EndpointDependencyGraph`** — Builds and manages endpoint dependency graph.
- **`ParallelTestEngine`** — High-performance parallel test execution.
- **`EventType`** — Types of pipeline events for real-time monitoring.
- **`PipelineEvent`** — A single pipeline event for real-time streaming.
- **`EventService`** — Service for publishing and subscribing to pipeline events in real-time.
- **`OverrideService`** — Service for applying manual overrides (patches) to the repo clone.
- **`NotificationEvent`** — —
- **`NotificationPayload`** — —
- **`WebhookConfig`** — —
- **`NotificationService`** — Send webhook notifications on rebuild events.
- **`ReporterService`** — Thin facade orchestrating the per-day / timeline / summary writers.
- **`Query`** — Base class for all CQRS queries (read side).
- **`QueryResult`** — Base class for all query results.
- **`QueryHandler`** — Handle a single Query type and return a QueryResult.
- **`QueryBus`** — Dispatch Queries to registered handlers.
- **`GetWalkHistoryQuery`** — Get historical walk results from output directory.
- **`WalkHistoryResult`** — Result of GetWalkHistoryQuery.
- **`GetDayResultQuery`** — Get results for a single day.
- **`DayResultQueryResult`** — Result of GetDayResultQuery.
- **`GetSnapshotStatsQuery`** — Get statistics about saved DB snapshots.
- **`SnapshotStatsResult`** — Result of GetSnapshotStatsQuery.
- **`GetPluginsQuery`** — List installed plugins.
- **`PluginsQueryResult`** — Result of GetPluginsQuery.
- **`ScanResult`** — Generic result produced by a scanner plugin.
- **`BaseScanner`** — Base class for rebuild scanner plugins.
- **`BaseReporter`** — Base class for rebuild reporter plugins.
- **`PluginRegistry`** — Central registry for rebuild plugins.
- **`DSLRequest`** — —
- **`NLPRequest`** — —
- **`PipelineEvent`** — —
- **`CommitInfo`** — —
- **`EndpointContext`** — —
- **`SnapshotType`** — Type of dependency snapshot.
- **`DependencyEdge`** — A single dependency relationship between modules.
- **`ModuleNode`** — A module in the dependency graph.
- **`GraphSnapshot`** — A snapshot of the dependency graph at a specific point in time.
- **`Timeline`** — Timeline of dependency graph snapshots for evolution playback.
- **`MessageType`** — MVP protocol message types.
- **`MVPMessage`** — MVP protocol message.
- **`MVPProtocolHandler`** — Handler for MVP protocol communication.
- **`MVPServer`** — MVP protocol server for handling incoming connections.
- **`Command`** — DSL command types.
- **`AnalyzeType`** — Analysis types for DSL.
- **`DSLCommand`** — Parsed DSL command.
- **`DSLParser`** — Parser for rebuild DSL syntax.
- **`DSLInterpreter`** — Interpreter for executing parsed DSL commands.
- **`DeployMethod`** — —
- **`WalkConfig`** — —
- **`WalkDSL`** — —
- **`AnalyzeDSL`** — —
- **`SnapshotDSL`** — —
- **`PruneDSL`** — —
- **`HistoryDSL`** — —
- **`PluginsDSL`** — —
- **`HelpDSL`** — —
- **`DSLParseError`** — —
- **`DSLParser`** — Parse a DSL string into a validated Pydantic model,
- **`NLPMapper`** — Rule-based NLP → DSL mapper.
- **`DSLShell`** — Interactive REPL for the rebuild DSL.
- **`EndpointStatus`** — —
- **`Endpoint`** — —
- **`EndpointResult`** — —
- **`DeployErrorCategory`** — —
- **`DayResult`** — —
- **`PipelineEvent`** — —
- **`DomainEvent`** — Base class for all domain events.
- **`WalkStartedEvent`** — —
- **`CommitCheckedOutEvent`** — —
- **`DeployStartedEvent`** — —
- **`DeployFinishedEvent`** — —
- **`DeployFailedEvent`** — —
- **`HealthCheckPassedEvent`** — —
- **`HealthCheckFailedEvent`** — —
- **`EndpointTestedEvent`** — —
- **`DayFinishedEvent`** — —
- **`WalkFinishedEvent`** — —
- **`AnalysisStartedEvent`** — —
- **`AnalysisFinishedEvent`** — —
- **`SnapshotCreatedEvent`** — —
- **`SnapshotPrunedEvent`** — —
- **`NotificationSentEvent`** — —
- **`RefactorSuggestion`** — —
- **`RecommendationEngine`** — Synthesizes analysis data into prioritized refactor suggestions.
- **`RefactorExecutor`** — Executes refactoring suggestions on the filesystem.

### Functions

- `print()` — —
- `print()` — —
- `send_mvp_command()` — —
- `print()` — —
- `sendMVPCommand()` — —
- `health()` — —
- `get_manifest()` — —
- `list_pages()` — —
- `serve_ui(filename)` — —
- `serve_model(filename)` — —
- `list_models()` — —
- `index()` — —
- `module_index()` — —
- `health()` — —
- `get_manifest()` — —
- `list_pages()` — —
- `serve_ui(filename)` — —
- `serve_model(filename)` — —
- `list_models()` — —
- `index()` — —
- `module_index()` — —
- `health()` — —
- `get_manifest()` — —
- `list_pages()` — —
- `serve_ui(filename)` — —
- `serve_model(filename)` — —
- `list_models()` — —
- `index()` — —
- `module_index()` — —
- `health()` — —
- `get_manifest()` — —
- `list_pages()` — —
- `serve_ui(filename)` — —
- `serve_model(filename)` — —
- `list_models()` — —
- `index()` — —
- `module_index()` — —
- `setup_repo(repo, n_files)` — Create *n_files* FastAPI module files inside *repo*.
- `churn(files, pct)` — Mutate ``ceil(pct * len(files))`` files in-place. Returns count touched.
- `run_walk(repo, files, n_commits, churn_pct)` — Run *n_commits* sequential scans, mutating *churn_pct* of files between them.
- `main()` — —
- `read_version()` — —
- `bump(version, part)` — —
- `update_init(new_version, dry_run)` — —
- `update_pyproject(new_version, dry_run)` — —
- `collect_unreleased_entries()` — Collect lines between [Unreleased] and the next ## [ section.
- `get_git_log_since_last_tag()` — Return one-line git log entries since the last tag.
- `categorize_commits(commits)` — —
- `build_new_section(new_version, commits, unreleased)` — —
- `update_changelog(new_version, dry_run)` — —
- `main()` — —
- `print()` — —
- `all()` — —
- `load_and_validate(path)` — Load a YAML file and validate against RebuildConfig schema.
- `get_event_bus()` — —
- `set_event_bus(bus)` — —
- `compute_endpoint_count_trend(results, warning_threshold_pct)` — Compute the per-day endpoint-count trend with warning flags.
- `compute_endpoint_count_trend_dict(results_asc, warning_threshold_pct)` — Adapter — return the trend as a ``{day_str: label}`` mapping.
- `compute_endpoint_count_trend_labels(results, warning_threshold_pct)` — Adapter — return labels in chronological order as a flat list.
- `load_config_from_env()` — Load PR configuration from environment variables.
- `compute_health_trend(results, regression_threshold)` — Compute the per-day health trend with regression flags.
- `compute_health_trend_dict(results_asc, regression_threshold)` — Adapter — return the trend as a ``{day_str: label}`` mapping.
- `compute_health_trend_labels(results, regression_threshold)` — Adapter — return labels in chronological order as a flat list.
- `get_event_service()` — Get the global event service singleton.
- `build_export_data(results)` — Build the JSON-serialisable list used by ``history.json`` and timeline JS.
- `render_timeline_html(results, output_dir)` — Render the full ``index.html`` document for the cross-day timeline.
- `write_csv(results, output_dir)` — Write ``summary.csv`` with one row per day. Returns the destination path.
- `write_markdown(results, output_dir)` — Write ``summary.md`` with a Markdown table of walk results.
- `generate_trend_chart(results)` — —
- `generate_endpoint_diff(results)` — —
- `to_yaml(data, indent)` — —
- `to_toon(result)` — —
- `status_badge(status)` — —
- `classify_error(result)` — —
- `render_endpoint_row(endpoint_result)` — Render a single ``<tr>`` for the per-day endpoint table.
- `render_endpoint_rows(result)` — Render concatenated ``<tr>`` rows for ``result.endpoint_results``.
- `render_deploy_log(result)` — —
- `render_deploy_category(result)` — —
- `render_deploy_section(result)` — Render the deploy status block (or empty string for dry-run).
- `render_day_html(result, data)` — Render the full per-day ``report.html`` document.
- `load_plugins()` — Return the default registry, discovering plugins on first call.
- `reset_registry()` — Reset the default registry (useful in tests).
- `get_cc_for_day(repo, day)` — Wywołuje `toon <repo> --format json` i zwraca średnie CC dla danego dnia.
- `generate_dashboard(results, output_dir, repo)` — Generuje dashboard.html w output_dir.
- `init(path, force)` — Zainicjuj nowy projekt rebuild i wygeneruj domyślną konfigurację.
- `walk(ctx, repo, days, date_from)` — Przejdź historię git dzień po dniu, deployuj i testuj endpointy.
- `restore(endpoint, repo, output, results_dir)` — Przywróć działający endpoint jako izolowany projekt.
- `report(results_dir)` — Wygeneruj zbiorczy raport z istniejących wyników.
- `dashboard(results_dir, repo)` — Wygeneruj dashboard porównawczy: timeline health% + CC.
- `accelerator(repo, days, date_from, date_to)` — ⚡ Ultra-szybki tryb 10x - worktree + hot reload + parallel testing.
- `serve(results_dir, port)` — Uruchom lokalny serwer HTTP z raportami i otwórz przeglądarkę.
- `tui()` — Interaktywne menu TUI: wybór projektu → walk → historia → diff → restore.
- `version()` — Pokaż wersję rebuild.
- `auto_pr(analysis_file, platform, token, repo_owner)` — Utwórz Pull/Merge Request z AI-generated summary z wyników analizy.
- `evolution(timeline_file, output, title)` — Generuj wizualizację D3.js Code Evolution playback z timeline snapshots.
- `dsl(script, command, execute)` — Wykonaj DSL (Domain Specific Language) komendy rebuild.
- `nlp(text, to_dsl, to_cli)` — Parsuj komendę w języku naturalnym i konwertuj na DSL/CLI.
- `mvp(host, port)` — Uruchom MVP protocol server.
- `watch(repo, output, health_url, base_url)` — [Long-running] Obserwuj zmiany w repo i uruchamiaj rebuild walk (--dry-run) automatycznie.
- `duplicates(path, min_lines, semantic, semantic_model)` — [Query] Znajdź strukturalne i semantyczne duplikaty kodu.
- `vector_build(path, index, min_lines, model)` — [Query] Zbuduj lokalny indeks wektorowy fragmentów kodu.
- `vector_query(query, index, top_k, min_score)` — [Query] Wyszukaj semantycznie podobne fragmenty w indeksie wektorowym.
- `multi_repo(repos, min_lines, export)` — [Query] Analiza zależności i klonów kodu między wieloma repozytoriami.
- `services(path, export)` — [Query] Wykryj nakładające się odpowiedzialności i powiązania między serwisami.
- `truth(file, function, repo)` — [Query] Znajdź 'najprawdziwszą' wersję funkcji w historii git.
- `plan(path, ai)` — [Query] Wygeneruj plan refaktoryzacji z opcjonalnym wsparciem AI.
- `pr(path)` — [Query] Wygeneruj profesjonalny opis Pull Requesta (wymaga AI).
- `execute(path, force)` — [Command] Wykonaj automatycznie plan refaktoryzacji.
- `plugins(verbose)` — Wylistuj zainstalowane pluginy (scanners, reporters).
- `generate_evolution_html(timeline_path, output_path, title)` — Generate HTML file with D3.js evolution playback visualization.
- `duplicates_command(path, min_lines, semantic, semantic_model)` — —
- `vector_build_command(path, index, min_lines, model)` — —
- `vector_query_command(query, index, top_k, min_score)` — —
- `multi_repo_command(repos, min_lines, export, console)` — —
- `services_command(path, export, console)` — —
- `truth_command(file, function, repo, console)` — —
- `collect_cli_overrides(ctx, names)` — Build a ``{param_name: was_explicitly_passed_on_cli}`` mapping.
- `print_report_links(output, port, console)` — —
- `compute_health_trend_labels(results, regression_threshold)` — —
- `compute_endpoint_count_trend_labels(results, warning_threshold_pct)` — —
- `print_summary_table(results, console)` — —
- `serve_reports(output, port, console)` — —
- `walk_command(repo, days, date_from, date_to)` — —
- `accelerator_command(repo, days, date_from, date_to)` — —
- `plan_command(path, ai, console)` — —
- `pr_command(path, console)` — —
- `execute_command(path, force, console)` — —
- `watch_command(repo, output, health_url, base_url)` — Run ``rebuild watch`` on *repo*.
- `launch_tui()` — Uruchamia TUI. Sprawdza dostępność Textual.
- `create_app(command_bus, query_bus, event_store, event_bus)` — Create and return a FastAPI application.
- `setup_metrics(app, registry)` — Register Prometheus metrics middleware and /metrics endpoint on *app*.


## Project Structure

📄 `.pre-commit-config`
📄 `ANALYSIS`
📄 `CHANGELOG`
📄 `Dockerfile`
📄 `Makefile` (2 functions)
📄 `PLAN`
📄 `README`
📄 `TODO`
📄 `docker-compose.example`
📄 `docs.README`
📄 `docs.architecture`
📄 `docs.benchmarks`
📄 `docs.c2004`
📄 `docs.case_study_c2004`
📄 `docs.changelog`
📄 `docs.getting-started.configuration`
📄 `docs.getting-started.installation`
📄 `docs.getting-started.quickstart`
📄 `docs.guide.analyze`
📄 `docs.guide.auto-pr`
📄 `docs.guide.plugins`
📄 `docs.guide.refactor`
📄 `docs.guide.walk`
📄 `docs.index`
📄 `docs.mutation_testing`
📄 `docs.reference.cli`
📄 `docs.reference.config`
📄 `docs.usage`
📄 `examples.01-dry-run-walk.README`
📄 `examples.01-dry-run-walk.rebuild`
📄 `examples.01-dry-run-walk.run`
📄 `examples.02-docker-compose-project.README`
📄 `examples.02-docker-compose-project.docker-compose`
📄 `examples.02-docker-compose-project.rebuild`
📄 `examples.02-docker-compose-project.run`
📄 `examples.03-restore-endpoint.README`
📄 `examples.03-restore-endpoint.mock_results`
📄 `examples.03-restore-endpoint.rebuild`
📄 `examples.03-restore-endpoint.run`
📄 `examples.05-ci-integrations.README`
📄 `examples.05-ci-integrations.circleci`
📄 `examples.05-ci-integrations.github-actions`
📄 `examples.05-ci-integrations.gitlab-ci`
📄 `examples.07-dsl-script.README`
📄 `examples.07-dsl-script.pipeline`
📄 `examples.08-nlp-commands.README` (4 functions)
📄 `examples.09-mvp-protocol.README` (5 functions)
📄 `examples.Makefile`
📄 `examples.rebuild`
📄 `examples.restore_endpoint`
📄 `examples.walk_dry_run`
📄 `goal`
📄 `infra-map`
📄 `mkdocs`
📄 `project`
📄 `pyproject`
📄 `pyqual`
📦 `rebuild`
📄 `rebuild.__main__`
📄 `rebuild.analysis.duplication_engine` (20 functions, 3 classes)
📄 `rebuild.analysis.git_truth_analyzer` (5 functions, 2 classes)
📄 `rebuild.analysis.graph_exporter` (3 functions, 1 classes)
📄 `rebuild.analysis.service_graph` (17 functions, 6 classes)
📄 `rebuild.analysis.service_similarity` (2 functions, 2 classes)
📄 `rebuild.analysis.vector_search` (11 functions, 2 classes)
📄 `rebuild.application.accelerated_pipeline` (19 functions, 1 classes)
📄 `rebuild.application.base_pipeline` (5 functions, 1 classes)
📦 `rebuild.application.commands`
📄 `rebuild.application.commands.analyze_commands` (1 functions, 4 classes)
📄 `rebuild.application.commands.base` (4 functions, 4 classes)
📄 `rebuild.application.commands.snapshot_commands` (4 classes)
📄 `rebuild.application.commands.walk_commands` (2 functions, 2 classes)
📄 `rebuild.application.pipeline` (12 functions, 1 classes)
📦 `rebuild.application.queries`
📄 `rebuild.application.queries.base` (4 functions, 4 classes)
📄 `rebuild.application.queries.walk_queries` (8 classes)
📄 `rebuild.application.services.accelerator_deploy` (23 functions, 1 classes)
📄 `rebuild.application.services.base` (1 functions, 1 classes)
📄 `rebuild.application.services.db_snapshot_manager` (22 functions, 2 classes)
📄 `rebuild.application.services.deploy_service` (24 functions, 1 classes)
📄 `rebuild.application.services.deploy_strategy` (2 functions, 1 classes)
📄 `rebuild.application.services.endpoint_trend_service` (3 functions, 1 classes)
📄 `rebuild.application.services.event_service` (9 functions, 3 classes)
📄 `rebuild.application.services.git_service` (10 functions, 1 classes)
📄 `rebuild.application.services.history_service` (3 functions, 1 classes)
📄 `rebuild.application.services.llm_service` (4 functions, 1 classes)
📄 `rebuild.application.services.nlp_service` (6 functions, 3 classes)
📄 `rebuild.application.services.notification_service` (14 functions, 4 classes)
📄 `rebuild.application.services.override_service` (1 functions, 1 classes)
📄 `rebuild.application.services.parallel_test_engine` (25 functions, 3 classes)
📄 `rebuild.application.services.patcher_service` (4 functions, 1 classes)
📄 `rebuild.application.services.pr_service` (6 functions, 4 classes)
📄 `rebuild.application.services.regression_service` (3 functions, 1 classes)
📄 `rebuild.application.services.reporter_service`
📦 `rebuild.application.services.reporting`
📄 `rebuild.application.services.reporting._html_assets`
📄 `rebuild.application.services.reporting.chart_builder` (2 functions)
📄 `rebuild.application.services.reporting.day_html` (6 functions)
📄 `rebuild.application.services.reporting.formatters` (5 functions)
📄 `rebuild.application.services.reporting.reporter` (14 functions, 1 classes)
📄 `rebuild.application.services.reporting.summary_export` (2 functions)
📄 `rebuild.application.services.reporting.timeline_html` (4 functions)
📄 `rebuild.application.services.restore_service` (7 functions, 1 classes)
📄 `rebuild.application.services.scanner_service` (21 functions, 1 classes)
📄 `rebuild.application.services.screenshot_service` (2 functions, 2 classes)
📄 `rebuild.application.services.smart_test_selector` (11 functions, 3 classes)
📄 `rebuild.application.services.summary_service` (5 functions, 3 classes)
📄 `rebuild.application.services.tui_data_service` (5 functions, 1 classes)
📄 `rebuild.application.services.worktree_manager` (10 functions, 2 classes)
📄 `rebuild.domain.commit` (1 classes)
📄 `rebuild.domain.context` (1 classes)
📄 `rebuild.domain.day_result` (1 functions, 2 classes)
📄 `rebuild.domain.dsl` (13 functions, 5 classes)
📄 `rebuild.domain.dsl_v2` (11 functions, 11 classes)
📄 `rebuild.domain.endpoint` (3 classes)
📦 `rebuild.domain.events`
📄 `rebuild.domain.events.domain_events` (4 functions, 17 classes)
📄 `rebuild.domain.models` (2 classes)
📄 `rebuild.domain.mvp_protocol` (14 functions, 4 classes)
📄 `rebuild.domain.timeline` (7 functions, 5 classes)
📦 `rebuild.infrastructure`
📄 `rebuild.infrastructure.config_loader` (13 functions, 1 classes)
📄 `rebuild.infrastructure.config_schema` (9 functions, 6 classes)
📄 `rebuild.infrastructure.config_template`
📄 `rebuild.infrastructure.event_bus` (12 functions, 1 classes)
📄 `rebuild.infrastructure.event_store` (8 functions, 1 classes)
📄 `rebuild.infrastructure.http_adapter` (7 functions, 1 classes)
📄 `rebuild.infrastructure.shell_adapter` (3 functions, 1 classes)
📦 `rebuild.interfaces.api`
📄 `rebuild.interfaces.api.app` (1 functions, 2 classes)
📄 `rebuild.interfaces.api.metrics` (2 functions)
📄 `rebuild.interfaces.cli` (30 functions)
📄 `rebuild.interfaces.commands.analyze_command` (6 functions)
📄 `rebuild.interfaces.commands.helpers` (6 functions)
📄 `rebuild.interfaces.commands.refactor_command` (4 functions)
📄 `rebuild.interfaces.commands.walk_command` (11 functions)
📄 `rebuild.interfaces.commands.watch_command` (4 functions)
📄 `rebuild.interfaces.dashboard` (4 functions)
📄 `rebuild.interfaces.evolution_viz` (2 functions)
📦 `rebuild.interfaces.tui`
📄 `rebuild.interfaces.tui.app` (1 functions)
📄 `rebuild.interfaces.tui.compat`
📄 `rebuild.interfaces.tui.screens.endpoint_screens`
📄 `rebuild.interfaces.tui.screens.help_screen`
📄 `rebuild.interfaces.tui.screens.history_screen`
📄 `rebuild.interfaces.tui.screens.project_screen`
📄 `rebuild.interfaces.tui.screens.restore_screen`
📄 `rebuild.interfaces.tui.screens.walk_screens`
📦 `rebuild.plugins`
📄 `rebuild.plugins.base` (4 functions, 3 classes)
📄 `rebuild.plugins.registry` (14 functions, 1 classes)
📄 `rebuild.refactor.recommendation_engine` (6 functions, 2 classes)
📄 `rebuild.refactor.refactor_executor` (3 functions, 1 classes)
📄 `restored_c2004_health.api-health.README`
📄 `restored_c2004_health.api-health.backend.modules.connect-config-network.api.main` (9 functions)
📄 `restored_c2004_health.api-health.backend.modules.connect-id-user-list.api.main` (9 functions)
📄 `restored_c2004_health.api-health.backend.modules.connect-manager-library.api.main` (9 functions)
📄 `restored_c2004_health.api-health.backend.modules.connect-reports-month.api.main` (9 functions)
📄 `restored_c2004_health.api-health.docker.Dockerfile`
📄 `restored_c2004_health.api-health.docker.docker-compose`
📄 `scripts.benchmark_scanner_cache` (6 functions)
📄 `scripts.bump_version` (10 functions)
📄 `scripts.run_c2004_full` (2 functions)
📄 `scripts.run_mutation_tests`
📄 `testql-scenarios.generated-cli-tests.testql.toon`
📄 `testql-scenarios.generated-from-pytests.testql.toon` (2 functions)
📄 `tree`

## Requirements

- Python >= >=3.11
- typer >=0.12- rich >=13- gitpython >=3.1- httpx >=0.27- pyyaml >=6- pydantic >=2- deta >=0.1- astor >=0.8- goal >=2.1.0- costs >=0.1.20- pfix >=0.1.60

## Contributing

**Contributors:**
- Tom Softreck <tom@sapletta.com>
- Tom Sapletta <tom-sapletta-com@users.noreply.github.com>
- github-actions[bot] <github-actions[bot]@users.noreply.github.com>

We welcome contributions! Open an issue or pull request to get started.
### Development Setup

```bash
# Clone the repository
git clone https://github.com/semcod/resplit
cd rebuild

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## Documentation

- 🏛️ [Architecture](./docs/architecture.md) — Architecture with diagrams
- 💡 [Examples](./examples) — Usage examples and code samples
- ⚙️ [MkDocs Config](./mkdocs.yml) — MkDocs site configuration

### Generated Files

| Output | Description | Link |
|--------|-------------|------|
| `README.md` | Project overview (this file) | — |
| `docs/architecture.md` | Architecture with diagrams | [View](./docs/architecture.md) |
| `examples` | Usage examples and code samples | [View](./examples) |
| `mkdocs.yml` | MkDocs site configuration | [View](./mkdocs.yml) |

<!-- code2docs:end -->