from __future__ import annotations
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..domain.models import WalkConfig, DeployMethod

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
        """
        errors: List[str] = []
        if not isinstance(yaml_data, dict):
            return ["rebuild.yaml: root must be a YAML mapping"]

        project = yaml_data.get("project", {})
        if not isinstance(project, dict):
            errors.append("project: must be a mapping")
            project = {}

        if "days" in project:
            v = project["days"]
            if not isinstance(v, int) or v < 1:
                errors.append(f"project.days: must be a positive integer, got {v!r}")

        if "output" in project:
            out = project["output"]
            if isinstance(out, dict):
                if "dir" not in out:
                    errors.append("project.output: mapping must contain 'dir' key")
                elif not isinstance(out["dir"], str):
                    errors.append(f"project.output.dir: must be a string, got {out['dir']!r}")
            elif not isinstance(out, str):
                errors.append(f"project.output: must be a string or mapping with 'dir', got {out!r}")

        if "deploy" in project:
            d = project["deploy"]
            if isinstance(d, dict):
                if "method" in d and d["method"] not in _VALID_DEPLOY_METHODS:
                    errors.append(
                        f"project.deploy.method: invalid value {d['method']!r}, "
                        f"allowed: {sorted(_VALID_DEPLOY_METHODS)}"
                    )
                for int_field in ("health_timeout", "health_interval", "retry_attempts"):
                    if int_field in d:
                        v = d[int_field]
                        if not isinstance(v, int) or v < 1:
                            errors.append(
                                f"project.deploy.{int_field}: must be a positive integer, got {v!r}"
                            )
                for float_field in ("retry_backoff_seconds", "retry_backoff_multiplier"):
                    if float_field in d:
                        v = d[float_field]
                        if not isinstance(v, (int, float)) or v < 0:
                            errors.append(
                                f"project.deploy.{float_field}: must be a non-negative number, got {v!r}"
                            )
                for url_field in ("health_url",):
                    if url_field in d and not isinstance(d[url_field], str):
                        errors.append(f"project.deploy.{url_field}: must be a string, got {d[url_field]!r}")
            elif not isinstance(d, str):
                errors.append(f"project.deploy: must be a string or mapping, got {d!r}")
            elif d not in _VALID_DEPLOY_METHODS:
                errors.append(
                    f"project.deploy: invalid value {d!r}, allowed: {sorted(_VALID_DEPLOY_METHODS)}"
                )

        for str_field in ("health_url", "base_url", "compose_file"):
            if str_field in project and not isinstance(project[str_field], str):
                errors.append(f"project.{str_field}: must be a string, got {project[str_field]!r}")

        if "screenshots" in project and not isinstance(project["screenshots"], bool):
            errors.append(f"project.screenshots: must be true or false, got {project['screenshots']!r}")

        if "auth" in yaml_data and not isinstance(yaml_data["auth"], dict):
            errors.append(f"auth: must be a mapping, got {yaml_data['auth']!r}")

        if "test_fixtures" in yaml_data and not isinstance(yaml_data["test_fixtures"], dict):
            errors.append(f"test_fixtures: must be a mapping, got {yaml_data['test_fixtures']!r}")

        if "test_bodies" in yaml_data and not isinstance(yaml_data["test_bodies"], dict):
            errors.append(f"test_bodies: must be a mapping, got {yaml_data['test_bodies']!r}")

        return errors

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
