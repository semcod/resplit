"""Coverage boost for Phase 16 — targets config_loader, helpers, walk_command, mvp_protocol."""
from __future__ import annotations

import csv
import io
from datetime import date, datetime
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rebuild.domain.day_result import DayResult
from rebuild.domain.endpoint import Endpoint, EndpointResult, EndpointStatus
from rebuild.domain.models import DeployMethod, WalkConfig
from rebuild.infrastructure.config_loader import ConfigLoader


# ─────────────────────────────────────────────
# ConfigLoader.apply_to_config – uncovered branches
# ─────────────────────────────────────────────

def test_apply_health_verbose(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path)
    ConfigLoader.apply_to_config(cfg, {"project": {"deploy": {"health_verbose": True}}})
    assert cfg.health_verbose is True


def test_apply_retry_backoff_multiplier(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path)
    ConfigLoader.apply_to_config(cfg, {"project": {"deploy": {"retry_backoff_multiplier": 2.0}}})
    assert cfg.deploy_retry_backoff_multiplier == 2.0


def test_apply_base_url(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path)
    ConfigLoader.apply_to_config(cfg, {"project": {"base_url": "http://example.com"}})
    assert cfg.base_url == "http://example.com"


def test_apply_screenshots_false(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path)
    ConfigLoader.apply_to_config(cfg, {"project": {"screenshots": False}})
    assert cfg.screenshots is False


def test_apply_compose_file_project(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path)
    ConfigLoader.apply_to_config(cfg, {"project": {"compose_file": "infra/compose.yml"}})
    assert cfg.compose_file == "infra/compose.yml"


def test_apply_fixtures_in_project(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path)
    ConfigLoader.apply_to_config(cfg, {"project": {"fixtures": {"uid": "1"}}})
    assert cfg.test_fixtures["uid"] == "1"


def test_apply_auth_in_project(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path)
    ConfigLoader.apply_to_config(cfg, {"project": {"auth": {"X-Key": "abc"}}})
    assert cfg.auth["X-Key"] == "abc"


def test_apply_login_url_in_project(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path)
    ConfigLoader.apply_to_config(cfg, {"project": {"login_url": "http://x/login"}})
    assert cfg.login_url == "http://x/login"


def test_apply_login_payload_in_project(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path)
    ConfigLoader.apply_to_config(cfg, {"project": {"login_payload": {"user": "a"}}})
    assert cfg.login_payload == {"user": "a"}


def test_apply_login_url_top_level(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path)
    ConfigLoader.apply_to_config(cfg, {"login_url": "http://top/login"})
    assert cfg.login_url == "http://top/login"


def test_apply_login_payload_top_level(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path)
    ConfigLoader.apply_to_config(cfg, {"login_payload": {"user": "b"}})
    assert cfg.login_payload == {"user": "b"}


def test_apply_test_bodies_in_project(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path)
    ConfigLoader.apply_to_config(cfg, {"project": {"test_bodies": {"POST /x": {"a": 1}}}})
    assert cfg.test_bodies["POST /x"] == {"a": 1}


def test_apply_replay_and_service(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path)
    ConfigLoader.apply_to_config(cfg, {"project": {"replay": True, "service": "backend"}})
    assert cfg.replay is True
    assert cfg.app_service == "backend"


def test_apply_patch_dir_relative(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path)
    ConfigLoader.apply_to_config(cfg, {"project": {"patch_dir": "patches"}})
    assert cfg.patch_dir == (tmp_path / "patches").resolve()


def test_apply_patch_dir_absolute(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path)
    abs_path = str(tmp_path / "abs_patches")
    ConfigLoader.apply_to_config(cfg, {"project": {"patch_dir": abs_path}})
    assert cfg.patch_dir == Path(abs_path)


def test_apply_output_absolute(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path)
    abs_out = str(tmp_path / "out")
    ConfigLoader.apply_to_config(cfg, {"project": {"output": abs_out}})
    assert cfg.output_dir == Path(abs_out)


def test_validate_valid_output_mapping(tmp_path):
    errors = ConfigLoader.validate({"project": {"output": {"dir": "out"}}})
    assert errors == []


def test_validate_invalid_output_dir_not_string():
    errors = ConfigLoader.validate({"project": {"output": {"dir": 42}}})
    assert any("output" in e for e in errors)


def test_validate_retry_backoff_negative():
    errors = ConfigLoader.validate({"project": {"deploy": {"retry_backoff_seconds": -1}}})
    assert any("retry_backoff_seconds" in e for e in errors)


def test_validate_health_url_not_string():
    errors = ConfigLoader.validate({"project": {"deploy": {"health_url": 123}}})
    assert any("health_url" in e for e in errors)


def test_validate_screenshots_not_bool():
    errors = ConfigLoader.validate({"project": {"screenshots": "yes"}})
    assert any("screenshots" in e for e in errors)


def test_validate_project_not_mapping():
    errors = ConfigLoader.validate({"project": "string"})
    assert any("project" in e for e in errors)


def test_validate_test_fixtures_not_mapping():
    errors = ConfigLoader.validate({"test_fixtures": "flat"})
    assert len(errors) >= 1


