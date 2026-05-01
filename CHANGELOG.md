# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.10] - 2026-05-01

### Docs
- Update CHANGELOG.md
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update docs/README.md
- Update docs/architecture.md
- Update project/README.md
- Update project/context.md

### Test
- Update tests/test_deploy_service.py
- Update tests/test_deployer.py
- Update tests/test_endpoint_scanner.py
- Update tests/test_git_service.py
- Update tests/test_git_walker.py
- Update tests/test_history_service.py
- Update tests/test_models.py
- Update tests/test_pipeline.py
- Update tests/test_reporter.py
- Update tests/test_reporter_service.py
- ... and 6 more files

### Other
- Update .rebuild_test/2026-05-01/commit.txt
- Update .rebuild_test/2026-05-01/endpoints.json
- Update .rebuild_test/2026-05-01/results.json
- Update .rebuild_test/index.html
- Update Makefile
- Update app.doql.less
- Update examples/01-dry-run-walk/.rebuild_dry/2026-05-01/commit.txt
- Update examples/01-dry-run-walk/.rebuild_dry/2026-05-01/endpoints.json
- Update examples/01-dry-run-walk/.rebuild_dry/2026-05-01/results.json
- Update examples/01-dry-run-walk/.rebuild_dry/index.html
- ... and 49 more files

## [0.1.10] - 2026-05-01

### Added
- **Intelligence Layer**: New `rebuild/analysis/` package for deep codebase insights.
- **Duplication Engine**: AST-based structural and semantic duplication detection.
- **Service Graph**: Visual architectural dependency mapping and cycle detection in CLI.
- **Truth Ranker**: Historical function quality ranking correlated with git and test results.
- **Refactor Recommender**: Automated generation of refactoring plans (Merge/Extract/Split).
- **New CLI Commands**: `rebuild analyze duplicates|services|truth` and `rebuild refactor plan`.

### Changed
- **Architectural Stabilization**: Transitioned to a strictly layered architecture (`CLI → Pipeline → Services → Infrastructure`).
- **Unified Service Interface**: All core logic migrated to standardized `Service` classes in `application/services/`.
- **Pipeline v2**: Refactored as a pure composer/orchestrator of injected services.
- **Thin CLI**: Stripped business logic from `interfaces/cli.py` to act as a routing layer.

### Removed
- Legacy monolithic modules: `git_walker.py`, `deployer.py`, `endpoint_scanner.py`, `tester.py`, `screenshotter.py`, `reporter.py`, `restorer.py`.

### Test
- Standardized test suite with 65 passing tests across all service layers.

## [0.1.9] - 2026-05-01
...
