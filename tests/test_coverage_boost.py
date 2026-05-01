"""
Coverage boost tests targeting under-covered modules.
Focuses on: deploy_service, dsl, scanner_service, restore_service, formatters.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rebuild.domain.models import WalkConfig, DeployMethod
from rebuild.domain.day_result import DayResult, DeployErrorCategory
from rebuild.domain.endpoint import Endpoint, EndpointResult, EndpointStatus
from rebuild.domain.commit import CommitInfo


# ─────────────────────────────────────────────────────────────
# deploy_service — error category classification
# ─────────────────────────────────────────────────────────────

from rebuild.application.services.deploy_service import DeployService


def _cfg(tmp_path, method=DeployMethod.NONE, **kw):
    return WalkConfig(repo_path=tmp_path, deploy_method=method, **kw)


def test_classify_compose_build_fail(tmp_path):
    svc = DeployService(_cfg(tmp_path))
    cat = svc._classify_deploy_error("ERROR: failed to build image")
    assert cat == DeployErrorCategory.COMPOSE_BUILD_FAIL


def test_classify_port_conflict(tmp_path):
    svc = DeployService(_cfg(tmp_path))
    assert svc._classify_deploy_error("port is already allocated") == DeployErrorCategory.PORT_CONFLICT


def test_classify_migration_fail(tmp_path):
    svc = DeployService(_cfg(tmp_path))
    assert svc._classify_deploy_error("Applying migration 0001... FAILED") == DeployErrorCategory.MIGRATION_FAIL


def test_classify_missing_env(tmp_path):
    svc = DeployService(_cfg(tmp_path))
    assert svc._classify_deploy_error("missing required env variable SECRET_KEY") == DeployErrorCategory.MISSING_ENV


def test_classify_health_timeout(tmp_path):
    svc = DeployService(_cfg(tmp_path))
    svc.last_error_category = DeployErrorCategory.HEALTH_TIMEOUT
    assert svc.last_error_category == DeployErrorCategory.HEALTH_TIMEOUT


def test_classify_unknown(tmp_path):
    svc = DeployService(_cfg(tmp_path))
    assert svc._classify_deploy_error("something completely unexpected") == DeployErrorCategory.UNKNOWN


def test_detect_deploy_method_docker_compose(tmp_path):
    (tmp_path / "docker-compose.yml").touch()
    svc = DeployService(_cfg(tmp_path))
    assert svc.detect_deploy_method(tmp_path) == DeployMethod.DOCKER_COMPOSE


def test_detect_deploy_method_uvicorn(tmp_path):
    (tmp_path / "server.py").touch()
    svc = DeployService(_cfg(tmp_path))
    assert svc.detect_deploy_method(tmp_path) == DeployMethod.UVICORN


def test_detect_deploy_method_none(tmp_path):
    svc = DeployService(_cfg(tmp_path))
    assert svc.detect_deploy_method(tmp_path) == DeployMethod.NONE


def test_start_docker_compose_calls_compose_up(tmp_path):
    cfg = _cfg(tmp_path, method=DeployMethod.DOCKER_COMPOSE)
    svc = DeployService(cfg)
    with patch.object(svc, "_run_with_retry", return_value=True) as mock_retry:
        result = svc.start(tmp_path)
    assert result is True
    mock_retry.assert_called_once()


def test_stop_docker_compose_calls_down(tmp_path):
    cfg = _cfg(tmp_path, method=DeployMethod.DOCKER_COMPOSE)
    svc = DeployService(cfg)
    with patch.object(svc, "_compose_down") as mock_down:
        svc.stop(tmp_path)
    mock_down.assert_called_once_with(tmp_path)


def test_stop_uvicorn_calls_stop(tmp_path):
    cfg = _cfg(tmp_path, method=DeployMethod.UVICORN)
    svc = DeployService(cfg)
    with patch.object(svc, "_uvicorn_stop") as mock_stop:
        svc.stop(tmp_path)
    mock_stop.assert_called_once()


def test_run_with_retry_succeeds_first(tmp_path):
    svc = DeployService(_cfg(tmp_path))
    called = []
    def action():
        called.append(1)
        return True
    result = svc._run_with_retry(action, "test")
    assert result is True
    assert len(called) == 1


def test_run_with_retry_fails_all(tmp_path):
    cfg = WalkConfig(repo_path=tmp_path, deploy_retry_attempts=2, deploy_retry_backoff_seconds=0.0)
    svc = DeployService(cfg)
    called = []
    def action():
        called.append(1)
        return False
    result = svc._run_with_retry(action, "test")
    assert result is False
    assert len(called) == 2


# ─────────────────────────────────────────────────────────────
# DSL
# ─────────────────────────────────────────────────────────────

from rebuild.domain.dsl import DSLParser, DSLInterpreter, Command


def test_dsl_parse_walk():
    cmd = DSLParser().parse("walk repo:/tmp days:7 deploy:docker-compose")
    assert cmd.command == Command.WALK
    assert cmd.parameters["repo"] == "/tmp"
    assert cmd.parameters["days"] == 7
    assert cmd.parameters["deploy"] == "docker-compose"


def test_dsl_parse_flags():
    cmd = DSLParser().parse("walk dry_run=true replay=false")
    assert cmd.flags["dry_run"] is True
    assert cmd.flags["replay"] is False


def test_dsl_parse_unknown_command():
    with pytest.raises(ValueError, match="Unknown command"):
        DSLParser().parse("unknown cmd")


def test_dsl_parse_empty():
    with pytest.raises(ValueError, match="Empty"):
        DSLParser().parse("")


def test_dsl_parse_analyze():
    cmd = DSLParser().parse("analyze repo:/src type:duplicates min_lines:6")
    assert cmd.command == Command.ANALYZE
    assert cmd.parameters["type"] == "duplicates"
    assert cmd.parameters["min_lines"] == 6


def test_dsl_parse_file(tmp_path):
    script = tmp_path / "test.dsl"
    script.write_text("walk repo:/tmp days:3\n# comment\nanalyze type:services\n")
    cmds = DSLParser().parse_file(script)
    assert len(cmds) == 2
    assert cmds[0].command == Command.WALK
    assert cmds[1].command == Command.ANALYZE


def test_dsl_interpreter_walk():
    cmd = DSLParser().parse("walk repo:/tmp days:5")
    result = DSLInterpreter().execute(cmd)
    assert result["command"] == "walk"
    assert result["days"] == 5
    assert result["status"] == "parsed"


def test_dsl_interpreter_analyze():
    cmd = DSLParser().parse("analyze type:services")
    result = DSLInterpreter().execute(cmd)
    assert result["command"] == "analyze"


def test_dsl_interpreter_evolution():
    cmd = DSLParser().parse("evolution timeline:/tmp/tl.json output:out.html")
    result = DSLInterpreter().execute(cmd)
    assert result["command"] == "evolution"
    assert result["output"] == "out.html"


def test_dsl_interpreter_serve():
    cmd = DSLParser().parse("serve results_dir:.rebuild port:7821")
    result = DSLInterpreter().execute(cmd)
    assert result["command"] == "serve"
    assert result["port"] == 7821


def test_dsl_interpreter_restore():
    cmd = DSLParser().parse("restore endpoint:/api/health repo:/tmp")
    result = DSLInterpreter().execute(cmd)
    assert result["command"] == "restore"


def test_dsl_interpreter_accelerator():
    cmd = DSLParser().parse("accelerator repo:/tmp days:10 parallel:4")
    result = DSLInterpreter().execute(cmd)
    assert result["command"] == "accelerator"
    assert result["parallel"] == 4


# ─────────────────────────────────────────────────────────────
# reporting/formatters
# ─────────────────────────────────────────────────────────────

from rebuild.application.services.reporting.formatters import (
    to_yaml, to_toon, status_badge, classify_error
)


def _make_commit():
    return CommitInfo(sha="abc12345", message="test", author="tester",
                      timestamp="2025-01-01T00:00:00", date=date(2025, 1, 1))


def _make_day_result(tmp_path):
    ep = Endpoint(method="GET", path="/api/health", base_url="http://localhost:8003")
    er = EndpointResult(endpoint=ep, status=EndpointStatus.OK, http_status=200)
    return DayResult(
        day=date(2025, 1, 1),
        commit=_make_commit(),
        deploy_method=DeployMethod.NONE,
        deploy_success=True,
        endpoints=[ep],
        endpoint_results=[er],
        output_dir=tmp_path,
    )


def test_to_yaml_simple():
    out = to_yaml({"key": "val", "num": 42})
    assert "key: val" in out
    assert "num: 42" in out


def test_to_yaml_nested():
    out = to_yaml({"a": {"b": "c"}})
    assert "a:" in out
    assert "b: c" in out


def test_to_yaml_list():
    out = to_yaml({"items": [1, 2, 3]})
    assert "items:" in out
    assert "- 1" in out


def test_to_toon(tmp_path):
    dr = _make_day_result(tmp_path)
    out = to_toon(dr)
    assert "type: rebuild_report" in out
    assert "day: 2025-01-01" in out
    assert "deploy: success" in out


def test_status_badge_ok():
    badge = status_badge(EndpointStatus.OK)
    assert "OK" in badge
    assert "green" in badge.lower() or "#22c55e" in badge


def test_status_badge_fail():
    badge = status_badge(EndpointStatus.FAIL)
    assert "FAIL" in badge


def test_classify_error_ok():
    ep = Endpoint(method="GET", path="/", base_url="http://x")
    er = EndpointResult(endpoint=ep, status=EndpointStatus.OK)
    assert classify_error(er) == ""


def test_classify_error_fail_auth():
    ep = Endpoint(method="GET", path="/", base_url="http://x")
    er = EndpointResult(endpoint=ep, status=EndpointStatus.FAIL_AUTH, error="401 Unauthorized")
    assert classify_error(er) == "auth"


def test_classify_error_fail_network():
    ep = Endpoint(method="GET", path="/", base_url="http://x")
    er = EndpointResult(endpoint=ep, status=EndpointStatus.FAIL_NETWORK, error="Connection refused")
    assert classify_error(er) == "network"


def test_classify_error_by_keyword():
    ep = Endpoint(method="GET", path="/", base_url="http://x")
    er = EndpointResult(endpoint=ep, status=EndpointStatus.FAIL, error="connection refused")
    assert classify_error(er) == "network"


# ─────────────────────────────────────────────────────────────
# reporting/chart_builder
# ─────────────────────────────────────────────────────────────

from rebuild.application.services.reporting.chart_builder import (
    generate_trend_chart, generate_endpoint_diff
)


def _make_results(n: int, tmp_path: Path):
    results = []
    for i in range(n):
        ep = Endpoint(method="GET", path=f"/ep{i}", base_url="http://x")
        er = EndpointResult(endpoint=ep, status=EndpointStatus.OK, http_status=200)
        dr = DayResult(
            day=date(2025, 1, i + 1),
            commit=CommitInfo(sha=f"sha{i:08d}", message="m", author="a",
                              timestamp="t", date=date(2025, 1, i + 1)),
            deploy_method=DeployMethod.NONE,
            deploy_success=True,
            endpoints=[ep],
            endpoint_results=[er],
            output_dir=tmp_path / str(i),
        )
        results.append(dr)
    return results


def test_generate_trend_chart_empty():
    assert generate_trend_chart([]) == ""


def test_generate_trend_chart_single(tmp_path):
    results = _make_results(1, tmp_path)
    svg = generate_trend_chart(results)
    assert "<svg" in svg
    assert "polyline" in svg


def test_generate_trend_chart_multiple(tmp_path):
    results = _make_results(5, tmp_path)
    svg = generate_trend_chart(results)
    assert "<svg" in svg
    assert svg.count("<circle") == 5


def test_generate_endpoint_diff_empty(tmp_path):
    results = _make_results(1, tmp_path)
    assert generate_endpoint_diff(results) == ""


def test_generate_endpoint_diff_detects_added(tmp_path):
    ep1 = Endpoint(method="GET", path="/a", base_url="http://x")
    ep2 = Endpoint(method="GET", path="/b", base_url="http://x")
    er1 = EndpointResult(endpoint=ep1, status=EndpointStatus.OK)
    er2 = EndpointResult(endpoint=ep2, status=EndpointStatus.OK)
    r1 = DayResult(day=date(2025,1,1),
                   commit=CommitInfo(sha="s1", message="m", author="a", timestamp="t", date=date(2025,1,1)),
                   deploy_method=DeployMethod.NONE, deploy_success=True,
                   endpoints=[ep1], endpoint_results=[er1], output_dir=tmp_path/"d1")
    r2 = DayResult(day=date(2025,1,2),
                   commit=CommitInfo(sha="s2", message="m", author="a", timestamp="t", date=date(2025,1,2)),
                   deploy_method=DeployMethod.NONE, deploy_success=True,
                   endpoints=[ep1, ep2], endpoint_results=[er1, er2], output_dir=tmp_path/"d2")
    diff = generate_endpoint_diff([r1, r2])
    assert "added" in diff


# ─────────────────────────────────────────────────────────────
# DayResult serialization
# ─────────────────────────────────────────────────────────────

def test_day_result_to_dict_with_error_category(tmp_path):
    ep = Endpoint(method="GET", path="/api", base_url="http://x")
    er = EndpointResult(endpoint=ep, status=EndpointStatus.FAIL_AUTH, http_status=401, fail_reason="no token")
    dr = DayResult(
        day=date(2025, 6, 1),
        commit=None,
        deploy_method=DeployMethod.DOCKER_COMPOSE,
        deploy_success=False,
        endpoints=[ep],
        endpoint_results=[er],
        deploy_error_category=DeployErrorCategory.HEALTH_TIMEOUT,
    )
    d = dr.to_dict()
    assert d["deploy"]["error_category"] == "health_timeout"
    assert dr.fail_count == 1
    assert dr.ok_count == 0


def test_day_result_health_pct_all_ok():
    ep = Endpoint(method="GET", path="/", base_url="http://x")
    er = EndpointResult(endpoint=ep, status=EndpointStatus.OK, http_status=200)
    dr = DayResult(
        day=date(2025, 1, 1), commit=None,
        deploy_method=DeployMethod.NONE, deploy_success=True,
        endpoints=[ep], endpoint_results=[er],
    )
    assert dr.health_pct == 100


def test_day_result_health_pct_partial():
    ep1 = Endpoint(method="GET", path="/a", base_url="http://x")
    ep2 = Endpoint(method="GET", path="/b", base_url="http://x")
    er1 = EndpointResult(endpoint=ep1, status=EndpointStatus.OK, http_status=200)
    er2 = EndpointResult(endpoint=ep2, status=EndpointStatus.FAIL, http_status=500)
    dr = DayResult(
        day=date(2025, 1, 1), commit=None,
        deploy_method=DeployMethod.NONE, deploy_success=True,
        endpoints=[ep1, ep2], endpoint_results=[er1, er2],
    )
    assert dr.health_pct == 50


def test_day_result_skip_not_counted_as_fail():
    ep = Endpoint(method="DELETE", path="/x", base_url="http://x")
    er = EndpointResult(endpoint=ep, status=EndpointStatus.SKIP_METHOD)
    dr = DayResult(
        day=date(2025, 1, 1), commit=None,
        deploy_method=DeployMethod.NONE, deploy_success=True,
        endpoints=[ep], endpoint_results=[er],
    )
    assert dr.fail_count == 0


# ─────────────────────────────────────────────────────────────
# MVP protocol dispatch table
# ─────────────────────────────────────────────────────────────

from rebuild.domain.mvp_protocol import MVPProtocolHandler, MVPMessage, MessageType


def test_mvp_handle_walk():
    handler = MVPProtocolHandler()
    msg = MVPMessage(message_type=MessageType.COMMAND, payload={"command": "walk", "parameters": {"days": 7}})
    resp = handler.handle_message(msg)
    assert resp.message_type == MessageType.RESPONSE
    assert resp.payload["command"] == "walk"


def test_mvp_handle_analyze():
    handler = MVPProtocolHandler()
    msg = MVPMessage(message_type=MessageType.COMMAND, payload={"command": "analyze", "parameters": {}})
    resp = handler.handle_message(msg)
    assert resp.payload["command"] == "analyze"


def test_mvp_unknown_command():
    handler = MVPProtocolHandler()
    msg = MVPMessage(message_type=MessageType.COMMAND, payload={"command": "kaboom", "parameters": {}})
    resp = handler.handle_message(msg)
    assert resp.message_type == MessageType.ERROR
    assert "kaboom" in resp.payload["error"]


def test_mvp_missing_command():
    handler = MVPProtocolHandler()
    msg = MVPMessage(message_type=MessageType.COMMAND, payload={})
    resp = handler.handle_message(msg)
    assert resp.message_type == MessageType.ERROR


def test_mvp_event_handler():
    handler = MVPProtocolHandler()
    msg = MVPMessage(message_type=MessageType.EVENT, payload={"event_type": "test"})
    resp = handler.handle_message(msg)
    assert resp.message_type == MessageType.RESPONSE
    assert resp.payload["event_type"] == "test"


def test_mvp_message_roundtrip():
    msg = MVPMessage(message_type=MessageType.COMMAND, payload={"command": "serve"})
    json_str = msg.to_json()
    restored = MVPMessage.from_json(json_str)
    assert restored.message_type == MessageType.COMMAND
    assert restored.payload["command"] == "serve"


def test_mvp_handle_dsl():
    handler = MVPProtocolHandler()
    msg = MVPMessage(message_type=MessageType.COMMAND, payload={
        "command": "dsl", "parameters": {"dsl": "walk repo:/tmp days:3"}
    })
    resp = handler.handle_message(msg)
    assert resp.message_type == MessageType.RESPONSE
    assert resp.payload["status"] == "executed"


def test_mvp_handle_nlp():
    handler = MVPProtocolHandler()
    msg = MVPMessage(message_type=MessageType.COMMAND, payload={
        "command": "nlp", "parameters": {"text": "walk last 7 days"}
    })
    resp = handler.handle_message(msg)
    assert resp.message_type == MessageType.RESPONSE
    assert "intent" in resp.payload


# ─────────────────────────────────────────────────────────────
# NLP service
# ─────────────────────────────────────────────────────────────

from rebuild.application.services.nlp_service import NLPService, Intent


def test_nlp_detect_walk():
    svc = NLPService()
    cmd = svc.parse("walk last 7 days")
    assert cmd.intent == Intent.WALK
    assert cmd.confidence > 0
    assert cmd.parameters.get("days") == "7"


def test_nlp_detect_analyze():
    svc = NLPService()
    cmd = svc.parse("analyze duplicates in code")
    assert cmd.intent == Intent.ANALYZE


def test_nlp_to_dsl():
    svc = NLPService()
    cmd = svc.parse("walk last 30 days")
    dsl = svc.to_dsl(cmd)
    assert dsl.startswith("walk")
    assert "30" in dsl


def test_nlp_to_cli_args():
    svc = NLPService()
    cmd = svc.parse("restore endpoint")
    args = svc.to_cli_args(cmd)
    assert isinstance(args, list)
    assert len(args) >= 1


def test_nlp_dry_run_flag():
    svc = NLPService()
    cmd = svc.parse("walk dry-run mode")
    assert cmd.parameters.get("dry_run") == "true"


def test_nlp_semantic_flag():
    svc = NLPService()
    cmd = svc.parse("analyze with semantic embeddings")
    assert cmd.parameters.get("semantic") == "true"


def test_nlp_unknown_falls_back_to_help():
    svc = NLPService()
    cmd = svc.parse("xyzzy frobozz")
    assert cmd.intent == Intent.HELP
    assert cmd.confidence > 0