def test_validate_deploy_not_string_or_dict():
    errors = ConfigLoader.validate({"project": {"deploy": 42}})
    assert any("deploy" in e for e in errors)


def test_validate_base_url_not_string():
    errors = ConfigLoader.validate({"project": {"base_url": True}})
    assert any("base_url" in e for e in errors)


# ─────────────────────────────────────────────
# helpers — print_summary_table branches
# ─────────────────────────────────────────────

from rebuild.interfaces.commands.helpers import print_summary_table, compute_endpoint_count_trend_labels
from rich.console import Console


def _ep(path="/h"):
    return Endpoint(method="GET", path=path, base_url="http://x")


def _ok(ep):
    return EndpointResult(endpoint=ep, status=EndpointStatus.OK, http_status=200)


def _day(day_date, ep_count=5, ok_count=5, deploy=True, duration=1.0):
    ep = _ep()
    eps = [ep] * ep_count
    oks = [_ok(ep)] * ok_count
    fails = [EndpointResult(endpoint=ep, status=EndpointStatus.FAIL)] * (ep_count - ok_count)
    return DayResult(
        day=day_date,
        commit=None,
        deploy_method=DeployMethod.NONE,
        deploy_success=deploy,
        endpoints=eps,
        endpoint_results=oks + fails,
        duration_seconds=duration,
    )


def test_print_summary_table_with_regression(tmp_path):
    buf = StringIO()
    console = Console(file=buf, highlight=False)
    d1 = _day(date(2025, 1, 1), ep_count=5, ok_count=5)
    d2 = _day(date(2025, 1, 2), ep_count=5, ok_count=0)
    print_summary_table([d1, d2], console)
    out = buf.getvalue()
    assert "⚠" in out


def test_print_summary_table_with_positive_trend(tmp_path):
    buf = StringIO()
    console = Console(file=buf, highlight=False)
    d1 = _day(date(2025, 1, 1), ep_count=5, ok_count=0)
    d2 = _day(date(2025, 1, 2), ep_count=5, ok_count=5)
    print_summary_table([d1, d2], console)
    out = buf.getvalue()
    assert "+" in out


def test_print_summary_table_deploy_fail(tmp_path):
    buf = StringIO()
    console = Console(file=buf, highlight=False)
    d = _day(date(2025, 1, 1), deploy=False)
    print_summary_table([d], console)
    assert "✗" in buf.getvalue()


def test_compute_endpoint_count_no_change():
    ep = _ep()
    ok = _ok(ep)
    d1 = DayResult(day=date(2025,1,1), commit=None, deploy_method=DeployMethod.NONE,
                   deploy_success=True, endpoints=[ep]*5, endpoint_results=[ok]*5)
    d2 = DayResult(day=date(2025,1,2), commit=None, deploy_method=DeployMethod.NONE,
                   deploy_success=True, endpoints=[ep]*5, endpoint_results=[ok]*5)
    labels = compute_endpoint_count_trend_labels([d1, d2])
    assert labels[1] == "0"


def test_compute_endpoint_count_increase_small():
    ep = _ep()
    ok = _ok(ep)
    d1 = DayResult(day=date(2025,1,1), commit=None, deploy_method=DeployMethod.NONE,
                   deploy_success=True, endpoints=[ep]*10, endpoint_results=[ok]*10)
    d2 = DayResult(day=date(2025,1,2), commit=None, deploy_method=DeployMethod.NONE,
                   deploy_success=True, endpoints=[ep]*11, endpoint_results=[ok]*11)
    labels = compute_endpoint_count_trend_labels([d1, d2], warning_threshold_pct=10.0)
    assert not labels[1].startswith("⚠")
    assert "+" in labels[1]


def test_compute_endpoint_count_first_zero():
    ep = _ep()
    ok = _ok(ep)
    d1 = DayResult(day=date(2025,1,1), commit=None, deploy_method=DeployMethod.NONE,
                   deploy_success=True, endpoints=[], endpoint_results=[])
    d2 = DayResult(day=date(2025,1,2), commit=None, deploy_method=DeployMethod.NONE,
                   deploy_success=True, endpoints=[ep]*5, endpoint_results=[ok]*5)
    labels = compute_endpoint_count_trend_labels([d1, d2])
    assert labels[0] == "—"
    assert labels[1] == "—"


# ─────────────────────────────────────────────
# walk_command — CLI overrides branch coverage
# ─────────────────────────────────────────────

from rebuild.interfaces.commands.walk_command import walk_command
import click


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    return repo


def test_walk_command_no_git_repo_exits(tmp_path):
    repo = tmp_path / "norepo"
    repo.mkdir()
    buf = StringIO()
    console = Console(file=buf, highlight=False)
    with pytest.raises((click.exceptions.Exit, SystemExit)):
        walk_command(repo=repo, days=1, date_from=None, date_to=None,
                     output=tmp_path/"out", deploy="none", replay=False,
                     service=None, health_url="http://x/h", base_url="http://x",
                     screenshots=False, dry_run=True, serve=False, port=8080,
                     accelerator=False, patch_dir=None, console=console, health_timeout=10)


