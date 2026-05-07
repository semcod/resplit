# System Architecture Analysis
<!-- generated in 0.00s -->

## Overview

- **Project**: /home/tom/github/semcod/rebuild
- **Primary Language**: python
- **Languages**: python: 92, md: 29, yaml: 9, shell: 8, yml: 3
- **Analysis Mode**: static
- **Total Functions**: 587
- **Total Classes**: 159
- **Modules**: 148
- **Entry Points**: 517

## Architecture by Module

### rebuild.interfaces.cli
- **Functions**: 29
- **File**: `cli.py`

### rebuild.application.services.parallel_test_engine
- **Functions**: 25
- **Classes**: 3
- **File**: `parallel_test_engine.py`

### rebuild.application.services.deploy_service
- **Functions**: 24
- **Classes**: 1
- **File**: `deploy_service.py`

### rebuild.application.services.accelerator_deploy
- **Functions**: 23
- **Classes**: 1
- **File**: `accelerator_deploy.py`

### rebuild.application.services.db_snapshot_manager
- **Functions**: 22
- **Classes**: 2
- **File**: `db_snapshot_manager.py`

### rebuild.analysis.duplication_engine
- **Functions**: 20
- **Classes**: 3
- **File**: `duplication_engine.py`

### rebuild.application.accelerated_pipeline
- **Functions**: 19
- **Classes**: 1
- **File**: `accelerated_pipeline.py`

### rebuild.application.services.scanner_service
- **Functions**: 19
- **Classes**: 1
- **File**: `scanner_service.py`

### rebuild.analysis.service_graph
- **Functions**: 17
- **Classes**: 6
- **File**: `service_graph.py`

### rebuild.application.services.reporting.reporter
- **Functions**: 16
- **Classes**: 1
- **File**: `reporter.py`

### rebuild.application.services.notification_service
- **Functions**: 14
- **Classes**: 4
- **File**: `notification_service.py`

### rebuild.plugins.registry
- **Functions**: 14
- **Classes**: 1
- **File**: `registry.py`

### rebuild.domain.mvp_protocol
- **Functions**: 14
- **Classes**: 4
- **File**: `mvp_protocol.py`

### rebuild.infrastructure.config_loader
- **Functions**: 13
- **Classes**: 1
- **File**: `config_loader.py`

### rebuild.domain.dsl
- **Functions**: 13
- **Classes**: 5
- **File**: `dsl.py`

### rebuild.infrastructure.event_bus
- **Functions**: 12
- **Classes**: 1
- **File**: `event_bus.py`

### rebuild.application.pipeline
- **Functions**: 12
- **Classes**: 1
- **File**: `pipeline.py`

### rebuild.analysis.vector_search
- **Functions**: 11
- **Classes**: 2
- **File**: `vector_search.py`

### rebuild.application.services.smart_test_selector
- **Functions**: 11
- **Classes**: 3
- **File**: `smart_test_selector.py`

### rebuild.interfaces.commands.walk_command
- **Functions**: 11
- **File**: `walk_command.py`

## Key Entry Points

Main execution flows into the system:

### rebuild.interfaces.api.app.create_app
> Create and return a FastAPI application.

All dependencies are injected — ideal for testing.
- **Calls**: FastAPI, app.add_middleware, app.post, app.post, app.post, app.post, app.post, app.post

### rebuild.application.services.history_service.HistoryService.load_history
- **Calls**: sorted, results_dir.exists, results_dir.iterdir, self._load_commit, json.loads, isinstance, DayResult, all_results.append

### rebuild.interfaces.cli.walk
> Przejdź historię git dzień po dniu, deployuj i testuj endpointy.
- **Calls**: app.command, typer.Argument, typer.Option, typer.Option, typer.Option, typer.Option, typer.Option, typer.Option

### rebuild.application.accelerated_pipeline.AcceleratedPipeline.run
> Run accelerated analysis over commit history.
- **Calls**: self.git.days_with_commits, self._emit, self.log, self.log, self.log, self._prewarm_worktrees, self.worktrees.get_active_path, self.deploy.prepare_runtime

### rebuild.application.pipeline.Pipeline.run
- **Calls**: self.git.days_with_commits, self._event_service.enable, self._emit, self.log, self._emit, self.reporter.save_timeline_index, self.log, self.log

### rebuild.interfaces.cli.dsl
> Wykonaj DSL (Domain Specific Language) komendy rebuild.
- **Calls**: app.command, typer.Option, typer.Option, typer.Option, DSLParser, DSLInterpreter, console.print, typer.Exit

### rebuild.infrastructure.config_schema.ProjectConfig._validate_deploy_and_output
- **Calls**: model_validator, isinstance, isinstance, isinstance, ValueError, ValueError, OutputConfig.model_validate, isinstance

### rebuild.application.services.reporting.reporter.ReporterService.save_timeline_index
- **Calls**: output_dir.mkdir, sorted, self._health_trend_by_day, self._endpoint_count_trend_by_day, self._results_to_export_data, None.write_text, rebuild.application.services.reporting.chart_builder.generate_trend_chart, rebuild.application.services.reporting.chart_builder.generate_endpoint_diff

