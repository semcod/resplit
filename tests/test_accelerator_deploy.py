from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

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
    svc.wait_healthy = MagicMock(return_value=True)
    svc._trigger_reload = MagicMock()
    svc._verify_runtime_commit = MagicMock(return_value=True)

    result = svc.switch_commit("deadbeefcafebabe", tmp_path)

    assert result is True
    svc._update_bind_mount.assert_not_called()
    svc._sync_code_to_container.assert_called_once_with(
        "backend", worktree_path, sha="deadbeefcafebabe", repo=tmp_path
    )
    svc._trigger_reload.assert_called_once_with("backend")
    svc.wait_healthy.assert_called_once_with(timeout=5.0, interval=1.0)
    svc._verify_runtime_commit.assert_called_once_with("backend", "deadbeefcafebabe")
    assert svc._current_sha == "deadbeefcafebabe"


def test_switch_commit_sets_current_sha_before_triggering_reload(tmp_path):
    worktrees = MagicMock()
    worktree_path = tmp_path / "worktrees" / "wt_feedface"
    worktrees.get_or_create.return_value = MagicMock(path=worktree_path)

    svc = AcceleratorDeployService(_config(tmp_path), worktrees)
    svc._sync_code_to_container = MagicMock(return_value=True)
    svc.wait_healthy = MagicMock(return_value=True)
    svc._verify_runtime_commit = MagicMock(return_value=True)

    seen = {}

    def _check_trigger(service: str):
        seen["service"] = service
        seen["sha"] = svc._current_sha

    svc._trigger_reload = _check_trigger

    result = svc.switch_commit("feedface12345678", tmp_path)

    assert result is True
    svc.wait_healthy.assert_called_once_with(timeout=5.0, interval=1.0)
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
    svc.wait_healthy = MagicMock(return_value=True)

    result = svc.start(tmp_path)

    assert result is True
    command = svc.shell.run.call_args.args[0]
    assert str(svc._runtime_compose_file) in command


def test_switch_commit_uses_short_health_gate_even_with_long_config_timeout(tmp_path):
    worktrees = MagicMock()
    worktree_path = tmp_path / "worktrees" / "wt_beaded"
    worktrees.get_or_create.return_value = MagicMock(path=worktree_path)

    config = _config(tmp_path)
    config.health_timeout = 30
    config.health_interval = 3

    svc = AcceleratorDeployService(config, worktrees)
    svc._sync_code_to_container = MagicMock(return_value=True)
    svc.wait_healthy = MagicMock(return_value=True)
    svc._trigger_reload = MagicMock()
    svc._verify_runtime_commit = MagicMock(return_value=True)

    result = svc.switch_commit("beaded0011223344", tmp_path)

    assert result is True
    svc.wait_healthy.assert_called_once_with(timeout=5.0, interval=1.0)


def test_switch_commit_skips_short_health_probe_when_recent_success_is_cached(tmp_path):
    worktrees = MagicMock()
    worktree_path = tmp_path / "worktrees" / "wt_c001d00d"
    worktrees.get_or_create.return_value = MagicMock(path=worktree_path)

    svc = AcceleratorDeployService(_config(tmp_path), worktrees)
    svc._sync_code_to_container = MagicMock(return_value=True)
    svc.wait_healthy = MagicMock(return_value=True)
    svc._trigger_reload = MagicMock()
    svc._verify_runtime_commit = MagicMock(return_value=True)
    svc._last_health_success_at = 100.0

    with patch("rebuild.application.services.accelerator_deploy.time.monotonic", return_value=101.0):
        result = svc.switch_commit("c001d00d12345678", tmp_path)

    assert result is True
    svc.wait_healthy.assert_not_called()
    svc._verify_runtime_commit.assert_called_once_with("backend", "c001d00d12345678")


def test_switch_commit_rechecks_health_when_cache_is_stale(tmp_path):
    worktrees = MagicMock()
    worktree_path = tmp_path / "worktrees" / "wt_fadedcab"
    worktrees.get_or_create.return_value = MagicMock(path=worktree_path)

    svc = AcceleratorDeployService(_config(tmp_path), worktrees)
    svc._sync_code_to_container = MagicMock(return_value=True)
    svc.wait_healthy = MagicMock(return_value=True)
    svc._trigger_reload = MagicMock()
    svc._verify_runtime_commit = MagicMock(return_value=True)
    svc._last_health_success_at = 100.0

    with patch("rebuild.application.services.accelerator_deploy.time.monotonic", side_effect=[103.5, 103.5]):
        result = svc.switch_commit("fadedcab12345678", tmp_path)

    assert result is True
    svc.wait_healthy.assert_called_once_with(timeout=5.0, interval=1.0)