def test_walk_command_cli_overrides_applied(tmp_path):
    repo = _make_repo(tmp_path)
    (repo / "rebuild.yaml").write_text("project:\n  days: 99\n  output: .old_out\n")
    buf = StringIO()
    console = Console(file=buf, highlight=False)
    with patch("rebuild.interfaces.commands.walk_command.Pipeline") as MockPipeline:
        MockPipeline.return_value.run.return_value = []
        walk_command(
            repo=repo, days=3, date_from=None, date_to=None,
            output=tmp_path/"cli_out", deploy="none", replay=False,
            service=None, health_url="http://x/h", base_url="http://x",
            screenshots=False, dry_run=True, serve=False, port=8080,
            accelerator=False, patch_dir=None, console=console, health_timeout=10,
            cli_overrides={"days": True, "output": True},
        )
    cfg = MockPipeline.call_args[0][0]
    assert cfg.days == 3
    assert "cli_out" in str(cfg.output_dir)


def test_walk_command_no_yaml(tmp_path):
    repo = _make_repo(tmp_path)
    buf = StringIO()
    console = Console(file=buf, highlight=False)
    with patch("rebuild.interfaces.commands.walk_command.Pipeline") as MockPipeline:
        MockPipeline.return_value.run.return_value = []
        walk_command(repo=repo, days=1, date_from=None, date_to=None,
                     output=tmp_path/"out", deploy="none", replay=False,
                     service=None, health_url="http://x/h", base_url="http://x",
                     screenshots=False, dry_run=True, serve=False, port=8080,
                     accelerator=False, patch_dir=None, console=console, health_timeout=10)
    out = buf.getvalue()
    assert "Brak rebuild.yaml" in out


def test_walk_command_with_results_generates_exports(tmp_path):
    from rebuild.application.services.reporting import reporter as reporter_mod
    repo = _make_repo(tmp_path)
    ep = _ep()
    ok = _ok(ep)
    out_dir = tmp_path / "out"
    day_dir = out_dir / "2025-01-01"
    day_dir.mkdir(parents=True)
    fake_result = DayResult(
        day=date(2025, 1, 1), commit=None,
        deploy_method=DeployMethod.NONE, deploy_success=True,
        endpoints=[ep], endpoint_results=[ok],
        output_dir=day_dir,
    )
    buf = StringIO()
    console = Console(file=buf, highlight=False)
    mock_reporter = MagicMock()
    with patch("rebuild.interfaces.commands.walk_command.Pipeline") as MockPipeline, \
         patch.object(reporter_mod, "ReporterService", return_value=mock_reporter), \
         patch("rebuild.interfaces.commands.helpers.print_report_links"), \
         patch("rebuild.interfaces.commands.helpers.print_summary_table"):
        MockPipeline.return_value.run.return_value = [fake_result]
        walk_command(repo=repo, days=1, date_from=None, date_to=None,
                     output=out_dir, deploy="none", replay=False,
                     service=None, health_url="http://x/h", base_url="http://x",
                     screenshots=False, dry_run=True, serve=False, port=8080,
                     accelerator=False, patch_dir=None, console=console, health_timeout=10)
    mock_reporter.export_csv.assert_called_once()
    mock_reporter.export_markdown.assert_called_once()


# ─────────────────────────────────────────────
# mvp_protocol — uncovered branches
# ─────────────────────────────────────────────

from rebuild.domain.mvp_protocol import MVPMessage, MVPProtocolHandler, MessageType


def test_mvp_message_default_timestamp():
    msg = MVPMessage()
    assert msg.timestamp.endswith("Z")


def test_mvp_message_to_json_roundtrip():
    msg = MVPMessage(message_type=MessageType.COMMAND, payload={"command": "walk"})
    json_str = msg.to_json()
    decoded = MVPMessage.from_json(json_str)
    assert decoded.message_type == MessageType.COMMAND
    assert decoded.payload["command"] == "walk"


def test_mvp_handler_handle_event():
    handler = MVPProtocolHandler()
    msg = MVPMessage(message_type=MessageType.EVENT, payload={"event_type": "deploy_done"})
    response = handler.handle_message(msg)
    assert response.payload.get("status") == "event_received"


def test_mvp_handler_unknown_command():
    handler = MVPProtocolHandler()
    msg = MVPMessage(message_type=MessageType.COMMAND, payload={"command": "nonexistent"})
    response = handler.handle_message(msg)
    assert response.message_type == MessageType.ERROR


def test_mvp_handler_missing_command_key():
    handler = MVPProtocolHandler()
    msg = MVPMessage(message_type=MessageType.COMMAND, payload={})
    response = handler.handle_message(msg)
    assert response.message_type == MessageType.ERROR


def test_mvp_handler_walk_command():
    handler = MVPProtocolHandler()
    msg = MVPMessage(message_type=MessageType.COMMAND, payload={"command": "walk", "parameters": {"days": 5}})
    response = handler.handle_message(msg)
    assert response.message_type == MessageType.RESPONSE


def test_mvp_handler_analyze_command():
    handler = MVPProtocolHandler()
    msg = MVPMessage(message_type=MessageType.COMMAND, payload={"command": "analyze", "parameters": {}})
    response = handler.handle_message(msg)
    assert response.message_type == MessageType.RESPONSE


