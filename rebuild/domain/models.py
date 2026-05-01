from __future__ import annotations
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from datetime import date

class DeployMethod(str, Enum):
    DOCKER_COMPOSE = "docker-compose"
    UVICORN = "uvicorn"
    CUSTOM = "custom"
    NONE = "none"

@dataclass
class WalkConfig:
    repo_path: Path
    output_dir: Path = Path(".rebuild")
    days: int = 30
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    deploy_method: DeployMethod = DeployMethod.DOCKER_COMPOSE
    compose_file: str = "docker-compose.yml"
    health_url: str = "http://localhost:8003/api/health"
    health_timeout: int = 60
    health_interval: float = 2.0
    base_url: str = "http://localhost:8003"
    testql_dir: Optional[Path] = None
    screenshots: bool = True
    dry_run: bool = False
    earliest_commit_per_day: bool = True