def test_get_container_name_reuses_cached_container_lookup(tmp_path):
    worktrees = MagicMock()
    svc = AcceleratorDeployService(_config(tmp_path), worktrees)
    svc.shell.run = MagicMock(return_value=SimpleNamespace(returncode=0, stdout="running", stderr=""))

    first = svc._get_container_name("backend")
    second = svc._get_container_name("backend")

    assert first == "backend"
    assert second == "backend"
    svc.shell.run.assert_called_once_with(["docker", "inspect", "-f", "{{.State.Status}}", "backend"])


def test_get_container_name_caches_compose_ps_fallback_result(tmp_path):
    worktrees = MagicMock()
    svc = AcceleratorDeployService(_config(tmp_path), worktrees)
    svc.shell.run = MagicMock(
        side_effect=[
            SimpleNamespace(returncode=1, stdout="", stderr="missing"),
            SimpleNamespace(returncode=1, stdout="", stderr="missing"),
            SimpleNamespace(returncode=1, stdout="", stderr="missing"),
            SimpleNamespace(returncode=0, stdout="1234567890abcdef\n", stderr=""),
        ]
    )

    first = svc._get_container_name("backend")
    second = svc._get_container_name("backend")

    assert first == "1234567890ab"
    assert second == "1234567890ab"
    assert svc.shell.run.call_count == 4


def test_trigger_reload_caches_signal_strategy_after_first_success(tmp_path):
    worktrees = MagicMock()
    worktrees.get_active_path.return_value = tmp_path

    svc = AcceleratorDeployService(_config(tmp_path), worktrees)
    svc._current_sha = "deadbeefcafebabe"
    svc._get_container_name = MagicMock(return_value="backend")
    svc._send_hup_signal = MagicMock(return_value=SimpleNamespace(returncode=0))
    svc._send_exec_hup = MagicMock(return_value=SimpleNamespace(returncode=0))

    svc._trigger_reload("backend")
    svc._trigger_reload("backend")

    assert svc._reload_strategy_cache["backend"] == "signal"
    assert svc._send_hup_signal.call_count == 2
    svc._send_exec_hup.assert_not_called()


def test_sync_code_incremental_when_diff_is_small(tmp_path):
    worktrees = MagicMock()
    svc = AcceleratorDeployService(_config(tmp_path), worktrees)
    svc._current_sha = "prevsha0011223344"
    svc._get_container_name = MagicMock(return_value="mycontainer")
    svc._get_changed_files = MagicMock(return_value=["app.py", "utils/helpers.py"])
    svc._copy_changed_files = MagicMock(return_value=True)
    svc.shell.run = MagicMock()

    code_path = tmp_path / "wt_new"
    result = svc._sync_code_to_container(
        "backend", code_path, sha="newsha0011223344", repo=tmp_path
    )

    assert result is True
    svc._get_changed_files.assert_called_once_with(tmp_path, "prevsha0011223344", "newsha0011223344")
    svc._copy_changed_files.assert_called_once_with("mycontainer", code_path, ["app.py", "utils/helpers.py"])
    svc.shell.run.assert_not_called()  # full docker cp must NOT be invoked


def test_sync_code_falls_back_to_full_copy_when_diff_exceeds_threshold(tmp_path):
    from types import SimpleNamespace

    worktrees = MagicMock()
    svc = AcceleratorDeployService(_config(tmp_path), worktrees)
    svc._current_sha = "prevsha0011223344"
    svc._get_container_name = MagicMock(return_value="mycontainer")
    svc._get_changed_files = MagicMock(
        return_value=[f"file_{i}.py" for i in range(svc._INCREMENTAL_FILE_THRESHOLD + 1)]
    )
    svc._copy_changed_files = MagicMock(return_value=True)
    svc.shell.run = MagicMock(
        return_value=SimpleNamespace(returncode=0, stdout="", stderr="")
    )

    code_path = tmp_path / "wt_new"
    result = svc._sync_code_to_container(
        "backend", code_path, sha="newsha0011223344", repo=tmp_path
    )

    assert result is True
    svc._copy_changed_files.assert_not_called()
    cp_calls = [c.args[0] for c in svc.shell.run.call_args_list]
    assert any(c[0] == "docker" and c[1] == "cp" for c in cp_calls)


def test_trigger_reload_caches_exec_strategy_after_signal_failure(tmp_path):
    worktrees = MagicMock()
    worktrees.get_active_path.return_value = tmp_path

    svc = AcceleratorDeployService(_config(tmp_path), worktrees)
    svc._current_sha = "feedface12345678"
    svc._get_container_name = MagicMock(return_value="backend")
    svc._send_hup_signal = MagicMock(return_value=SimpleNamespace(returncode=1))
    svc._send_exec_hup = MagicMock(return_value=SimpleNamespace(returncode=0))

    svc._trigger_reload("backend")
    svc._trigger_reload("backend")

    assert svc._reload_strategy_cache["backend"] == "exec"
    svc._send_hup_signal.assert_called_once_with("backend")
    assert svc._send_exec_hup.call_count == 2