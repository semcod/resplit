from __future__ import annotations
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..domain.models import WalkConfig, DeployMethod
from .config_schema import ConfigSchemaValidator

_VALID_DEPLOY_METHODS = {m.value for m in DeployMethod}


class ConfigLoader:
    """
    Loader for rebuild.yaml configuration files.
    Merges file configuration with CLI defaults.
    """
    @staticmethod
    def load(path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def validate(yaml_data: Dict[str, Any]) -> List[str]:
        """
        Validates rebuild.yaml data and returns a list of human-readable error strings.
        An empty list means the config is valid.
        Uses pydantic-based ConfigSchemaValidator internally.
        """
        return ConfigSchemaValidator.validate(yaml_data)

    @staticmethod
    def apply_to_config(config: WalkConfig, yaml_data: Dict[str, Any]):
        """
        Updates WalkConfig instance with data from YAML.
        """
        project = yaml_data.get("project", {})
        if not project: # Support flat structure too
            project = yaml_data

        if "output" in project:
            out = project["output"]
            val = out["dir"] if isinstance(out, dict) and "dir" in out else out
            p = Path(val)
            if not p.is_absolute():
                p = (config.repo_path / p).resolve()
            config.output_dir = p
        if "days" in project:
            config.days = int(project["days"])
        if "deploy" in project:
            d = project["deploy"]
            if isinstance(d, dict):
                if "method" in d:
                    config.deploy_method = DeployMethod(d["method"])
                if "compose_file" in d:
                    config.compose_file = d["compose_file"]
                if "health_url" in d:
                    config.health_url = d["health_url"]
                if "health_timeout" in d:
                    config.health_timeout = int(d["health_timeout"])
                if "health_interval" in d:
                    config.health_interval = int(d["health_interval"])
                if "health_verbose" in d:
                    config.health_verbose = bool(d["health_verbose"])
                if "retry_attempts" in d:
                    config.deploy_retry_attempts = int(d["retry_attempts"])
                if "retry_backoff_seconds" in d:
                    config.deploy_retry_backoff_seconds = float(d["retry_backoff_seconds"])
                if "retry_backoff_multiplier" in d:
                    config.deploy_retry_backoff_multiplier = float(d["retry_backoff_multiplier"])
            else:
                config.deploy_method = DeployMethod(d)
        if "health_url" in project:
            config.health_url = project["health_url"]
        if "base_url" in project:
            config.base_url = project["base_url"]
        if "screenshots" in project:
            config.screenshots = bool(project["screenshots"])
        if "compose_file" in project:
            config.compose_file = project["compose_file"]
        
        # Fixtures
        if "test_fixtures" in yaml_data:
            config.test_fixtures.update(yaml_data["test_fixtures"])
        elif "fixtures" in project:
            config.test_fixtures.update(project["fixtures"])
            
        # Auth
        if "auth" in yaml_data:
            config.auth.update(yaml_data["auth"])
        elif "auth" in project:
            config.auth.update(project["auth"])

        # Login for token propagation
        if "login_url" in yaml_data:
            config.login_url = yaml_data["login_url"]
        elif "login_url" in project:
            config.login_url = project["login_url"]
        if "login_payload" in yaml_data and isinstance(yaml_data["login_payload"], dict):
            config.login_payload = yaml_data["login_payload"]
        elif "login_payload" in project and isinstance(project["login_payload"], dict):
            config.login_payload = project["login_payload"]

        # Per-endpoint request bodies
        if "test_bodies" in yaml_data and isinstance(yaml_data["test_bodies"], dict):
            config.test_bodies.update(yaml_data["test_bodies"])
        elif "test_bodies" in project and isinstance(project["test_bodies"], dict):
            config.test_bodies.update(project["test_bodies"])
            
        # Replay
        if "replay" in project:
            config.replay = bool(project["replay"])
        if "service" in project:
            config.app_service = project["service"]
        if "patch_dir" in project:
            p = Path(project["patch_dir"])
            if not p.is_absolute():
                p = (config.repo_path / p).resolve()
            config.patch_dir = p
