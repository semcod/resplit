"""
Base pipeline: shared state, event emit, and common services.
"""
from __future__ import annotations

import json
from typing import List, Set

from ..domain.events import PipelineEvent  # Legacy for backward compatibility
from ..domain.models import WalkConfig

from .services.git_service import GitService
from .services.scanner_service import ScannerService
from .services.screenshot_service import ScreenshotService, ScreenshotConfig
from .services.reporter_service import ReporterService
from .services.patcher_service import PatcherService
from .services.override_service import OverrideService
from .services.event_service import get_event_service, EventType


class BasePipeline:
    """
    Shared infrastructure for Pipeline and AcceleratedPipeline.

    Provides:
    - Service initialization (git, scanner, screenshots, reporter, patcher, overrider)
    - Incremental state tracking (_processed_shas)
    - Event emission (_emit)
    - Console logging (log)
    """

    def __init__(self, config: WalkConfig, console=None):
        self.config = config
        self.console = console
        self._event_log: List[PipelineEvent] = []
        self._event_service = get_event_service()

        self.git = GitService(config.repo_path)
        self.scanner = ScannerService(config)
        self.screenshots = ScreenshotService(ScreenshotConfig(output_dir=config.output_dir))
        self.reporter = ReporterService()
        self.patcher = PatcherService()
        self.overrider = OverrideService()

        self._state_file = config.output_dir / "walk_state.json"
        self._processed_shas: Set[str] = self._load_state()

    # ── State ─────────────────────────────────────────────────────────────

    def _load_state(self) -> Set[str]:
        if self._state_file.exists():
            try:
                data = json.loads(self._state_file.read_text())
                return set(data.get("processed_shas", []))
            except Exception:
                pass
        return set()

    def _save_state(self) -> None:
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        self._state_file.write_text(
            json.dumps({"processed_shas": list(self._processed_shas)}, indent=2)
        )

    # ── Events ────────────────────────────────────────────────────────────

    def _emit(self, event_type: str, **kwargs) -> None:
        event = PipelineEvent.create(event_type, **kwargs)
        self._event_log.append(event)
        log_file = self.config.output_dir / "history.jsonl"
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        with open(log_file, "a") as f:
            f.write(event.to_json() + "\n")

        try:
            event_map = {
                "PIPELINE_STARTED": EventType.PIPELINE_START,
                "PIPELINE_FINISHED": EventType.PIPELINE_END,
                "DAY_STARTED": EventType.DAY_START,
                "DAY_FINISHED": EventType.DAY_END,
                "DEPLOY_STARTED": EventType.DEPLOY_START,
                "DEPLOY_SUCCESS": EventType.DEPLOY_SUCCESS,
                "DEPLOY_FAILED": EventType.DEPLOY_FAIL,
                "TEST_STARTED": EventType.TEST_START,
                "TEST_FINISHED": EventType.TEST_END,
                "HEALTH_CHECK": EventType.HEALTH_CHECK,
                "ERROR": EventType.ERROR,
                "LOG": EventType.LOG,
            }
            rt_type = event_map.get(event_type, EventType.LOG)
            self._event_service.emit(rt_type, kwargs, day=kwargs.get("day"), commit=kwargs.get("commit_sha"))
        except Exception:
            pass

    # ── Logging ───────────────────────────────────────────────────────────

    def log(self, message: str) -> None:
        if self.console:
            self.console.print(message)