### rebuild.domain.mvp_protocol.MVPServer.start
> Start the MVP server.
- **Calls**: socketserver.TCPServer, Makefile.print, httpd.serve_forever, int, None.decode, self.headers.get, MVPMessage.from_json, server.handler.handle_message

### rebuild.analysis.duplication_engine.DuplicationEngine.scan
- **Calls**: self.collect_fragments, exact_matches.items, fuzzy_matches.items, self._find_semantic_groups, groups.extend, sorted, None.append, id

### rebuild.interfaces.cli.plugins
> Wylistuj zainstalowane pluginy (scanners, reporters).
- **Calls**: app.command, typer.Option, rebuild.plugins.registry.load_plugins, Table, table.add_column, table.add_column, table.add_column, table.add_column

### rebuild.interfaces.cli.accelerator
> ⚡ Ultra-szybki tryb 10x - worktree + hot reload + parallel testing.
- **Calls**: app.command, typer.Argument, typer.Option, typer.Option, typer.Option, typer.Option, typer.Option, typer.Option

### scripts.bump_version.main
- **Calls**: argparse.ArgumentParser, parser.add_argument, parser.add_argument, parser.add_argument, parser.parse_args, scripts.bump_version.read_version, scripts.bump_version.bump, Makefile.print

### rebuild.infrastructure.event_bus.EventBus.publish
> Publish event — dispatch to all registered handlers.
- **Calls**: self._sync_handlers.get, set, list, type, asyncio.get_running_loop, self._async_handlers.get, self._event_store.append, handler

### rebuild.application.services.restore_service.RestoreService.extract_endpoint
- **Calls**: target.mkdir, docker_dir.mkdir, self._find_backend_files, self._write_readme, self.console.print, src.exists, df.exists, backend_dir.mkdir

### rebuild.domain.dsl_v2.NLPMapper.to_dsl
> Convert natural language text to a DSL string.
- **Calls**: None.lower, None.strip, pat.search, working.split, self._llm_fallback, text.strip, re.compile, re.compile

### rebuild.analysis.service_similarity.ServiceSimilarityAnalyzer.analyze_directory
- **Calls**: services_dir.glob, list, range, sorted, services_data.keys, len, range, ast.parse

### rebuild.application.accelerated_pipeline.AcceleratedPipeline._run_day_fast
> Execute single day analysis with maximum speed.
- **Calls**: time.perf_counter, self.log, self._make_fast_day_result, str, self._switch_fast_day_commit, self._apply_fast_overrides, self._changed_modules_for_fast_day, self._populate_fast_endpoints

### rebuild.application.pipeline.Pipeline.run_day
- **Calls**: self.log, time.perf_counter, self._make_day_result, getattr, str, self._prepare_day_repo, self._deploy_day, self._save_if_deploy_failed

### rebuild.domain.dsl.DSLParser.parse
> Parse a DSL string into a DSLCommand.
- **Calls**: None.split, None.lower, DSLCommand, ValueError, Command, dsl_string.strip, command_str.replace, ValueError

### rebuild.analysis.duplication_engine.DuplicationEngine._extract_regex_fragments
> Fallback structural extraction for JS/TS using regex.
Identifies blocks between braces and normalizes them.
- **Calls**: file_path.read_text, re.finditer, match.group, match.start, range, len, frag_content.splitlines, len

### rebuild.application.accelerated_pipeline.AcceleratedPipeline._prewarm_worktrees
> Pre-create worktrees for all commits to avoid delays during execution.
- **Calls**: self.log, time.perf_counter, self.log, self.worktrees.get_or_create, min, ThreadPoolExecutor, as_completed, time.perf_counter

### rebuild.application.services.reporting.reporter.ReporterService.export_csv
> Write summary.csv with one row per day.
- **Calls**: output_dir.mkdir, sorted, self._health_trend_by_day, self._endpoint_count_trend_by_day, io.StringIO, csv.writer, writer.writerow, dest.write_text

### rebuild.interfaces.cli.restore
> Przywróć działający endpoint jako izolowany projekt.
- **Calls**: app.command, typer.Argument, typer.Argument, typer.Option, typer.Option, RestoreService, restore_svc.find_last_working_day, console.print

### rebuild.domain.dsl_v2.DSLParser.parse_tokens
> Return (command_name, raw_kwargs_dict).
- **Calls**: None.lower, shlex.split, DSLParseError, DSLParseError, dsl_string.strip, DSLParseError, token.partition, _ALIAS_MAP.get

### rebuild.analysis.service_graph.MultiRepoAnalyzer._repo_aliases
- **Calls**: self.repos.items, pyproject.exists, repo.iterdir, pyproject.read_text, content.splitlines, line.strip, item.is_dir, None.exists

### rebuild.analysis.service_graph.MultiRepoAnalyzer._analyze_shared_clones
- **Calls**: DuplicationEngine, self.repos.items, by_hash.items, groups.sort, self._iter_fragment_files, groups.append, len, CrossRepoCloneGroup

### rebuild.application.services.parallel_test_engine.ParallelTestEngine._test_single
> Test a single endpoint.
- **Calls**: time.perf_counter, EndpointResult, endpoint.method.upper, isinstance, time.perf_counter, EndpointResult, EndpointResult, client.get