def test_mvp_handler_dsl_command_missing_param():
    handler = MVPProtocolHandler()
    msg = MVPMessage(message_type=MessageType.COMMAND, payload={"command": "dsl", "parameters": {}})
    response = handler.handle_message(msg)
    assert response.message_type == MessageType.ERROR


def test_mvp_handler_dsl_command_with_dsl():
    handler = MVPProtocolHandler()
    msg = MVPMessage(message_type=MessageType.COMMAND,
                     payload={"command": "dsl", "parameters": {"dsl": "restore endpoint:/api/health repo:/tmp"}})
    response = handler.handle_message(msg)
    assert response.message_type in (MessageType.RESPONSE, MessageType.ERROR)


def test_mvp_handler_nlp_command_missing_text():
    handler = MVPProtocolHandler()
    msg = MVPMessage(message_type=MessageType.COMMAND, payload={"command": "nlp", "parameters": {}})
    response = handler.handle_message(msg)
    assert response.message_type == MessageType.ERROR


def test_mvp_handler_evolution_command():
    handler = MVPProtocolHandler()
    msg = MVPMessage(message_type=MessageType.COMMAND, payload={"command": "evolution", "parameters": {}})
    response = handler.handle_message(msg)
    assert response.message_type == MessageType.RESPONSE


def test_mvp_handler_auto_pr_command():
    handler = MVPProtocolHandler()
    msg = MVPMessage(message_type=MessageType.COMMAND, payload={"command": "auto_pr", "parameters": {}})
    response = handler.handle_message(msg)
    assert response.message_type == MessageType.RESPONSE


# ─────────────────────────────────────────────
# analyze_command — smoke tests with mocks
# ─────────────────────────────────────────────

from rebuild.interfaces.commands.analyze_command import (
    duplicates_command, multi_repo_command, services_command, vector_query_command,
)
from rich.console import Console as RConsole


def test_duplicates_command_no_groups(tmp_path):
    buf = StringIO()
    console = RConsole(file=buf, highlight=False)
    with patch("rebuild.analysis.duplication_engine.DuplicationEngine") as MockEng:
        MockEng.return_value.scan.return_value = []
        MockEng.return_value.semantic_warning = None
        with patch("rebuild.analysis.duplication_engine.DuplicationEngine", MockEng):
            duplicates_command(tmp_path, 5, False, "m", 0.9, 50, console)
    assert "duplikatów" in buf.getvalue()


def test_duplicates_command_with_groups(tmp_path):
    buf = StringIO()
    console = RConsole(file=buf, highlight=False)
    frag = MagicMock()
    frag.file = "f.py"
    frag.start_line = 1
    frag.name = "fn"
    group = MagicMock()
    group.similarity = 0.95
    group.reason = "exact"
    group.fragments = [frag]
    mock_eng = MagicMock()
    mock_eng.scan.return_value = [group]
    mock_eng.semantic_warning = None
    import rebuild.analysis.duplication_engine as dup_mod
    with patch.object(dup_mod, "DuplicationEngine", return_value=mock_eng):
        duplicates_command(tmp_path, 5, False, "m", 0.9, 50, console)
    assert "Grupa 1" in buf.getvalue()


def test_duplicates_command_semantic_warning(tmp_path):
    buf = StringIO()
    console = RConsole(file=buf, highlight=False)
    mock_eng = MagicMock()
    mock_eng.scan.return_value = []
    mock_eng.semantic_warning = "model not found"
    import rebuild.analysis.duplication_engine as dup_mod
    with patch.object(dup_mod, "DuplicationEngine", return_value=mock_eng):
        duplicates_command(tmp_path, 5, True, "m", 0.9, 50, console)
    assert "model not found" in buf.getvalue()


def test_multi_repo_command_less_than_2_repos(tmp_path):
    buf = StringIO()
    console = RConsole(file=buf, highlight=False)
    import click
    with pytest.raises((click.exceptions.Exit, SystemExit)):
        multi_repo_command([tmp_path], 5, None, console)


def test_multi_repo_command_missing_repos(tmp_path):
    buf = StringIO()
    console = RConsole(file=buf, highlight=False)
    import click
    with pytest.raises((click.exceptions.Exit, SystemExit)):
        multi_repo_command([tmp_path / "a", tmp_path / "b"], 5, None, console)


def test_services_command_no_export(tmp_path):
    buf = StringIO()
    console = RConsole(file=buf, highlight=False)
    node = MagicMock()
    node.methods = ["m1"]
    node.dependencies = ["dep"]
    import rebuild.analysis.service_graph as sg_mod
    import rebuild.analysis.service_similarity as ss_mod
    mock_builder = MagicMock()
    mock_builder.build.return_value = {"MyService": node}
    mock_builder.detect_cycles.return_value = []
    mock_sim = MagicMock()
    mock_sim.analyze_directory.return_value = []
    with patch.object(sg_mod, "ServiceGraphBuilder", return_value=mock_builder), \
         patch.object(ss_mod, "ServiceSimilarityAnalyzer", return_value=mock_sim):
        services_command(tmp_path, False, console)
    assert "MyService" in buf.getvalue()


