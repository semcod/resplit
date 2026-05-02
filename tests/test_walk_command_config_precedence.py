from __future__ import annotations

from pathlib import Path

from rich.console import Console

from rebuild.interfaces.commands import walk_command as walk_mod


class _CapturePipeline:
    captured_config = None

    def __init__(self, config, console=None):
        self.config = config
        _CapturePipeline.captured_config = config

    def run(self):
        return []


def _invoke_walk(repo: Path, *, health_timeout: int = 60, deploy: str = "none", cli_overrides=None):
    console = Console(record=True)
    walk_mod.walk_command(
        repo=repo,
        days=30,
        date_from=None,
        date_to=None,
        output=repo / "cli_output",
        deploy=deploy,
        replay=False,
        service=None,
        health_url="http://localhost:8003/api/health",
        base_url="http://localhost:8003",
        screenshots=True,
        dry_run=False,
        serve=False,
        port=7821,
        accelerator=False,
        patch_dir=None,
        console=console,
        health_timeout=health_timeout,
        cli_overrides=cli_overrides,
    )
    return _CapturePipeline.captured_config


def test_walk_cli_health_timeout_overrides_yaml_when_explicit(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "rebuild.yaml").write_text(
        "project:\n"
        "  deploy:\n"
        "    method: docker-compose\n"
        "    health_timeout: 15\n"
    )

    monkeypatch.setattr(walk_mod, "Pipeline", _CapturePipeline)

    cfg = _invoke_walk(
        repo,
        health_timeout=300,
        deploy="none",
        cli_overrides={"health_timeout": True, "deploy": True},
    )

    assert cfg.health_timeout == 300
    assert cfg.deploy_method.value == "none"


def test_walk_uses_yaml_when_option_not_explicit(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "rebuild.yaml").write_text(
        "project:\n"
        "  output: yaml_out\n"
        "  deploy:\n"
        "    method: docker-compose\n"
        "    health_timeout: 120\n"
    )

    monkeypatch.setattr(walk_mod, "Pipeline", _CapturePipeline)

    cfg = _invoke_walk(repo, health_timeout=60, deploy="none", cli_overrides={})

    assert cfg.health_timeout == 120
    assert cfg.deploy_method.value == "docker-compose"
    assert cfg.output_dir == (repo / "yaml_out").resolve()


def test_walk_cli_output_overrides_yaml_when_explicit(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "rebuild.yaml").write_text("project:\n  output: yaml_out\n")

    monkeypatch.setattr(walk_mod, "Pipeline", _CapturePipeline)

    cfg = _invoke_walk(repo, cli_overrides={"output": True})

    assert cfg.output_dir == (repo / "cli_output").resolve()
