from __future__ import annotations
import yaml
from pathlib import Path
from typing import Any, Dict, List

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
        project = ConfigLoader._project_section(yaml_data)
        ConfigLoader._apply_output(config, project)
        ConfigLoader._apply_basic_project_options(config, project)
        ConfigLoader._apply_deploy_options(config, project)
        ConfigLoader._apply_mapping_options(config, yaml_data, project)
        ConfigLoader._apply_login_options(config, yaml_data, project)
        ConfigLoader._apply_replay_options(config, project)
        ConfigLoader._apply_notifications(config, yaml_data, project)

    @staticmethod
    def _project_section(yaml_data: Dict[str, Any]) -> Dict[str, Any]:
        project = yaml_data.get("project", {})
        if not project: # Support flat structure too
            project = yaml_data
        return project

    @staticmethod
    def _resolve_repo_path(config: WalkConfig, value: Any) -> Path:
        path = Path(value)
        if not path.is_absolute():
            path = (config.repo_path / path).resolve()
        return path

    @staticmethod
    def _apply_output(config: WalkConfig, project: Dict[str, Any]) -> None:
        if "output" in project:
            out = project["output"]
            val = out["dir"] if isinstance(out, dict) and "dir" in out else out
            config.output_dir = ConfigLoader._resolve_repo_path(config, val)

    @staticmethod
    def _apply_basic_project_options(config: WalkConfig, project: Dict[str, Any]) -> None:
        if "days" in project:
            config.days = int(project["days"])
        if "health_url" in project:
            config.health_url = project["health_url"]
        if "base_url" in project:
            config.base_url = project["base_url"]
        if "screenshots" in project:
            config.screenshots = bool(project["screenshots"])
        if "compose_file" in project:
            config.compose_file = project["compose_file"]

    @staticmethod
    def _apply_deploy_options(config: WalkConfig, project: Dict[str, Any]) -> None:
        if "deploy" in project:
            d = project["deploy"]
            if isinstance(d, dict):
                ConfigLoader._apply_deploy_dict(config, d)
            else:
                config.deploy_method = DeployMethod(d)

    @staticmethod
    def _apply_deploy_dict(config: WalkConfig, deploy_data: Dict[str, Any]) -> None:
        fields = {
            "compose_file": ("compose_file", str),
            "health_url": ("health_url", str),
            "health_timeout": ("health_timeout", int),
            "health_interval": ("health_interval", int),
            "health_verbose": ("health_verbose", bool),
            "retry_attempts": ("deploy_retry_attempts", int),
            "retry_backoff_seconds": ("deploy_retry_backoff_seconds", float),
            "retry_backoff_multiplier": ("deploy_retry_backoff_multiplier", float),
        }
        if "method" in deploy_data:
            config.deploy_method = DeployMethod(deploy_data["method"])
        for key, (attr, caster) in fields.items():
            if key in deploy_data:
                setattr(config, attr, caster(deploy_data[key]))

    @staticmethod
    def _apply_mapping_options(
        config: WalkConfig, yaml_data: Dict[str, Any], project: Dict[str, Any]
    ) -> None:
        if "test_fixtures" in yaml_data:
            config.test_fixtures.update(yaml_data["test_fixtures"])
        elif "fixtures" in project:
            config.test_fixtures.update(project["fixtures"])

        if "auth" in yaml_data:
            config.auth.update(yaml_data["auth"])
        elif "auth" in project:
            config.auth.update(project["auth"])

        if "test_bodies" in yaml_data and isinstance(yaml_data["test_bodies"], dict):
            config.test_bodies.update(yaml_data["test_bodies"])
        elif "test_bodies" in project and isinstance(project["test_bodies"], dict):
            config.test_bodies.update(project["test_bodies"])

    @staticmethod
    def _apply_login_options(
        config: WalkConfig, yaml_data: Dict[str, Any], project: Dict[str, Any]
    ) -> None:
        if "login_url" in yaml_data:
            config.login_url = yaml_data["login_url"]
        elif "login_url" in project:
            config.login_url = project["login_url"]

        if "login_payload" in yaml_data and isinstance(yaml_data["login_payload"], dict):
            config.login_payload = yaml_data["login_payload"]
        elif "login_payload" in project and isinstance(project["login_payload"], dict):
            config.login_payload = project["login_payload"]

    @staticmethod
    def _apply_replay_options(config: WalkConfig, project: Dict[str, Any]) -> None:
        if "replay" in project:
            config.replay = bool(project["replay"])
        if "service" in project:
            config.app_service = project["service"]
        if "patch_dir" in project:
            config.patch_dir = ConfigLoader._resolve_repo_path(config, project["patch_dir"])

    @staticmethod
    def _apply_notifications(
        config: WalkConfig, yaml_data: Dict[str, Any], project: Dict[str, Any]
    ) -> None:
        if "notifications" in project and isinstance(project["notifications"], list):
            config.notifications = project["notifications"]
        elif "notifications" in yaml_data and isinstance(yaml_data["notifications"], list):
            config.notifications = yaml_data["notifications"]