def test_services_command_with_cycles(tmp_path):
    buf = StringIO()
    console = RConsole(file=buf, highlight=False)
    import rebuild.analysis.service_graph as sg_mod
    import rebuild.analysis.service_similarity as ss_mod
    mock_builder = MagicMock()
    mock_builder.build.return_value = {}
    mock_builder.detect_cycles.return_value = [["A", "B", "A"]]
    mock_sim = MagicMock()
    mock_sim.analyze_directory.return_value = []
    with patch.object(sg_mod, "ServiceGraphBuilder", return_value=mock_builder), \
         patch.object(ss_mod, "ServiceSimilarityAnalyzer", return_value=mock_sim):
        services_command(tmp_path, False, console)
    assert "cykle" in buf.getvalue().lower() or "→" in buf.getvalue()


def test_vector_query_no_index(tmp_path):
    buf = StringIO()
    console = RConsole(file=buf, highlight=False)
    import click
    with pytest.raises((click.exceptions.Exit, SystemExit)):
        vector_query_command("query", tmp_path / "nonexistent.db", 5, 0.5, "m", console)


# ─────────────────────────────────────────────
# refactor_command — smoke tests
# ─────────────────────────────────────────────

from rebuild.interfaces.commands.refactor_command import plan_command, execute_command


def test_plan_command_no_suggestions(tmp_path):
    buf = StringIO()
    console = RConsole(file=buf, highlight=False)
    with patch("rebuild.interfaces.commands.refactor_command._generate_refactor_plan", return_value=[]):
        plan_command(tmp_path, False, console)
    assert "krytycznych" in buf.getvalue()


def test_plan_command_with_suggestions(tmp_path):
    buf = StringIO()
    console = RConsole(file=buf, highlight=False)
    suggestion = MagicMock()
    suggestion.title = "Extract method"
    suggestion.description = "Move logic out"
    suggestion.impact = "HIGH"
    suggestion.rationale = "reduces complexity"
    suggestion.files = []
    with patch("rebuild.interfaces.commands.refactor_command._generate_refactor_plan", return_value=[suggestion]):
        plan_command(tmp_path, False, console)
    assert "Extract method" in buf.getvalue()


def test_execute_command_no_suggestions(tmp_path):
    buf = StringIO()
    console = RConsole(file=buf, highlight=False)
    with patch("rebuild.interfaces.commands.refactor_command._generate_refactor_plan", return_value=[]):
        execute_command(tmp_path, True, console)
    assert "Brak" in buf.getvalue()


def test_execute_command_with_force(tmp_path):
    buf = StringIO()
    console = RConsole(file=buf, highlight=False)
    suggestion = MagicMock()
    suggestion.title = "Merge classes"
    import rebuild.refactor.refactor_executor as rex_mod
    mock_executor = MagicMock()
    mock_executor.execute_suggestion.return_value = True
    with patch("rebuild.interfaces.commands.refactor_command._generate_refactor_plan", return_value=[suggestion]), \
         patch.object(rex_mod, "RefactorExecutor", return_value=mock_executor):
        execute_command(tmp_path, True, console)
    assert "Merge classes" in buf.getvalue()


# ─────────────────────────────────────────────
# http_adapter — retry and other methods
# ─────────────────────────────────────────────

from rebuild.infrastructure.http_adapter import HttpAdapter
import httpx


def test_http_adapter_post(tmp_path):
    adapter = HttpAdapter()
    mock_resp = MagicMock()
    with patch.object(adapter.client, "post", return_value=mock_resp) as m:
        result = adapter.post("http://x", json={"a": 1})
    assert result == mock_resp


def test_http_adapter_put(tmp_path):
    adapter = HttpAdapter()
    mock_resp = MagicMock()
    with patch.object(adapter.client, "put", return_value=mock_resp):
        result = adapter.put("http://x", json={"a": 1})
    assert result == mock_resp


def test_http_adapter_patch(tmp_path):
    adapter = HttpAdapter()
    mock_resp = MagicMock()
    with patch.object(adapter.client, "patch", return_value=mock_resp):
        result = adapter.patch("http://x", json={"b": 2})
    assert result == mock_resp


def test_http_adapter_delete(tmp_path):
    adapter = HttpAdapter()
    mock_resp = MagicMock()
    with patch.object(adapter.client, "delete", return_value=mock_resp):
        result = adapter.delete("http://x")
    assert result == mock_resp


def test_http_adapter_get_retry_then_succeed():
    adapter = HttpAdapter(timeout=1, retries=3)
    good_resp = MagicMock()
    calls = [httpx.RequestError("fail"), good_resp]
    with patch.object(adapter.client, "get", side_effect=calls):
        with patch("time.sleep"):
            result = adapter.get("http://x")
    assert result == good_resp


def test_http_adapter_get_all_retries_fail():
    adapter = HttpAdapter(timeout=1, retries=2)
    with patch.object(adapter.client, "get", side_effect=httpx.RequestError("fail")):
        with patch("time.sleep"):
            with pytest.raises(httpx.RequestError):
                adapter.get("http://x")


def test_http_adapter_close():
    adapter = HttpAdapter()
    adapter.close()  # should not raise


# ─────────────────────────────────────────────
# analyze_command — remaining branches
# ─────────────────────────────────────────────

from rebuild.interfaces.commands.analyze_command import truth_command, vector_build_command


