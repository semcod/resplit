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
            data = json.loads(rf.read_text())
            
            endpoints = []
            ep_results = []
            for r in data:
                ep = Endpoint(method=r["method"], path=r["path"], base_url=r.get("url", ""))
                endpoints.append(ep)
                ep_results.append(EndpointResult(
                    endpoint=ep,
                    status=EndpointStatus(r["status"]),
                    http_status=r.get("http_status"),
                    response_time_ms=r.get("response_time_ms"),
                    screenshot_path=Path(r["screenshot"]) if r.get("screenshot") else None,
                    testql_passed=r.get("testql_passed"),
                    error=r.get("error"),
                ))
            
            result = DayResult(
                day=day_date,
                commit=commit,
                deploy_method=DeployMethod.NONE, # Unknown at load time
                deploy_success=True, # Assume true if results exist
                endpoints=endpoints,
                endpoint_results=ep_results,
                output_dir=day_dir,
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
