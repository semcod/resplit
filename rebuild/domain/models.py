from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Optional

class DeployMethod(Enum):
    AUTO = "auto"
    DOCKER_COMPOSE = "docker-compose"
    UVICORN = "uvicorn"
    NONE = "none"

@dataclass
class WalkConfig:
    repo_path: Path
    output_dir: Path = Path(".rebuild")
    days: int = 30
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    deploy_method: DeployMethod = DeployMethod.AUTO
    health_url: str = "http://localhost:8003/api/health"
    health_timeout: int = 60
    health_interval: int = 2
    base_url: str = "http://localhost:8003"
    screenshots: bool = True
    dry_run: bool = False
    compose_file: str = "docker-compose.yml"
    
    # Phase 12: Replay Engine
    replay: bool = False
    app_service: Optional[str] = None  # Docker service to restart (e.g. 'backend')