def test_truth_command_no_history(tmp_path):
    buf = StringIO()
    console = RConsole(file=buf, highlight=False)
    import rebuild.analysis.git_truth_analyzer as gta_mod
    mock_analyzer = MagicMock()
    mock_analyzer.analyze_function_history.return_value = []
    with patch.object(gta_mod, "GitTruthAnalyzer", return_value=mock_analyzer):
        truth_command(tmp_path / "f.py", "my_fn", tmp_path, console)
    assert "Nie znaleziono" in buf.getvalue()


def test_truth_command_with_history(tmp_path):
    from datetime import datetime as dt
    buf = StringIO()
    console = RConsole(file=buf, highlight=False)
    import rebuild.analysis.git_truth_analyzer as gta_mod
    q = MagicMock()
    q.commit_sha = "abc12345def"
    q.timestamp = dt(2025, 1, 1)
    q.complexity = 5
    q.size_lines = 20
    q.test_pass_rate = 0.9
    q.score = 8.5
    mock_analyzer = MagicMock()
    mock_analyzer.analyze_function_history.return_value = [q]
    with patch.object(gta_mod, "GitTruthAnalyzer", return_value=mock_analyzer):
        truth_command(tmp_path / "f.py", "my_fn", tmp_path, console)
    assert "abc12345" in buf.getvalue()


def test_vector_build_command(tmp_path):
    buf = StringIO()
    console = RConsole(file=buf, highlight=False)
    import rebuild.analysis.vector_search as vs_mod
    mock_vs = MagicMock()
    mock_vs.build_from_path.return_value = 42
    mock_vs.count.return_value = 42
    mock_vs.warning = None
    with patch.object(vs_mod, "VectorSearchIndex", return_value=mock_vs):
        vector_build_command(tmp_path, tmp_path / "idx.db", 5, "m", console)
    assert "42" in buf.getvalue()


def test_vector_build_command_with_warning(tmp_path):
    buf = StringIO()
    console = RConsole(file=buf, highlight=False)
    import rebuild.analysis.vector_search as vs_mod
    mock_vs = MagicMock()
    mock_vs.build_from_path.return_value = 0
    mock_vs.count.return_value = 0
    mock_vs.warning = "torch not available"
    with patch.object(vs_mod, "VectorSearchIndex", return_value=mock_vs):
        vector_build_command(tmp_path, tmp_path / "idx.db", 5, "m", console)
    assert "torch not available" in buf.getvalue()


def test_vector_query_with_results(tmp_path):
    buf = StringIO()
    console = RConsole(file=buf, highlight=False)
    idx = tmp_path / "idx.db"
    idx.touch()
    import rebuild.analysis.vector_search as vs_mod
    hit = MagicMock()
    hit.score = 0.9
    hit.fragment.file = "x.py"
    hit.fragment.start_line = 5
    hit.fragment.name = "fn"
    hit.fragment.content = "def fn(): pass"
    mock_vs = MagicMock()
    mock_vs.query.return_value = [hit]
    mock_vs.warning = None
    with patch.object(vs_mod, "VectorSearchIndex", return_value=mock_vs):
        vector_query_command("query", idx, 5, 0.5, "m", console)
    assert "fn" in buf.getvalue()


def test_vector_query_no_results_after_filter(tmp_path):
    buf = StringIO()
    console = RConsole(file=buf, highlight=False)
    idx = tmp_path / "idx.db"
    idx.touch()
    import rebuild.analysis.vector_search as vs_mod
    hit = MagicMock()
    hit.score = 0.1
    mock_vs = MagicMock()
    mock_vs.query.return_value = [hit]
    mock_vs.warning = None
    with patch.object(vs_mod, "VectorSearchIndex", return_value=mock_vs):
        vector_query_command("query", idx, 5, 0.5, "m", console)
    assert "Brak" in buf.getvalue()


def test_multi_repo_command_success(tmp_path):
    buf = StringIO()
    console = RConsole(file=buf, highlight=False)
    repo_a = tmp_path / "a"
    repo_b = tmp_path / "b"
    repo_a.mkdir()
    repo_b.mkdir()
    import rebuild.analysis.service_graph as sg_mod
    mock_analyzer = MagicMock()
    report = MagicMock()
    report.repositories = {"a": str(repo_a), "b": str(repo_b)}
    report.dependencies = []
    report.clone_groups = []
    mock_analyzer.analyze.return_value = report
    with patch.object(sg_mod, "MultiRepoAnalyzer", return_value=mock_analyzer):
        multi_repo_command([repo_a, repo_b], 5, None, console)
    assert "Repositories" in buf.getvalue()


def test_multi_repo_command_with_deps_and_clones(tmp_path):
    buf = StringIO()
    console = RConsole(file=buf, highlight=False)
    repo_a = tmp_path / "a"
    repo_b = tmp_path / "b"
    repo_a.mkdir()
    repo_b.mkdir()
    import rebuild.analysis.service_graph as sg_mod
    dep = MagicMock()
    dep.source_repo = "a"
    dep.target_repo = "b"
    dep.imports_count = 3
    clone = MagicMock()
    clone.structural_hash = "abc123456789xyz"
    clone.repositories = ["a", "b"]
    clone.fragments_count = 2
    mock_analyzer = MagicMock()
    report = MagicMock()
    report.repositories = {"a": str(repo_a), "b": str(repo_b)}
    report.dependencies = [dep]
    report.clone_groups = [clone]
    mock_analyzer.analyze.return_value = report
    with patch.object(sg_mod, "MultiRepoAnalyzer", return_value=mock_analyzer):
        multi_repo_command([repo_a, repo_b], 5, None, console)
    assert "a" in buf.getvalue()


