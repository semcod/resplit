from __future__ import annotations
import json
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

from ...domain.commit import CommitInfo
from ...domain.day_result import DayResult
from ...domain.endpoint import Endpoint, EndpointResult, EndpointStatus
from ...domain.models import DeployMethod
from .base import Service


class HistoryService(Service[Path, List[DayResult]]):
    """
    Service for loading and managing historical scan results from disk.
    """

    def execute(self, results_dir: Path) -> List[DayResult]:
        return self.load_history(results_dir)

    def load_history(self, results_dir: Path) -> List[DayResult]:
        if not results_dir.exists():
            return []

        all_results = []
        for day_dir in sorted(results_dir.iterdir()):
            rf = day_dir / "results.json"
            if not rf.exists():
                continue
            try:
                day_date = date.fromisoformat(day_dir.name)
            except ValueError:
                continue

            commit = self._load_commit(day_dir, day_date)
            raw = json.loads(rf.read_text())

            # Support both new dict format (to_dict()) and old list format
            if isinstance(raw, dict):
                ep_list = raw.get("results", [])
                if commit is None and raw.get("commit"):
                    c = raw["commit"]
                    commit = CommitInfo(
                        sha=c.get("sha", ""),
                        message=c.get("message", ""),
                        author=c.get("author", ""),
                        timestamp=datetime.fromisoformat(c["timestamp"])
                        if c.get("timestamp")
                        else datetime.now(),
                        date=day_date,
                    )
                deploy_success = raw.get("deploy", {}).get("success", True)
                is_dry_run = raw.get("deploy", {}).get("is_dry_run", False)
            else:
                ep_list = raw
                deploy_success = True
                is_dry_run = False

            endpoints = []
            ep_results = []
            for r in ep_list:
                ep = Endpoint(method=r["method"], path=r["path"], base_url=r.get("url", ""))
                endpoints.append(ep)
                ep_results.append(
                    EndpointResult(
                        endpoint=ep,
                        status=EndpointStatus(r["status"]),
                        http_status=r.get("http_status"),
                        response_time_ms=r.get("response_time_ms") or r.get("time_ms"),
                        screenshot_path=Path(r["screenshot"]) if r.get("screenshot") else None,
                        testql_passed=r.get("testql_passed"),
                        error=r.get("error"),
                    )
                )

            result = DayResult(
                day=day_date,
                commit=commit,
                deploy_method=DeployMethod.NONE,
                deploy_success=deploy_success,
                endpoints=endpoints,
                endpoint_results=ep_results,
                output_dir=day_dir,
                is_dry_run=is_dry_run,
            )
            all_results.append(result)

        return all_results

    def _load_commit(self, day_dir: Path, day_date: date) -> Optional[CommitInfo]:
        commit_file = day_dir / "commit.txt"
        if not commit_file.exists():
            return None

        lines = commit_file.read_text().splitlines()
        if not lines:
            return None

        return CommitInfo(
            sha=lines[0] if len(lines) > 0 else "",
            message=lines[1] if len(lines) > 1 else "",
            author=lines[2] if len(lines) > 2 else "",
            timestamp=datetime.fromisoformat(lines[3]) if len(lines) > 3 else datetime.now(),
            date=day_date,
        )
