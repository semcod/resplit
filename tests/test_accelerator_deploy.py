from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import yaml

from rebuild.application.services.accelerator_deploy import AcceleratorDeployService
from rebuild.domain.models import DeployMethod, WalkConfig


def _config(tmp_path: Path) -> WalkConfig:
    return WalkConfig(
        repo_path=tmp_path,
        deploy_method=DeployMethod.DOCKER_COMPOSE,
        app_service="backend",
    )


def test_switch_commit_syncs_code_when_live_bind_swap_is_disabled(tmp_path):
    worktrees = MagicMock()
    worktree_path = tmp_path / "worktrees" / "wt_deadbeef"
    worktrees.get_or_create.return_value = MagicMock(path=worktree_path)

    svc = AcceleratorDeployService(_config(tmp_path), worktrees)
    svc._sync_code_to_container = MagicMock(return_value=True)
    svc._update_bind_mount = MagicMock(return_value=True)
    svc._wait_healthy = MagicMock(return_value=True)
    svc._trigger_reload = MagicMock()
    svc._verify_runtime_commit = MagicMock(return_value=True)

    result = svc.switch_commit("deadbeefcafebabe", tmp_path)

    assert result is True
    svc._update_bind_mount.assert_not_called()
    svc._sync_code_to_container.assert_called_once_with("backend", worktree_path)
    svc._trigger_reload.assert_called_once_with("backend")
    svc._verify_runtime_commit.assert_called_once_with("backend", "deadbeefcafebabe")
    assert svc._current_sha == "deadbeefcafebabe"


def test_switch_commit_sets_current_sha_before_triggering_reload(tmp_path):
    worktrees = MagicMock()
    worktree_path = tmp_path / "worktrees" / "wt_feedface"
    worktrees.get_or_create.return_value = MagicMock(path=worktree_path)

    svc = AcceleratorDeployService(_config(tmp_path), worktrees)
    svc._sync_code_to_container = MagicMock(return_value=True)
    svc._wait_healthy = MagicMock(return_value=True)
    svc._verify_runtime_commit = MagicMock(return_value=True)

    seen = {}

    def _check_trigger(service: str):
        seen["service"] = service
        seen["sha"] = svc._current_sha

    svc._trigger_reload = _check_trigger

    result = svc.switch_commit("feedface12345678", tmp_path)

    assert result is True
    svc._verify_runtime_commit.assert_called_once_with("backend", "feedface12345678")
    assert seen == {"service": "backend", "sha": "feedface12345678"}


def test_prepare_runtime_creates_runtime_compose_and_active_link(tmp_path):
    worktrees = MagicMock()
    worktrees.base_dir = tmp_path / "worktrees"

    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text(
        yaml.safe_dump(
            {
                "services": {
                    "backend": {
                        "image": "example/backend:latest",
                    }
                }
            }
        )
    )

    code_path = tmp_path / "worktrees" / "wt_first"
    code_path.mkdir(parents=True)

    svc = AcceleratorDeployService(_config(tmp_path), worktrees)

    prepared = svc.prepare_runtime(tmp_path, code_path)

    assert prepared is True
    assert svc._live_bind_swap_enabled is True
    assert svc._runtime_compose_file == tmp_path / "docker-compose.rebuild.yml"

    active_link = worktrees.base_dir / "active"
    assert active_link.is_symlink()
    assert active_link.resolve() == code_path.resolve()

    runtime_compose = yaml.safe_load(svc._runtime_compose_file.read_text())
    assert runtime_compose["services"]["backend"]["volumes"] == [f"{active_link}:/app:rw"]


def test_accelerated_compose_up_uses_runtime_compose_override(tmp_path):
    worktrees = MagicMock()
    worktrees.base_dir = tmp_path / "worktrees"

    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text(
        yaml.safe_dump(
            {
                "services": {
                    "backend": {
                        "image": "example/backend:latest",
                    }
                }
            }
        )
    )

    code_path = tmp_path / "worktrees" / "wt_first"
    code_path.mkdir(parents=True)

    svc = AcceleratorDeployService(_config(tmp_path), worktrees)
    svc.prepare_runtime(tmp_path, code_path)
    svc.shell.run = MagicMock(return_value=MagicMock(returncode=0, stderr=""))
    svc._wait_healthy = MagicMock(return_value=True)

    result = svc.start(tmp_path)

    assert result is True
    command = svc.shell.run.call_args.args[0]
    assert str(svc._runtime_compose_file) in command