# ─────────────────────────────────────────────
# helpers — print_report_links with port
# ─────────────────────────────────────────────

from rebuild.interfaces.commands.helpers import print_report_links


def test_print_report_links_with_port(tmp_path):
    buf = StringIO()
    console = Console(file=buf, highlight=False)
    print_report_links(tmp_path, 8080, console)
    assert "localhost:8080" in buf.getvalue()


def test_print_report_links_no_port(tmp_path):
    buf = StringIO()
    console = Console(file=buf, highlight=False)
    print_report_links(tmp_path, None, console)
    assert "index.html" in buf.getvalue()


# ─────────────────────────────────────────────
# refactor_command — remaining branches
# ─────────────────────────────────────────────

def test_execute_command_executor_fails(tmp_path):
    buf = StringIO()
    console = RConsole(file=buf, highlight=False)
    suggestion = MagicMock()
    suggestion.title = "Bad refactor"
    import rebuild.refactor.refactor_executor as rex_mod
    mock_executor = MagicMock()
    mock_executor.execute_suggestion.return_value = False
    with patch("rebuild.interfaces.commands.refactor_command._generate_refactor_plan", return_value=[suggestion]), \
         patch.object(rex_mod, "RefactorExecutor", return_value=mock_executor):
        execute_command(tmp_path, True, console)
    assert "Błąd" in buf.getvalue()


def test_plan_command_medium_impact(tmp_path):
    buf = StringIO()
    console = RConsole(file=buf, highlight=False)
    suggestion = MagicMock()
    suggestion.title = "Refactor X"
    suggestion.description = "desc"
    suggestion.impact = "MEDIUM"
    suggestion.rationale = ""
    suggestion.files = [MagicMock(name="a.py")]
    with patch("rebuild.interfaces.commands.refactor_command._generate_refactor_plan", return_value=[suggestion]):
        plan_command(tmp_path, False, console)
    assert "Refactor X" in buf.getvalue()


def test_plan_command_low_impact_with_files(tmp_path):
    buf = StringIO()
    console = RConsole(file=buf, highlight=False)
    f = MagicMock()
    f.name = "b.py"
    suggestion = MagicMock()
    suggestion.title = "Minor fix"
    suggestion.description = "d"
    suggestion.impact = "LOW"
    suggestion.rationale = "cleaner"
    suggestion.files = [f]
    with patch("rebuild.interfaces.commands.refactor_command._generate_refactor_plan", return_value=[suggestion]):
        plan_command(tmp_path, False, console)
    assert "Minor fix" in buf.getvalue()


# ─────────────────────────────────────────────
# pr_service
# ─────────────────────────────────────────────

from rebuild.application.services.pr_service import (
    PRService, PRConfig, PRResult, Platform, load_config_from_env
)


def test_pr_config_defaults():
    cfg = PRConfig(platform=Platform.GITHUB, token="tok", repo_owner="own", repo_name="repo")
    assert cfg.base_branch == "main"
    assert cfg.head_branch == "rebuild-auto"


def test_pr_service_github_success():
    cfg = PRConfig(platform=Platform.GITHUB, token="tok", repo_owner="own", repo_name="repo")
    svc = PRService(cfg)
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"html_url": "http://gh/pr/1", "number": 1}
    with patch("requests.post", return_value=mock_resp):
        result = svc.create_pr("summary", ["fix x"])
    assert result.success is True
    assert result.pr_number == 1


def test_pr_service_github_error():
    cfg = PRConfig(platform=Platform.GITHUB, token="tok", repo_owner="own", repo_name="repo")
    svc = PRService(cfg)
    mock_resp = MagicMock()
    mock_resp.status_code = 422
    mock_resp.text = "Unprocessable"
    with patch("requests.post", return_value=mock_resp):
        result = svc.create_pr("summary", [])
    assert result.success is False
    assert "422" in result.error


def test_pr_service_gitlab_success():
    cfg = PRConfig(platform=Platform.GITLAB, token="tok", repo_owner="own", repo_name="repo")
    svc = PRService(cfg)
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"web_url": "http://gl/mr/1", "iid": 7}
    with patch("requests.post", return_value=mock_resp):
        result = svc.create_pr("summary", ["fix y"])
    assert result.success is True
    assert result.pr_number == 7


def test_pr_service_gitlab_error():
    cfg = PRConfig(platform=Platform.GITLAB, token="tok", repo_owner="own", repo_name="repo")
    svc = PRService(cfg)
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Server Error"
    with patch("requests.post", return_value=mock_resp):
        result = svc.create_pr("summary", [])
    assert result.success is False


