"""
Pydantic-based schema for rebuild.yaml.

Provides:
  - RebuildConfig         — root model, mirrors rebuild.yaml structure
  - ConfigSchemaValidator — wraps pydantic validation into list[str] errors,
                            compatible with the existing ConfigLoader.validate() contract
  - load_and_validate     — convenience: load YAML file → RebuildConfig or list[str] errors
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError


# ─────────────────────────────────────────────────────────────────────────────
# Sub-models
# ─────────────────────────────────────────────────────────────────────────────

_VALID_DEPLOY_METHODS = {"none", "docker-compose", "auto", "custom"}


class DeployConfig(BaseModel):
    method: Optional[str] = None
    compose_file: Optional[str] = None
    health_url: Optional[str] = None
    health_timeout: Optional[int] = Field(default=None, ge=1)
    health_interval: Optional[int] = Field(default=None, ge=1)
    health_verbose: Optional[bool] = None
    retry_attempts: Optional[int] = Field(default=None, ge=1)
    retry_backoff_seconds: Optional[float] = Field(default=None, ge=0)
    retry_backoff_multiplier: Optional[float] = Field(default=None, ge=1.0)

    @field_validator("method")
    @classmethod
    def _valid_method(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _VALID_DEPLOY_METHODS:
            raise ValueError(
                f"invalid deploy method {v!r}; allowed: {sorted(_VALID_DEPLOY_METHODS)}"
            )
        return v


class OutputConfig(BaseModel):
    dir: str

    @field_validator("dir")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("output.dir must not be empty")
        return v


class AuthConfig(BaseModel):
    model_config = {"extra": "allow"}


class ProjectConfig(BaseModel):
    days: Optional[int] = Field(default=None, ge=1)
    output: Optional[Any] = None
    deploy: Optional[Any] = None
    health_url: Optional[str] = None
    base_url: Optional[str] = None
    screenshots: Optional[bool] = None
    compose_file: Optional[str] = None
    service: Optional[str] = None
    replay: Optional[bool] = None
    patch_dir: Optional[str] = None
    login_url: Optional[str] = None
    login_payload: Optional[Dict[str, Any]] = None
    fixtures: Optional[Dict[str, Any]] = None
    test_bodies: Optional[Dict[str, Any]] = None
    auth: Optional[Dict[str, Any]] = None

    @field_validator("screenshots", mode="before")
    @classmethod
    def _strict_bool(cls, v: Any) -> Any:
        if v is not None and not isinstance(v, bool):
            raise ValueError(f"must be true or false, got {v!r}")
        return v

    @model_validator(mode="after")
    def _validate_deploy_and_output(self) -> "ProjectConfig":
        if self.deploy is not None:
            d = self.deploy
            if isinstance(d, str):
                if d not in _VALID_DEPLOY_METHODS:
                    raise ValueError(
                        f"project.deploy: invalid value {d!r}; "
                        f"allowed: {sorted(_VALID_DEPLOY_METHODS)}"
                    )
            elif isinstance(d, dict):
                try:
                    self.deploy = DeployConfig.model_validate(d)
                except ValidationError as exc:
                    msgs = "; ".join(
                        f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}"
                        for e in exc.errors()
                    )
                    raise ValueError(f"project.deploy: {msgs}") from exc
            else:
                raise ValueError(
                    f"project.deploy: must be a string or mapping, got {type(d).__name__!r}"
                )
        if self.output is not None:
            o = self.output
            if isinstance(o, dict):
                try:
                    self.output = OutputConfig.model_validate(o)
                except ValidationError as exc:
                    msgs = "; ".join(
                        f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}"
                        for e in exc.errors()
                    )
                    raise ValueError(f"project.output: {msgs}") from exc
            elif not isinstance(o, str):
                raise ValueError(
                    f"project.output: must be a string or mapping with 'dir', got {type(o).__name__!r}"
                )
        return self


_REBUILD_ROOT_KEYS = frozenset(
    {"project", "auth", "test_fixtures", "test_bodies", "login_url", "login_payload"}
)


class RebuildConfig(BaseModel):
    """Root model for rebuild.yaml."""

    project: Optional[ProjectConfig] = None
    auth: Optional[Dict[str, Any]] = None
    test_fixtures: Optional[Any] = None
    test_bodies: Optional[Any] = None
    login_url: Optional[str] = None
    login_payload: Optional[Dict[str, Any]] = None

    model_config = {"extra": "allow"}

    @field_validator("test_fixtures", "test_bodies", mode="before")
    @classmethod
    def _must_be_mapping(cls, v: Any) -> Any:
        if v is not None and not isinstance(v, dict):
            raise ValueError(f"must be a mapping, got {type(v).__name__!r}")
        return v

    @model_validator(mode="before")
    @classmethod
    def _allow_flat(cls, values: Any) -> Any:
        if isinstance(values, dict) and "project" not in values:
            if not any(k in _REBUILD_ROOT_KEYS for k in values):
                return {"project": values}
        return values


# ─────────────────────────────────────────────────────────────────────────────
# Validator helper — compatible with ConfigLoader.validate() return type
# ─────────────────────────────────────────────────────────────────────────────

class ConfigSchemaValidator:
    """
    Drop-in pydantic-based replacement for ConfigLoader.validate().
    Returns list[str] — empty means valid.
    """

    @staticmethod
    def validate(yaml_data: Any) -> List[str]:
        if not isinstance(yaml_data, dict):
            return ["rebuild.yaml: root must be a YAML mapping"]
        try:
            RebuildConfig.model_validate(yaml_data)
            return []
        except ValidationError as exc:
            errors: List[str] = []
            for err in exc.errors():
                loc = ".".join(str(p) for p in err["loc"]) if err["loc"] else "config"
                msg = err["msg"].replace("Value error, ", "")
                errors.append(f"{loc}: {msg}")
            return errors

    @staticmethod
    def parse(yaml_data: Any) -> RebuildConfig:
        """Parse and return a RebuildConfig, raising ValidationError on failure."""
        return RebuildConfig.model_validate(yaml_data)


# ─────────────────────────────────────────────────────────────────────────────
# Convenience loader
# ─────────────────────────────────────────────────────────────────────────────

def load_and_validate(path: Path) -> tuple[Optional[RebuildConfig], List[str]]:
    """
    Load a YAML file and validate against RebuildConfig schema.

    Returns:
        (RebuildConfig, [])         on success
        (None, [error, ...])        on failure
    """
    if not path.exists():
        return None, [f"{path}: file not found"]
    try:
        with open(path) as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        return None, [f"{path}: YAML parse error — {exc}"]

    if not isinstance(raw, dict):
        return None, [f"{path}: root must be a YAML mapping"]

    errors = ConfigSchemaValidator.validate(raw)
    if errors:
        return None, errors

    return ConfigSchemaValidator.parse(raw), []