### rebuild.application.services.reporting.reporter.ReporterService._results_to_export_data
- **Calls**: sorted, self._health_trend_by_day, self._endpoint_count_trend_by_day, str, trend_by_day.get, None.startswith, endpoint_trend_by_day.get, None.startswith

### rebuild.interfaces.cli.auto_pr
> Utwórz Pull/Merge Request z AI-generated summary z wyników analizy.
- **Calls**: app.command, typer.Argument, typer.Option, typer.Option, typer.Option, typer.Option, typer.Option, typer.Option

## Process Flows

Key execution flows identified:

### Flow 1: create_app
```
create_app [rebuild.interfaces.api.app]
```

### Flow 2: load_history
```
load_history [rebuild.application.services.history_service.HistoryService]
```

### Flow 3: walk
```
walk [rebuild.interfaces.cli]
```

### Flow 4: run
```
run [rebuild.application.accelerated_pipeline.AcceleratedPipeline]
```

### Flow 5: dsl
```
dsl [rebuild.interfaces.cli]
```

### Flow 6: _validate_deploy_and_output
```
_validate_deploy_and_output [rebuild.infrastructure.config_schema.ProjectConfig]
```

### Flow 7: save_timeline_index
```
save_timeline_index [rebuild.application.services.reporting.reporter.ReporterService]
```

### Flow 8: start
```
start [rebuild.domain.mvp_protocol.MVPServer]
  └─ →> print
```

### Flow 9: scan
```
scan [rebuild.analysis.duplication_engine.DuplicationEngine]
```

### Flow 10: plugins
```
plugins [rebuild.interfaces.cli]
  └─ →> load_plugins
```

## Key Classes