def test_pr_service_requests_import_error():
    cfg = PRConfig(platform=Platform.GITHUB, token="tok", repo_owner="own", repo_name="repo")
    svc = PRService(cfg)
    import builtins
    real_import = builtins.__import__
    def mock_import(name, *args, **kwargs):
        if name == "requests":
            raise ImportError("no requests")
        return real_import(name, *args, **kwargs)
    with patch("builtins.__import__", side_effect=mock_import):
        result = svc.create_pr("summary", [])
    assert result.success is False


def test_load_config_from_env_missing_platform():
    with patch.dict("os.environ", {}, clear=True):
        result = load_config_from_env()
    assert result is None


def test_load_config_from_env_invalid_platform():
    with patch.dict("os.environ", {"REBUILD_PR_PLATFORM": "bitbucket"}, clear=True):
        result = load_config_from_env()
    assert result is None


def test_load_config_from_env_missing_token():
    with patch.dict("os.environ", {"REBUILD_PR_PLATFORM": "github"}, clear=True):
        result = load_config_from_env()
    assert result is None


def test_load_config_from_env_full():
    env = {
        "REBUILD_PR_PLATFORM": "github",
        "REBUILD_PR_TOKEN": "tok",
        "REBUILD_PR_REPO_OWNER": "own",
        "REBUILD_PR_REPO_NAME": "repo",
    }
    with patch.dict("os.environ", env, clear=True):
        result = load_config_from_env()
    assert result is not None
    assert result.platform == Platform.GITHUB


# ─────────────────────────────────────────────
# summary_service
# ─────────────────────────────────────────────

from rebuild.application.services.summary_service import SummaryService


def test_summary_service_empty_duplication():
    svc = SummaryService()
    result = svc.generate_from_duplication({})
    assert result.suggestions == []
    assert result.total_duplication == 0.0


def test_summary_service_with_groups():
    svc = SummaryService()
    report = {
        "duplicate_groups": [
            {"fragments": [
                {"file_path": "a.py", "start_line": 1, "end_line": 5},
                {"file_path": "b.py", "start_line": 10, "end_line": 14},
            ]}
        ],
        "total_duplication_pct": 15.0,
    }
    result = svc.generate_from_duplication(report)
    assert len(result.suggestions) == 2
    assert result.total_duplication == 15.0


def test_summary_service_high_severity():
    svc = SummaryService()
    frags = [{"file_path": f"{i}.py", "start_line": i, "end_line": i+4} for i in range(5)]
    report = {"duplicate_groups": [{"fragments": frags}]}
    result = svc.generate_from_duplication(report)
    assert any(s.severity == "high" for s in result.suggestions)


def test_summary_service_from_service_graph_empty():
    svc = SummaryService()
    result = svc.generate_from_service_graph({})
    assert result is not None


# ─────────────────────────────────────────────
# refactor_executor
# ─────────────────────────────────────────────

from rebuild.refactor.refactor_executor import RefactorExecutor


def test_refactor_executor_execute_no_files(tmp_path):
    from rich.console import Console as RC
    console = RC(file=StringIO(), highlight=False)
    executor = RefactorExecutor(console)
    suggestion = MagicMock()
    suggestion.files = []
    suggestion.title = "Empty"
    result = executor.execute_suggestion(suggestion)
    assert isinstance(result, bool)


def test_refactor_executor_execute_with_files(tmp_path):
    from rich.console import Console as RC
    console = RC(file=StringIO(), highlight=False)
    executor = RefactorExecutor(console)
    f = MagicMock()
    f.__str__ = lambda self: str(tmp_path / "f.py")
    (tmp_path / "f.py").write_text("x = 1\n")
    suggestion = MagicMock()
    suggestion.files = [f]
    suggestion.title = "Fix f"
    result = executor.execute_suggestion(suggestion)
    assert isinstance(result, bool)


# ─────────────────────────────────────────────
# graph_exporter
# ─────────────────────────────────────────────

from rebuild.analysis.graph_exporter import GraphExporter


def test_graph_exporter_export_html(tmp_path):
    node = MagicMock()
    node.methods = ["get_data"]
    node.dependencies = ["ServiceB"]
    exporter = GraphExporter({"ServiceA": node})
    out = tmp_path / "arch.html"
    exporter.export_html(out)
    assert out.exists()
    content = out.read_text()
    assert "ServiceA" in content


def test_graph_exporter_empty(tmp_path):
    exporter = GraphExporter({})
    out = tmp_path / "arch.html"
    exporter.export_html(out)
    assert out.exists()


# ─────────────────────────────────────────────
# evolution_viz
# ─────────────────────────────────────────────

from rebuild.interfaces.evolution_viz import generate_evolution_html, _render_html


def test_render_html_empty_snapshots():
    html = _render_html([], "/repo", "Test Title")
    assert "Test Title" in html
    assert "REBUILD" in html


def test_render_html_with_snapshots():
    snapshots = [{"nodes": [], "edges": [], "commit_sha": "abc123"}]
    html = _render_html(snapshots, "/repo", "Evolution")
    assert "Evolution" in html
    assert "abc123" in html


def test_generate_evolution_html(tmp_path):
    import json
    timeline = tmp_path / "timeline.json"
    timeline.write_text(json.dumps({"snapshots": [], "repo_path": "/test"}))
    out = tmp_path / "evo.html"
    result = generate_evolution_html(timeline, out)
    assert result.exists()
    assert "REBUILD" in result.read_text()