### rebuild.application.services.deploy_service.DeployService
> Service for managing the lifecycle of the service being analyzed.
Supports 'Replay Mode' (Invariant 
- **Methods**: 24
- **Key Methods**: rebuild.application.services.deploy_service.DeployService.__init__, rebuild.application.services.deploy_service.DeployService.detect_deploy_method, rebuild.application.services.deploy_service.DeployService.start, rebuild.application.services.deploy_service.DeployService.execute, rebuild.application.services.deploy_service.DeployService.wait_healthy, rebuild.application.services.deploy_service.DeployService.reload, rebuild.application.services.deploy_service.DeployService.stop, rebuild.application.services.deploy_service.DeployService._compose_file, rebuild.application.services.deploy_service.DeployService._compose_up, rebuild.application.services.deploy_service.DeployService._compose_down
- **Inherits**: <ast.Subscript object at 0x7f3eb1697290>

### rebuild.application.services.accelerator_deploy.AcceleratorDeployService
> 10x faster deployment using:
1. Git worktrees (instant code checkout)
2. Bind volume mounts (no cont
- **Methods**: 23
- **Key Methods**: rebuild.application.services.accelerator_deploy.AcceleratorDeployService.__init__, rebuild.application.services.accelerator_deploy.AcceleratorDeployService.start, rebuild.application.services.accelerator_deploy.AcceleratorDeployService.prepare_runtime, rebuild.application.services.accelerator_deploy.AcceleratorDeployService._accelerated_compose_up, rebuild.application.services.accelerator_deploy.AcceleratorDeployService.switch_commit, rebuild.application.services.accelerator_deploy.AcceleratorDeployService._update_bind_mount, rebuild.application.services.accelerator_deploy.AcceleratorDeployService._sync_code_to_container, rebuild.application.services.accelerator_deploy.AcceleratorDeployService._get_changed_files, rebuild.application.services.accelerator_deploy.AcceleratorDeployService._copy_changed_files, rebuild.application.services.accelerator_deploy.AcceleratorDeployService._get_container_name
- **Inherits**: DeployService

### rebuild.application.services.db_snapshot_manager.DBSnapshotManager
> Manages database snapshots for instant state restore.

Instead of re-seeding DB for each test run:
1
- **Methods**: 22
- **Key Methods**: rebuild.application.services.db_snapshot_manager.DBSnapshotManager.__init__, rebuild.application.services.db_snapshot_manager.DBSnapshotManager._ensure_dirs, rebuild.application.services.db_snapshot_manager.DBSnapshotManager._load_metadata, rebuild.application.services.db_snapshot_manager.DBSnapshotManager._save_metadata, rebuild.application.services.db_snapshot_manager.DBSnapshotManager.create, rebuild.application.services.db_snapshot_manager.DBSnapshotManager._auto_prune, rebuild.application.services.db_snapshot_manager.DBSnapshotManager.prune_old, rebuild.application.services.db_snapshot_manager.DBSnapshotManager.stats, rebuild.application.services.db_snapshot_manager.DBSnapshotManager._postgres_dump, rebuild.application.services.db_snapshot_manager.DBSnapshotManager._mysql_dump
- **Inherits**: <ast.Subscript object at 0x71099f6bcfd0>

### rebuild.analysis.duplication_engine.DuplicationEngine
> Engine for detecting structural and semantic duplication in codebases.
Supports Python (AST) and JS/
- **Methods**: 20
- **Key Methods**: rebuild.analysis.duplication_engine.DuplicationEngine.__init__, rebuild.analysis.duplication_engine.DuplicationEngine.scan, rebuild.analysis.duplication_engine.DuplicationEngine.collect_fragments, rebuild.analysis.duplication_engine.DuplicationEngine._find_semantic_groups, rebuild.analysis.duplication_engine.DuplicationEngine._semantic_candidates, rebuild.analysis.duplication_engine.DuplicationEngine._encode_semantic_candidates, rebuild.analysis.duplication_engine.DuplicationEngine._semantic_duplicate_groups, rebuild.analysis.duplication_engine.DuplicationEngine._semantic_group_members, rebuild.analysis.duplication_engine.DuplicationEngine._build_semantic_group, rebuild.analysis.duplication_engine.DuplicationEngine._mark_semantic_group_seen

### rebuild.application.services.parallel_test_engine.ParallelTestEngine
> High-performance parallel test execution.

Features:
- Health-first: /health, /metrics run first, ab
- **Methods**: 20
- **Key Methods**: rebuild.application.services.parallel_test_engine.ParallelTestEngine.__init__, rebuild.application.services.parallel_test_engine.ParallelTestEngine.open_session, rebuild.application.services.parallel_test_engine.ParallelTestEngine._open_client, rebuild.application.services.parallel_test_engine.ParallelTestEngine.close_session, rebuild.application.services.parallel_test_engine.ParallelTestEngine._close_client, rebuild.application.services.parallel_test_engine.ParallelTestEngine.set_day_dir, rebuild.application.services.parallel_test_engine.ParallelTestEngine._setup_default_dependencies, rebuild.application.services.parallel_test_engine.ParallelTestEngine.execute, rebuild.application.services.parallel_test_engine.ParallelTestEngine._split_health_endpoints, rebuild.application.services.parallel_test_engine.ParallelTestEngine._run_health_phase

### rebuild.application.accelerated_pipeline.AcceleratedPipeline
> Ultra-fast pipeline using:
- Git worktrees (instant branch switching)
- Volume-mounted code (no cont
- **Methods**: 19
- **Key Methods**: rebuild.application.accelerated_pipeline.AcceleratedPipeline.__init__, rebuild.application.accelerated_pipeline.AcceleratedPipeline._save_state, rebuild.application.accelerated_pipeline.AcceleratedPipeline.run, rebuild.application.accelerated_pipeline.AcceleratedPipeline._prewarm_worktrees, rebuild.application.accelerated_pipeline.AcceleratedPipeline._create_baseline_snapshot, rebuild.application.accelerated_pipeline.AcceleratedPipeline._run_day_fast, rebuild.application.accelerated_pipeline.AcceleratedPipeline._make_fast_day_result, rebuild.application.accelerated_pipeline.AcceleratedPipeline._switch_fast_day_commit, rebuild.application.accelerated_pipeline.AcceleratedPipeline._apply_fast_overrides, rebuild.application.accelerated_pipeline.AcceleratedPipeline._changed_modules_for_fast_day
- **Inherits**: BasePipeline

### rebuild.application.services.scanner_service.ScannerService
> Service for discovering API endpoints in a repository.
- **Methods**: 19
- **Key Methods**: rebuild.application.services.scanner_service.ScannerService.__init__, rebuild.application.services.scanner_service.ScannerService.execute, rebuild.application.services.scanner_service.ScannerService._scan_via_deta, rebuild.application.services.scanner_service.ScannerService._scan_via_fastapi_routes, rebuild.application.services.scanner_service.ScannerService._iter_source_python_files, rebuild.application.services.scanner_service.ScannerService._parse_python_ast, rebuild.application.services.scanner_service.ScannerService._fastapi_endpoints_from_tree, rebuild.application.services.scanner_service.ScannerService._fastapi_endpoints_from_function, rebuild.application.services.scanner_service.ScannerService._endpoint_from_fastapi_decorator, rebuild.application.services.scanner_service.ScannerService._collect_router_prefixes
- **Inherits**: <ast.Subscript object at 0x7f3eb16271d0>

### rebuild.application.services.reporting.reporter.ReporterService
> Thin orchestrator: delegates to formatters, chart_builder, and saves files.
- **Methods**: 16
- **Key Methods**: rebuild.application.services.reporting.reporter.ReporterService.execute, rebuild.application.services.reporting.reporter.ReporterService.to_yaml, rebuild.application.services.reporting.reporter.ReporterService.to_toon, rebuild.application.services.reporting.reporter.ReporterService.save_day, rebuild.application.services.reporting.reporter.ReporterService._save_html_day, rebuild.application.services.reporting.reporter.ReporterService._endpoint_rows, rebuild.application.services.reporting.reporter.ReporterService._endpoint_row, rebuild.application.services.reporting.reporter.ReporterService._deploy_section, rebuild.application.services.reporting.reporter.ReporterService._deploy_log_html, rebuild.application.services.reporting.reporter.ReporterService._deploy_category_html
- **Inherits**: <ast.Subscript object at 0x7f3eb145db50>

### rebuild.infrastructure.config_loader.ConfigLoader
> Loader for rebuild.yaml configuration files.
Merges file configuration with CLI defaults.
- **Methods**: 13
- **Key Methods**: rebuild.infrastructure.config_loader.ConfigLoader.load, rebuild.infrastructure.config_loader.ConfigLoader.validate, rebuild.infrastructure.config_loader.ConfigLoader.apply_to_config, rebuild.infrastructure.config_loader.ConfigLoader._project_section, rebuild.infrastructure.config_loader.ConfigLoader._resolve_repo_path, rebuild.infrastructure.config_loader.ConfigLoader._apply_output, rebuild.infrastructure.config_loader.ConfigLoader._apply_basic_project_options, rebuild.infrastructure.config_loader.ConfigLoader._apply_deploy_options, rebuild.infrastructure.config_loader.ConfigLoader._apply_deploy_dict, rebuild.infrastructure.config_loader.ConfigLoader._apply_mapping_options

### rebuild.plugins.registry.PluginRegistry
> Central registry for rebuild plugins.

Usage::

    registry = PluginRegistry()
    registry.discove
- **Methods**: 13
- **Key Methods**: rebuild.plugins.registry.PluginRegistry.__init__, rebuild.plugins.registry.PluginRegistry.discover, rebuild.plugins.registry.PluginRegistry.register_scanner, rebuild.plugins.registry.PluginRegistry.register_reporter, rebuild.plugins.registry.PluginRegistry.unregister_scanner, rebuild.plugins.registry.PluginRegistry.unregister_reporter, rebuild.plugins.registry.PluginRegistry.scanners, rebuild.plugins.registry.PluginRegistry.reporters, rebuild.plugins.registry.PluginRegistry.get_scanner, rebuild.plugins.registry.PluginRegistry.get_reporter

### rebuild.analysis.service_graph.MultiRepoAnalyzer
> Analyze cross-repo dependencies and shared structural code clones.
- **Methods**: 12
- **Key Methods**: rebuild.analysis.service_graph.MultiRepoAnalyzer.__init__, rebuild.analysis.service_graph.MultiRepoAnalyzer.analyze, rebuild.analysis.service_graph.MultiRepoAnalyzer.export_json, rebuild.analysis.service_graph.MultiRepoAnalyzer._normalize_repo_keys, rebuild.analysis.service_graph.MultiRepoAnalyzer._repo_aliases, rebuild.analysis.service_graph.MultiRepoAnalyzer._analyze_dependencies, rebuild.analysis.service_graph.MultiRepoAnalyzer._import_roots, rebuild.analysis.service_graph.MultiRepoAnalyzer._analyze_shared_clones, rebuild.analysis.service_graph.MultiRepoAnalyzer._iter_python_files, rebuild.analysis.service_graph.MultiRepoAnalyzer._iter_fragment_files

### rebuild.application.pipeline.Pipeline
> Orchestrates the analysis process (Command).
Supports Incremental Walking, Event Sourcing, and Repla
- **Methods**: 12
- **Key Methods**: rebuild.application.pipeline.Pipeline.__init__, rebuild.application.pipeline.Pipeline._check_for_manual_fix, rebuild.application.pipeline.Pipeline.run, rebuild.application.pipeline.Pipeline.run_day, rebuild.application.pipeline.Pipeline._make_day_result, rebuild.application.pipeline.Pipeline._prepare_day_repo, rebuild.application.pipeline.Pipeline._checkout_commit_for_day, rebuild.application.pipeline.Pipeline._apply_accelerator_patches, rebuild.application.pipeline.Pipeline._apply_configured_overrides, rebuild.application.pipeline.Pipeline._deploy_day
- **Inherits**: BasePipeline

### rebuild.infrastructure.event_bus.EventBus
> Publish/subscribe event bus.

- Sync subscribers: called immediately on publish()
- Async subscriber
- **Methods**: 11
- **Key Methods**: rebuild.infrastructure.event_bus.EventBus.__init__, rebuild.infrastructure.event_bus.EventBus.subscribe, rebuild.infrastructure.event_bus.EventBus.subscribe_async, rebuild.infrastructure.event_bus.EventBus.subscribe_all, rebuild.infrastructure.event_bus.EventBus.subscribe_all_async, rebuild.infrastructure.event_bus.EventBus.unsubscribe, rebuild.infrastructure.event_bus.EventBus.create_ws_queue, rebuild.infrastructure.event_bus.EventBus.remove_ws_queue, rebuild.infrastructure.event_bus.EventBus.publish, rebuild.infrastructure.event_bus.EventBus.publish_many

### rebuild.analysis.vector_search.VectorSearchIndex
> SQLite-backed vector index for semantic lookup of code fragments.
- **Methods**: 11
- **Key Methods**: rebuild.analysis.vector_search.VectorSearchIndex.__init__, rebuild.analysis.vector_search.VectorSearchIndex._ensure_schema, rebuild.analysis.vector_search.VectorSearchIndex.build_from_path, rebuild.analysis.vector_search.VectorSearchIndex.upsert_fragments, rebuild.analysis.vector_search.VectorSearchIndex.query, rebuild.analysis.vector_search.VectorSearchIndex.count, rebuild.analysis.vector_search.VectorSearchIndex._load_rows, rebuild.analysis.vector_search.VectorSearchIndex._get_model, rebuild.analysis.vector_search.VectorSearchIndex._fragment_id, rebuild.analysis.vector_search.VectorSearchIndex._to_text

### rebuild.application.services.smart_test_selector.SmartTestSelector
> Selectively runs tests based on git diff analysis.

Instead of testing all endpoints for every commi
- **Methods**: 11
- **Key Methods**: rebuild.application.services.smart_test_selector.SmartTestSelector.__init__, rebuild.application.services.smart_test_selector.SmartTestSelector.analyze_changes, rebuild.application.services.smart_test_selector.SmartTestSelector.select_tests, rebuild.application.services.smart_test_selector.SmartTestSelector._critical_only_selection, rebuild.application.services.smart_test_selector.SmartTestSelector._affected_endpoint_patterns, rebuild.application.services.smart_test_selector.SmartTestSelector._requires_full_selection, rebuild.application.services.smart_test_selector.SmartTestSelector._select_affected_endpoints, rebuild.application.services.smart_test_selector.SmartTestSelector._path_matches, rebuild.application.services.smart_test_selector.SmartTestSelector.add_mapping, rebuild.application.services.smart_test_selector.SmartTestSelector.execute
- **Inherits**: <ast.Subscript object at 0x7f3eb17a3690>

### rebuild.application.services.notification_service.NotificationService
> Send webhook notifications on rebuild events.

Usage::

    svc = NotificationService()
    svc.add_
- **Methods**: 11
- **Key Methods**: rebuild.application.services.notification_service.NotificationService.__init__, rebuild.application.services.notification_service.NotificationService.add_webhook, rebuild.application.services.notification_service.NotificationService.remove_webhook, rebuild.application.services.notification_service.NotificationService.clear, rebuild.application.services.notification_service.NotificationService.hooks, rebuild.application.services.notification_service.NotificationService.notify, rebuild.application.services.notification_service.NotificationService.notify_deploy_fail, rebuild.application.services.notification_service.NotificationService.notify_health_regression, rebuild.application.services.notification_service.NotificationService.notify_walk_complete, rebuild.application.services.notification_service.NotificationService._build_body

### rebuild.application.services.git_service.GitService
> Service for interacting with Git repositories and history.
Uses ShellAdapter for all git commands.
- **Methods**: 10
- **Key Methods**: rebuild.application.services.git_service.GitService.__init__, rebuild.application.services.git_service.GitService.execute, rebuild.application.services.git_service.GitService.days_with_commits, rebuild.application.services.git_service.GitService.get_current_sha, rebuild.application.services.git_service.GitService.clone_for_walk, rebuild.application.services.git_service.GitService.sync_current_state, rebuild.application.services.git_service.GitService.checkout, rebuild.application.services.git_service.GitService.restore_head, rebuild.application.services.git_service.GitService.diff_names, rebuild.application.services.git_service.GitService._run_git
- **Inherits**: <ast.Subscript object at 0x71099f92f710>

### rebuild.application.services.worktree_manager.WorktreeManager
> Manages git worktrees for ultra-fast branch/commit switching.

Instead of 'git checkout' which modif
- **Methods**: 10
- **Key Methods**: rebuild.application.services.worktree_manager.WorktreeManager.__init__, rebuild.application.services.worktree_manager.WorktreeManager._ensure_base_dir, rebuild.application.services.worktree_manager.WorktreeManager._worktree_path, rebuild.application.services.worktree_manager.WorktreeManager.get_or_create, rebuild.application.services.worktree_manager.WorktreeManager._list_worktrees, rebuild.application.services.worktree_manager.WorktreeManager._remove_worktree, rebuild.application.services.worktree_manager.WorktreeManager.cleanup_all, rebuild.application.services.worktree_manager.WorktreeManager.prepare_sequence, rebuild.application.services.worktree_manager.WorktreeManager.get_active_path, rebuild.application.services.worktree_manager.WorktreeManager.execute
- **Inherits**: <ast.Subscript object at 0x71099f76f850>

### rebuild.domain.mvp_protocol.MVPProtocolHandler
> Handler for MVP protocol communication.
- **Methods**: 10
- **Key Methods**: rebuild.domain.mvp_protocol.MVPProtocolHandler.__init__, rebuild.domain.mvp_protocol.MVPProtocolHandler.handle_message, rebuild.domain.mvp_protocol.MVPProtocolHandler._handle_command, rebuild.domain.mvp_protocol.MVPProtocolHandler._handle_event, rebuild.domain.mvp_protocol.MVPProtocolHandler._handle_walk, rebuild.domain.mvp_protocol.MVPProtocolHandler._handle_analyze, rebuild.domain.mvp_protocol.MVPProtocolHandler._handle_evolution, rebuild.domain.mvp_protocol.MVPProtocolHandler._handle_auto_pr, rebuild.domain.mvp_protocol.MVPProtocolHandler._handle_dsl, rebuild.domain.mvp_protocol.MVPProtocolHandler._handle_nlp

### rebuild.domain.dsl.DSLInterpreter
> Interpreter for executing parsed DSL commands.
- **Methods**: 10
- **Key Methods**: rebuild.domain.dsl.DSLInterpreter.__init__, rebuild.domain.dsl.DSLInterpreter.execute, rebuild.domain.dsl.DSLInterpreter.execute_file, rebuild.domain.dsl.DSLInterpreter._handle_walk, rebuild.domain.dsl.DSLInterpreter._handle_analyze, rebuild.domain.dsl.DSLInterpreter._handle_evolution, rebuild.domain.dsl.DSLInterpreter._handle_auto_pr, rebuild.domain.dsl.DSLInterpreter._handle_accelerator, rebuild.domain.dsl.DSLInterpreter._handle_restore, rebuild.domain.dsl.DSLInterpreter._handle_serve

## Data Transformation Functions

Key functions that process and transform data:

### rebuild.infrastructure.config_schema.ProjectConfig._validate_deploy_and_output
- **Output to**: model_validator, isinstance, isinstance, isinstance, ValueError

### rebuild.infrastructure.config_schema.ConfigSchemaValidator.validate
- **Output to**: isinstance, RebuildConfig.model_validate, exc.errors, None.replace, errors.append

### rebuild.infrastructure.config_schema.ConfigSchemaValidator.parse
> Parse and return a RebuildConfig, raising ValidationError on failure.
- **Output to**: RebuildConfig.model_validate

### rebuild.infrastructure.config_schema.load_and_validate
> Load a YAML file and validate against RebuildConfig schema.

Returns:
    (RebuildConfig, [])       
- **Output to**: ConfigSchemaValidator.validate, path.exists, isinstance, ConfigSchemaValidator.parse, open

### rebuild.infrastructure.config_loader.ConfigLoader.validate
> Validates rebuild.yaml data and returns a list of human-readable error strings.
An empty list means 
- **Output to**: ConfigSchemaValidator.validate

### rebuild.analysis.duplication_engine.DuplicationEngine._encode_semantic_candidates
- **Output to**: self._semantic_text, encoder.encode

### rebuild.analysis.duplication_engine.DuplicationEngine._get_semantic_encoder
- **Output to**: SentenceTransformer

### rebuild.application.commands.analyze_commands.AnalyzeCommand._validate_type
- **Output to**: field_validator, ValueError, sorted

### rebuild.application.commands.walk_commands.WalkCommand._validate_deploy
- **Output to**: field_validator, ValueError, sorted

### rebuild.application.commands.walk_commands.WalkCommand._validate_repo
- **Output to**: field_validator, Path, p.exists, ValueError, None.exists

### rebuild.application.services.summary_service.SummaryService.format_suggestions_for_pr
> Format suggestions for PR body.
- **Output to**: formatted.append, suggestion.severity.upper

### rebuild.application.services.nlp_service.NLPService.parse
> Parse natural language command into structured command.
- **Output to**: None.strip, self._detect_intent, self._extract_parameters, NLPCommand, text.lower

### rebuild.application.services.scanner_service.ScannerService._parse_python_ast
- **Output to**: ast.parse, py_file.read_text

### rebuild.application.services.scanner_service.ScannerService._parse_openapi
- **Output to**: spec.get, paths.items, self._substitute_params, methods.items, method.upper

### rebuild.interfaces.commands.walk_command._parse_date
- **Output to**: date.fromisoformat

### rebuild.domain.dsl.DSLParser.parse
> Parse a DSL string into a DSLCommand.
- **Output to**: None.split, None.lower, DSLCommand, ValueError, Command

### rebuild.domain.dsl.DSLParser.parse_file
> Parse a DSL file with multiple commands.
- **Output to**: dsl_file.read_text, None.split, line.strip, content.strip, commands.append

### rebuild.domain.dsl_v2.DSLParser.parse_tokens
> Return (command_name, raw_kwargs_dict).
- **Output to**: None.lower, shlex.split, DSLParseError, DSLParseError, dsl_string.strip

### rebuild.domain.dsl_v2.DSLParser.parse
> Parse and validate DSL string. Returns the matching Pydantic schema.
- **Output to**: self.parse_tokens, schema_cls, DSLParseError

### rebuild.domain.dsl_v2.DSLShell._process
> Process one line — parse, dispatch, print result.
- **Output to**: self._nlp.to_dsl, self._parser.to_cqrs_command, Makefile.print, Makefile.print, self._command_bus.dispatch

### rebuild.domain.dsl_v2.DSLShell.process_line
> Process one line programmatically (for testing). Returns command or None.
- **Output to**: self._nlp.to_dsl, self._parser.to_cqrs_command

## Behavioral Patterns

### recursion_to_yaml
- **Type**: recursion
- **Confidence**: 0.90
- **Functions**: rebuild.application.services.reporting.reporter.ReporterService.to_yaml

### recursion_to_toon
- **Type**: recursion
- **Confidence**: 0.90
- **Functions**: rebuild.application.services.reporting.reporter.ReporterService.to_toon

### recursion_to_yaml
- **Type**: recursion
- **Confidence**: 0.90
- **Functions**: rebuild.application.services.reporting.formatters.to_yaml

### state_machine_BasePipeline
- **Type**: state_machine
- **Confidence**: 0.70
- **Functions**: rebuild.application.base_pipeline.BasePipeline.__init__, rebuild.application.base_pipeline.BasePipeline._load_state, rebuild.application.base_pipeline.BasePipeline._save_state, rebuild.application.base_pipeline.BasePipeline._emit, rebuild.application.base_pipeline.BasePipeline.log

## Public API Surface

Functions exposed as public API (no underscore prefix):

- `rebuild.interfaces.api.app.create_app` - 74 calls
- `rebuild.interfaces.commands.analyze_command.multi_repo_command` - 44 calls
- `rebuild.application.services.history_service.HistoryService.load_history` - 37 calls
- `rebuild.interfaces.cli.walk` - 35 calls
- `rebuild.application.accelerated_pipeline.AcceleratedPipeline.run` - 33 calls
- `rebuild.application.pipeline.Pipeline.run` - 28 calls
- `rebuild.interfaces.commands.helpers.serve_reports` - 28 calls
- `rebuild.interfaces.cli.dsl` - 26 calls
- `rebuild.interfaces.commands.analyze_command.services_command` - 25 calls
- `rebuild.interfaces.commands.walk_command.accelerator_command` - 24 calls
- `rebuild.application.services.reporting.reporter.ReporterService.save_timeline_index` - 23 calls
- `rebuild.domain.mvp_protocol.MVPServer.start` - 23 calls
- `rebuild.analysis.duplication_engine.DuplicationEngine.scan` - 22 calls
- `rebuild.interfaces.cli.plugins` - 22 calls
- `rebuild.interfaces.cli.accelerator` - 21 calls
- `scripts.bump_version.main` - 20 calls
- `rebuild.infrastructure.event_bus.EventBus.publish` - 20 calls
- `rebuild.interfaces.commands.analyze_command.vector_query_command` - 20 calls
- `rebuild.interfaces.commands.helpers.print_summary_table` - 20 calls
- `rebuild.application.services.restore_service.RestoreService.extract_endpoint` - 19 calls
- `rebuild.interfaces.commands.refactor_command.plan_command` - 19 calls
- `rebuild.domain.dsl_v2.NLPMapper.to_dsl` - 19 calls
- `rebuild.analysis.service_similarity.ServiceSimilarityAnalyzer.analyze_directory` - 18 calls
- `rebuild.application.pipeline.Pipeline.run_day` - 18 calls
- `rebuild.domain.dsl.DSLParser.parse` - 18 calls
- `rebuild.application.services.reporting.reporter.ReporterService.export_csv` - 17 calls
- `rebuild.interfaces.cli.restore` - 17 calls
- `rebuild.interfaces.commands.analyze_command.truth_command` - 17 calls
- `rebuild.domain.dsl_v2.DSLParser.parse_tokens` - 17 calls
- `rebuild.interfaces.cli.auto_pr` - 16 calls
- `scripts.bump_version.categorize_commits` - 15 calls
- `rebuild.analysis.vector_search.VectorSearchIndex.upsert_fragments` - 15 calls
- `rebuild.application.services.summary_service.SummaryService.generate_from_duplication` - 15 calls
- `rebuild.application.services.summary_service.SummaryService.generate_from_service_graph` - 15 calls
- `scripts.bump_version.build_new_section` - 14 calls
- `scripts.bump_version.update_changelog` - 14 calls
- `rebuild.application.services.screenshot_service.ScreenshotService.execute` - 14 calls
- `rebuild.application.services.reporting.formatters.to_yaml` - 14 calls
- `rebuild.interfaces.cli.init` - 14 calls
- `rebuild.interfaces.cli.nlp` - 14 calls

## System Interactions

How components interact:

```mermaid
graph TD
    create_app --> FastAPI
    create_app --> add_middleware
    create_app --> post
    load_history --> sorted
    load_history --> exists
    load_history --> iterdir
    load_history --> _load_commit
    load_history --> loads
    walk --> command
    walk --> Argument
    walk --> Option
    run --> days_with_commits
    run --> _emit
    run --> log
    run --> enable
    dsl --> command
    dsl --> Option
    dsl --> DSLParser
    _validate_deploy_and --> model_validator
    _validate_deploy_and --> isinstance
    _validate_deploy_and --> ValueError
    save_timeline_index --> mkdir
    save_timeline_index --> sorted
    save_timeline_index --> _health_trend_by_day
    save_timeline_index --> _endpoint_count_tren
    save_timeline_index --> _results_to_export_d
    start --> TCPServer
    start --> print
    start --> serve_forever
    start --> int
```

## Reverse Engineering Guidelines

1. **Entry Points**: Start analysis from the entry points listed above
2. **Core Logic**: Focus on classes with many methods
3. **Data Flow**: Follow data transformation functions
4. **Process Flows**: Use the flow diagrams for execution paths
5. **API Surface**: Public API functions reveal the interface

## Context for LLM

Maintain the identified architectural patterns and public API surface when suggesting changes.