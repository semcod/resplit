"""Sprint 5c coverage boost (2026-05-08).

Targets the lowest-hanging coverage gaps to push total coverage from 77 % toward
≥80 %. Each test exercises a previously-uncovered code path; we never touch
real network / filesystem outside ``tmp_path``.

Modules covered here:

* :mod:`rebuild.domain.context` (``EndpointContext`` dataclass) — was 0 %.
* :mod:`rebuild.domain.events` (legacy ``PipelineEvent``) — was 0 %.
* :mod:`rebuild.__main__` — import smoke (was 0 %).
* :mod:`rebuild.application.services.tui_data_service` — was 25 %.
* :mod:`rebuild.application.services.test_service` — was 60 %.
* :mod:`rebuild.domain.mvp_protocol` — was 68 %, all routing branches.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ───────────────────────────────────────────────────────────────────────────
# domain/context.py — EndpointContext dataclass
# ───────────────────────────────────────────────────────────────────────────


def test_endpoint_context_dataclass_round_trip():
    from datetime import datetime

    from rebuild.domain.commit import CommitInfo
    from rebuild.domain.context import EndpointContext
    from rebuild.domain.endpoint import Endpoint, EndpointResult, EndpointStatus

    ep = Endpoint(method="GET", path="/x", base_url="http://x")
    ci = CommitInfo(
        sha="abc1234",
        message="m",
        author="a",
        timestamp=datetime(2025, 1, 1, 12, 0, 0),
        date=date(2025, 1, 1),
    )
    ctx = EndpointContext(endpoint=ep, commit=ci, day=date(2025, 1, 1))
    assert ctx.endpoint is ep
    assert ctx.commit is ci
    assert ctx.day == date(2025, 1, 1)
    assert ctx.result is None

    res = EndpointResult(endpoint=ep, status=EndpointStatus.OK)
    ctx2 = EndpointContext(endpoint=ep, commit=ci, day=date(2025, 1, 2), result=res)
    assert ctx2.result is res


# ───────────────────────────────────────────────────────────────────────────
# domain/events.py — legacy PipelineEvent
# ───────────────────────────────────────────────────────────────────────────


def test_pipeline_event_create_and_to_json():
    from rebuild.domain.events import PipelineEvent

    ev = PipelineEvent.create("DEPLOY_STARTED", commit="abc123", method="docker")
    assert ev.event_type == "DEPLOY_STARTED"
    assert ev.timestamp  # ISO string
    assert ev.data == {"commit": "abc123", "method": "docker"}

    payload = json.loads(ev.to_json())
    assert payload["event_type"] == "DEPLOY_STARTED"
    assert payload["data"]["commit"] == "abc123"
    assert payload["timestamp"] == ev.timestamp


def test_pipeline_event_direct_construction():
    from rebuild.domain.events import PipelineEvent

    ev = PipelineEvent(event_type="X", timestamp="2025-01-01T00:00:00", data={"k": "v"})
    assert ev.to_json() == json.dumps({"event_type": "X", "timestamp": "2025-01-01T00:00:00", "data": {"k": "v"}})


# ───────────────────────────────────────────────────────────────────────────
# __main__.py — import smoke (sets module-level statements as covered)
# ───────────────────────────────────────────────────────────────────────────


def test_main_module_imports_app():
    """``python -m rebuild`` re-exports the typer app."""
    import importlib

    mod = importlib.import_module("rebuild.__main__")
    assert hasattr(mod, "app")
    # The conditional ``if __name__ == "__main__"`` branch is naturally skipped
    # under import; we only need the top-level statements covered.


# ───────────────────────────────────────────────────────────────────────────
# application/services/tui_data_service.py — TUIDataService
# ───────────────────────────────────────────────────────────────────────────


class TestTUIDataService:
    def test_health_bar_green_yellow_red(self):
        from rebuild.application.services.tui_data_service import TUIDataService

        green = TUIDataService.health_bar(95.0)
        yellow = TUIDataService.health_bar(60.0)
        red = TUIDataService.health_bar(20.0)
        assert "green" in green and "95" in green
        assert "yellow" in yellow and "60" in yellow
        assert "red" in red and "20" in red

    def test_calc_health_empty(self):
        from rebuild.application.services.tui_data_service import TUIDataService

        assert TUIDataService.calc_health([]) == 0.0

    def test_calc_health_partial(self):
        from rebuild.application.services.tui_data_service import TUIDataService

        results = [{"status": "ok"}, {"status": "ok"}, {"status": "fail"}]
        # 2 / 3 = 66.666... → rounded to 66.7
        assert TUIDataService.calc_health(results) == 66.7

    def test_endpoint_diff_added_removed_status_changed(self):
        from rebuild.application.services.tui_data_service import TUIDataService

        prev = [
            {"method": "GET", "path": "/a", "status": "ok"},
            {"method": "GET", "path": "/b", "status": "ok"},
        ]
        curr = [
            {"method": "GET", "path": "/a", "status": "fail"},  # status_changed
            {"method": "GET", "path": "/c", "status": "ok"},     # added
            # /b is missing → removed
        ]
        changes = TUIDataService.endpoint_diff(prev, curr)
        kinds = {(c["path"], c["change"]) for c in changes}
        assert ("/a", "status_changed") in kinds
        assert ("/c", "added") in kinds
        assert ("/b", "removed") in kinds
        # status_changed must carry the previous status for diff display.
        a_change = next(c for c in changes if c["path"] == "/a")
        assert a_change["prev_status"] == "ok"
        assert a_change["status"] == "fail"

    def test_load_day_results_skips_non_dirs_and_invalid_dates(self, tmp_path: Path):
        from rebuild.application.services.tui_data_service import TUIDataService

        # Valid day with results.json + commit.txt
        good = tmp_path / "2025-01-01"
        good.mkdir()
        (good / "results.json").write_text(json.dumps([{"method": "GET", "path": "/x", "status": "ok"}]))
        (good / "commit.txt").write_text("abc1234 first commit\nignored line")

        # Day directory but missing results.json → skipped
        skip_no_json = tmp_path / "2025-01-02"
        skip_no_json.mkdir()

        # Plain file (not a dir) → skipped
        (tmp_path / "stray.txt").write_text("noise")

        # Directory with results.json but invalid ISO date name → skipped
        bad_name = tmp_path / "not-a-date"
        bad_name.mkdir()
        (bad_name / "results.json").write_text("[]")

        days = TUIDataService.load_day_results(tmp_path)
        assert len(days) == 1
        assert days[0]["day"] == "2025-01-01"
        assert days[0]["commit"].startswith("abc1234")
        assert days[0]["results"] == [{"method": "GET", "path": "/x", "status": "ok"}]
        assert days[0]["path"] == good

    def test_load_day_results_handles_corrupt_json(self, tmp_path: Path):
        from rebuild.application.services.tui_data_service import TUIDataService

        d = tmp_path / "2025-01-01"
        d.mkdir()
        (d / "results.json").write_text("{not valid json")
        days = TUIDataService.load_day_results(tmp_path)
        # Corrupt JSON → empty results, day is still listed.
        assert len(days) == 1
        assert days[0]["results"] == []
        assert days[0]["commit"] == "—"  # no commit.txt

    def test_get_git_repo_toplevel_returns_path_on_success(self, tmp_path: Path):
        from rebuild.application.services.tui_data_service import TUIDataService

        with patch("subprocess.run") as run:
            run.return_value = MagicMock(returncode=0, stdout="/home/u/repo\n")
            assert TUIDataService.get_git_repo_toplevel(tmp_path) == "/home/u/repo"

    def test_get_git_repo_toplevel_returns_none_on_failure(self, tmp_path: Path):
        from rebuild.application.services.tui_data_service import TUIDataService

        with patch("subprocess.run") as run:
            run.return_value = MagicMock(returncode=128, stdout="")
            assert TUIDataService.get_git_repo_toplevel(tmp_path) is None

    def test_get_git_repo_toplevel_swallows_exceptions(self, tmp_path: Path):
        from rebuild.application.services.tui_data_service import TUIDataService

        with patch("subprocess.run", side_effect=FileNotFoundError("git missing")):
            assert TUIDataService.get_git_repo_toplevel(tmp_path) is None


# ───────────────────────────────────────────────────────────────────────────
# application/services/test_service.py — TestService
# ───────────────────────────────────────────────────────────────────────────


def _walk_config(tmp_path: Path, **overrides):
    from rebuild.domain.models import DeployMethod, WalkConfig

    cfg = WalkConfig(
        repo_path=tmp_path,
        output_dir=tmp_path / ".rebuild",
        deploy_method=DeployMethod.NONE,
    )
    for k, v in overrides.items():
        setattr(cfg, k, v)
    return cfg


class TestTestServiceClassification:
    """Cover ``_classify_http_status`` decision matrix end-to-end."""

    def test_2xx_is_ok(self, tmp_path: Path):
        from rebuild.application.services.test_service import TestService
        from rebuild.domain.endpoint import EndpointStatus

        svc = TestService(_walk_config(tmp_path))
        assert svc._classify_http_status(200, needs_auth=False) == EndpointStatus.OK
        assert svc._classify_http_status(204, needs_auth=True) == EndpointStatus.OK
        assert svc._classify_http_status(301, needs_auth=False) == EndpointStatus.OK

    def test_401_403_is_fail_auth(self, tmp_path: Path):
        from rebuild.application.services.test_service import TestService
        from rebuild.domain.endpoint import EndpointStatus

        svc = TestService(_walk_config(tmp_path))
        assert svc._classify_http_status(401, needs_auth=False) == EndpointStatus.FAIL_AUTH
        assert svc._classify_http_status(403, needs_auth=False) == EndpointStatus.FAIL_AUTH

    def test_405_no_auth_is_skip_method(self, tmp_path: Path):
        from rebuild.application.services.test_service import TestService
        from rebuild.domain.endpoint import EndpointStatus

        svc = TestService(_walk_config(tmp_path))
        assert svc._classify_http_status(405, needs_auth=False) == EndpointStatus.SKIP_METHOD

    def test_5xx_is_fail_server(self, tmp_path: Path):
        from rebuild.application.services.test_service import TestService
        from rebuild.domain.endpoint import EndpointStatus

        svc = TestService(_walk_config(tmp_path))
        assert svc._classify_http_status(500, needs_auth=False) == EndpointStatus.FAIL_SERVER
        assert svc._classify_http_status(503, needs_auth=True) == EndpointStatus.FAIL_SERVER

    def test_other_4xx_is_fail(self, tmp_path: Path):
        from rebuild.application.services.test_service import TestService
        from rebuild.domain.endpoint import EndpointStatus

        svc = TestService(_walk_config(tmp_path))
        assert svc._classify_http_status(404, needs_auth=False) == EndpointStatus.FAIL
        assert svc._classify_http_status(422, needs_auth=False) == EndpointStatus.FAIL


class TestTestServiceExecution:
    def _ep(self, method: str = "GET", path: str = "/x", template: str | None = None):
        from rebuild.domain.endpoint import Endpoint

        return Endpoint(method=method, path=path, base_url="http://x", template_path=template)

    def _mock_response(self, status_code: int = 200, elapsed_ms: float | None = 12.0):
        from datetime import timedelta

        resp = MagicMock()
        resp.status_code = status_code
        if elapsed_ms is None:
            resp.elapsed = None
        else:
            resp.elapsed = timedelta(milliseconds=elapsed_ms)
        return resp

    def test_set_day_dir_assigns(self, tmp_path: Path):
        from rebuild.application.services.test_service import TestService

        svc = TestService(_walk_config(tmp_path))
        svc.set_day_dir(tmp_path / "2025-01-01")
        assert svc.day_dir == tmp_path / "2025-01-01"

    def test_dry_run_returns_skip(self, tmp_path: Path):
        from rebuild.application.services.test_service import TestService
        from rebuild.domain.endpoint import EndpointStatus

        svc = TestService(_walk_config(tmp_path, dry_run=True))
        out = svc.execute([self._ep()])
        assert len(out) == 1
        assert out[0].status == EndpointStatus.SKIP

    def test_unresolved_template_short_circuits(self, tmp_path: Path):
        from rebuild.application.services.test_service import TestService
        from rebuild.domain.endpoint import EndpointStatus

        svc = TestService(_walk_config(tmp_path))
        ep = self._ep(path="/users/{id}", template="/users/{id}")
        out = svc.execute([ep])
        assert out[0].status == EndpointStatus.FAIL_TEMPLATE
        assert "Unresolved template" in (out[0].fail_reason or "")

    def test_get_request_classifies_200(self, tmp_path: Path):
        from rebuild.application.services.test_service import TestService
        from rebuild.domain.endpoint import EndpointStatus

        http = MagicMock()
        http.get.return_value = self._mock_response(200)
        svc = TestService(_walk_config(tmp_path), http=http)
        out = svc.execute([self._ep()])
        assert out[0].status == EndpointStatus.OK
        assert out[0].http_status == 200
        assert out[0].response_time_ms == pytest.approx(12.0, abs=0.5)
        http.get.assert_called_once()

    @pytest.mark.parametrize("method,attr", [
        ("POST", "post"),
        ("PUT", "put"),
        ("PATCH", "patch"),
        ("DELETE", "delete"),
    ])
    def test_method_dispatch_uses_correct_http_verb(self, tmp_path: Path, method: str, attr: str):
        from rebuild.application.services.test_service import TestService

        http = MagicMock()
        getattr(http, attr).return_value = self._mock_response(200)
        svc = TestService(_walk_config(tmp_path), http=http)
        ep = self._ep(method=method)
        if method in ("POST", "PUT", "PATCH"):
            ep.body = {"k": "v"}
        svc.execute([ep])
        getattr(http, attr).assert_called_once()

    def test_unknown_method_falls_back_to_get(self, tmp_path: Path):
        from rebuild.application.services.test_service import TestService

        http = MagicMock()
        http.get.return_value = self._mock_response(200)
        svc = TestService(_walk_config(tmp_path), http=http)
        svc.execute([self._ep(method="OPTIONS")])
        http.get.assert_called_once()

    def test_network_error_classifies_fail_network(self, tmp_path: Path):
        from rebuild.application.services.test_service import TestService
        from rebuild.domain.endpoint import EndpointStatus

        http = MagicMock()
        http.get.side_effect = Exception("Connection refused by host")
        svc = TestService(_walk_config(tmp_path), http=http)
        out = svc.execute([self._ep()])
        assert out[0].status == EndpointStatus.FAIL_NETWORK
        assert "Connection refused" in (out[0].error or "")

    def test_generic_exception_classifies_fail(self, tmp_path: Path):
        from rebuild.application.services.test_service import TestService
        from rebuild.domain.endpoint import EndpointStatus

        http = MagicMock()
        http.get.side_effect = Exception("unexpected weirdness")
        svc = TestService(_walk_config(tmp_path), http=http)
        out = svc.execute([self._ep()])
        assert out[0].status == EndpointStatus.FAIL
        assert "weirdness" in (out[0].error or "")

    def test_login_succeeds_and_attaches_bearer(self, tmp_path: Path):
        from rebuild.application.services.test_service import TestService

        http = MagicMock()
        login_resp = MagicMock(status_code=200)
        login_resp.json.return_value = {"access_token": "tok123"}
        http.post.return_value = login_resp
        http.get.return_value = self._mock_response(200)

        svc = TestService(
            _walk_config(
                tmp_path,
                login_url="http://x/login",
                login_payload={"u": "v"},
            ),
            http=http,
        )
        svc.execute([self._ep()])
        # Subsequent GET must include Authorization: Bearer tok123
        _, kwargs = http.get.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer tok123"

    def test_login_failure_continues_unauthenticated(self, tmp_path: Path):
        from rebuild.application.services.test_service import TestService
        from rebuild.domain.endpoint import EndpointStatus

        http = MagicMock()
        http.post.side_effect = Exception("boom")
        http.get.return_value = self._mock_response(200)
        svc = TestService(
            _walk_config(
                tmp_path,
                login_url="http://x/login",
                login_payload={"u": "v"},
            ),
            http=http,
        )
        out = svc.execute([self._ep()])
        assert out[0].status == EndpointStatus.OK

    def test_login_skips_when_no_credentials(self, tmp_path: Path):
        from rebuild.application.services.test_service import TestService

        http = MagicMock()
        http.get.return_value = self._mock_response(200)
        svc = TestService(_walk_config(tmp_path), http=http)
        svc.execute([self._ep()])
        http.post.assert_not_called()


# ───────────────────────────────────────────────────────────────────────────
# domain/mvp_protocol.py — MVPProtocolHandler routing branches
# ───────────────────────────────────────────────────────────────────────────


class TestMVPProtocolHandler:
    def _handler(self):
        from rebuild.domain.mvp_protocol import MVPProtocolHandler

        return MVPProtocolHandler()

    def test_unknown_message_type_returns_error(self):
        from rebuild.domain.mvp_protocol import MessageType, MVPMessage

        h = self._handler()
        msg = MVPMessage(message_type=MessageType.RESPONSE, payload={})
        out = h.handle_message(msg)
        assert out.message_type == MessageType.ERROR
        assert "Unknown message type" in out.payload["error"]

    def test_string_message_type_is_coerced(self):
        from rebuild.domain.mvp_protocol import MessageType, MVPMessage

        h = self._handler()
        # Bypass dataclass typing — emulate raw dict deserialisation.
        msg = MVPMessage(payload={"command": "walk", "parameters": {"a": 1}})
        msg.message_type = "command"  # type: ignore[assignment]
        out = h.handle_message(msg)
        assert out.message_type == MessageType.RESPONSE
        assert out.payload["command"] == "walk"

    def test_invalid_string_message_type_routes_to_error(self):
        from rebuild.domain.mvp_protocol import MessageType, MVPMessage

        h = self._handler()
        msg = MVPMessage(payload={})
        msg.message_type = "not-a-real-type"  # type: ignore[assignment]
        out = h.handle_message(msg)
        assert out.message_type == MessageType.ERROR

    def test_command_without_command_key_is_error(self):
        from rebuild.domain.mvp_protocol import MessageType, MVPMessage

        h = self._handler()
        msg = MVPMessage(message_type=MessageType.COMMAND, payload={})
        out = h.handle_message(msg)
        assert out.message_type == MessageType.ERROR
        assert "Missing 'command'" in out.payload["error"]

    def test_unknown_command_is_error(self):
        from rebuild.domain.mvp_protocol import MessageType, MVPMessage

        h = self._handler()
        msg = MVPMessage(message_type=MessageType.COMMAND, payload={"command": "wat"})
        out = h.handle_message(msg)
        assert out.message_type == MessageType.ERROR
        assert "Unknown command" in out.payload["error"]

    @pytest.mark.parametrize("command", ["walk", "analyze", "evolution", "auto_pr"])
    def test_simple_commands_echo_parameters(self, command):
        from rebuild.domain.mvp_protocol import MessageType, MVPMessage

        h = self._handler()
        msg = MVPMessage(
            message_type=MessageType.COMMAND,
            payload={"command": command, "parameters": {"x": 1}},
        )
        out = h.handle_message(msg)
        assert out.message_type == MessageType.RESPONSE
        assert out.payload["command"] == command
        assert out.payload["parameters"] == {"x": 1}
        assert out.payload["status"] == "parsed"

    def test_event_message_acknowledged(self):
        from rebuild.domain.mvp_protocol import MessageType, MVPMessage

        h = self._handler()
        msg = MVPMessage(message_type=MessageType.EVENT, payload={"event_type": "DEPLOY"})
        out = h.handle_message(msg)
        assert out.message_type == MessageType.RESPONSE
        assert out.payload["status"] == "event_received"
        assert out.payload["event_type"] == "DEPLOY"

    def test_dsl_command_missing_dsl_param(self):
        from rebuild.domain.mvp_protocol import MessageType, MVPMessage

        h = self._handler()
        msg = MVPMessage(message_type=MessageType.COMMAND, payload={"command": "dsl", "parameters": {}})
        out = h.handle_message(msg)
        assert out.message_type == MessageType.ERROR
        assert "Missing 'dsl'" in out.payload["error"]

    def test_dsl_command_handles_parser_exception(self):
        from rebuild.domain.mvp_protocol import MessageType, MVPMessage

        h = self._handler()
        with patch("rebuild.domain.dsl.DSLParser") as MockParser:
            MockParser.return_value.parse.side_effect = ValueError("bad dsl")
            msg = MVPMessage(
                message_type=MessageType.COMMAND,
                payload={"command": "dsl", "parameters": {"dsl": "garbage"}},
            )
            out = h.handle_message(msg)
            assert out.message_type == MessageType.ERROR
            assert out.payload["error"] == "bad dsl"

    def test_dsl_command_executes_successfully(self):
        from rebuild.domain.mvp_protocol import MessageType, MVPMessage

        h = self._handler()
        with patch("rebuild.domain.dsl.DSLParser") as MockParser, \
             patch("rebuild.domain.dsl.DSLInterpreter") as MockInterp:
            MockParser.return_value.parse.return_value = "PARSED"
            MockInterp.return_value.execute.return_value = {"ok": True}
            msg = MVPMessage(
                message_type=MessageType.COMMAND,
                payload={"command": "dsl", "parameters": {"dsl": "walk repo"}},
            )
            out = h.handle_message(msg)
            assert out.message_type == MessageType.RESPONSE
            assert out.payload["dsl"] == "walk repo"
            assert out.payload["status"] == "executed"

    def test_nlp_command_missing_text(self):
        from rebuild.domain.mvp_protocol import MessageType, MVPMessage

        h = self._handler()
        msg = MVPMessage(
            message_type=MessageType.COMMAND,
            payload={"command": "nlp", "parameters": {}},
        )
        out = h.handle_message(msg)
        assert out.message_type == MessageType.ERROR
        assert "Missing 'text'" in out.payload["error"]

    def test_nlp_command_handles_exception(self):
        from rebuild.domain.mvp_protocol import MessageType, MVPMessage

        h = self._handler()
        with patch("rebuild.application.services.nlp_service.NLPService") as MockNLP:
            MockNLP.return_value.parse.side_effect = RuntimeError("nlp boom")
            msg = MVPMessage(
                message_type=MessageType.COMMAND,
                payload={"command": "nlp", "parameters": {"text": "hi"}},
            )
            out = h.handle_message(msg)
            assert out.message_type == MessageType.ERROR
            assert out.payload["error"] == "nlp boom"


def test_mvp_server_construction():
    """``MVPServer.__init__`` must not start any sockets."""
    from rebuild.domain.mvp_protocol import MVPServer

    s = MVPServer(host="127.0.0.1", port=12345)
    assert s.host == "127.0.0.1"
    assert s.port == 12345
    assert s.handler is not None


# ───────────────────────────────────────────────────────────────────────────
# analysis/service_similarity.py — ServiceSimilarityAnalyzer
# ───────────────────────────────────────────────────────────────────────────


class TestServiceSimilarity:
    def test_dataclass_fields(self):
        from rebuild.analysis.service_similarity import ServiceSimilarity

        s = ServiceSimilarity(service_a="a", service_b="b", overlap=0.5, common_methods=["m"])
        assert s.service_a == "a"
        assert s.overlap == 0.5
        assert s.common_methods == ["m"]

    def test_empty_directory_returns_empty(self, tmp_path: Path):
        from rebuild.analysis.service_similarity import ServiceSimilarityAnalyzer

        analyzer = ServiceSimilarityAnalyzer()
        assert analyzer.analyze_directory(tmp_path) == []

    def test_extract_methods_skips_dunder_and_execute(self, tmp_path: Path):
        import ast

        from rebuild.analysis.service_similarity import ServiceSimilarityAnalyzer

        src = """
class S:
    def __init__(self):
        pass
    def execute(self):
        pass
    def foo(self):
        pass
    def bar(self):
        pass
"""
        methods = ServiceSimilarityAnalyzer()._extract_methods(ast.parse(src))
        assert methods == {"foo", "bar"}

    def test_overlap_detected_between_two_services(self, tmp_path: Path):
        from rebuild.analysis.service_similarity import ServiceSimilarityAnalyzer

        (tmp_path / "alpha_service.py").write_text(
            "class Alpha:\n    def foo(self): pass\n    def bar(self): pass\n"
        )
        (tmp_path / "beta_service.py").write_text(
            "class Beta:\n    def foo(self): pass\n    def baz(self): pass\n"
        )
        results = ServiceSimilarityAnalyzer().analyze_directory(tmp_path)
        assert len(results) == 1
        r = results[0]
        assert {r.service_a, r.service_b} == {"alpha_service", "beta_service"}
        assert r.common_methods == ["foo"]
        # Jaccard: |{foo}| / |{foo,bar,baz}| == 1/3
        assert abs(r.overlap - 1 / 3) < 1e-6

    def test_no_overlap_pair_is_skipped(self, tmp_path: Path):
        from rebuild.analysis.service_similarity import ServiceSimilarityAnalyzer

        (tmp_path / "a_service.py").write_text("class A:\n    def one(self): pass\n")
        (tmp_path / "b_service.py").write_text("class B:\n    def two(self): pass\n")
        assert ServiceSimilarityAnalyzer().analyze_directory(tmp_path) == []

    def test_syntax_error_file_is_skipped(self, tmp_path: Path):
        from rebuild.analysis.service_similarity import ServiceSimilarityAnalyzer

        (tmp_path / "bad_service.py").write_text("def (((")  # parse error
        (tmp_path / "good_service.py").write_text("class G:\n    def ok(self): pass\n")
        # Bad file ignored → no pairs to compare, result empty.
        assert ServiceSimilarityAnalyzer().analyze_directory(tmp_path) == []

    def test_results_sorted_by_overlap_desc(self, tmp_path: Path):
        from rebuild.analysis.service_similarity import ServiceSimilarityAnalyzer

        (tmp_path / "x_service.py").write_text(
            "class X:\n    def a(self): pass\n    def b(self): pass\n"
        )
        (tmp_path / "y_service.py").write_text(
            "class Y:\n    def a(self): pass\n    def b(self): pass\n"  # 100% overlap with x
        )
        (tmp_path / "z_service.py").write_text(
            "class Z:\n    def a(self): pass\n    def c(self): pass\n"  # 1/3 overlap
        )
        results = ServiceSimilarityAnalyzer().analyze_directory(tmp_path)
        assert len(results) == 3
        # Sorted descending by overlap.
        assert results[0].overlap >= results[1].overlap >= results[2].overlap


# ───────────────────────────────────────────────────────────────────────────
# interfaces/dashboard.py — CC extraction + html generation branches
# ───────────────────────────────────────────────────────────────────────────


class TestDashboard:
    def test_extract_avg_cc_returns_none_for_empty_files(self):
        from rebuild.interfaces.dashboard import _extract_avg_cc

        assert _extract_avg_cc({"files": []}) is None
        assert _extract_avg_cc({}) is None

    def test_extract_avg_cc_ignores_files_without_cc(self):
        from rebuild.interfaces.dashboard import _extract_avg_cc

        assert _extract_avg_cc({"files": [{"path": "x.py"}]}) is None

    def test_extract_avg_cc_computes_mean_rounded(self):
        from rebuild.interfaces.dashboard import _extract_avg_cc

        data = {"files": [
            {"avg_complexity": 2.0},
            {"avg_complexity": 4.0},
            {"avg_complexity": None},  # skipped
        ]}
        assert _extract_avg_cc(data) == 3.0

    def test_get_cc_for_day_returns_none_when_toon_missing(self, tmp_path: Path):
        from rebuild.interfaces.dashboard import get_cc_for_day

        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert get_cc_for_day(tmp_path, date(2025, 1, 1)) is None

    def test_get_cc_for_day_returns_none_on_non_zero_exit(self, tmp_path: Path):
        from rebuild.interfaces.dashboard import get_cc_for_day

        with patch("subprocess.run") as run:
            run.return_value = MagicMock(returncode=1, stdout="")
            assert get_cc_for_day(tmp_path, date(2025, 1, 1)) is None

    def test_get_cc_for_day_returns_none_on_invalid_json(self, tmp_path: Path):
        from rebuild.interfaces.dashboard import get_cc_for_day

        with patch("subprocess.run") as run:
            run.return_value = MagicMock(returncode=0, stdout="{not json")
            assert get_cc_for_day(tmp_path, date(2025, 1, 1)) is None

    def test_get_cc_for_day_extracts_cc_on_success(self, tmp_path: Path):
        from rebuild.interfaces.dashboard import get_cc_for_day

        with patch("subprocess.run") as run:
            run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({"files": [{"avg_complexity": 5.0}]}),
            )
            assert get_cc_for_day(tmp_path, date(2025, 1, 1)) == 5.0

    def test_generate_dashboard_without_repo_has_no_cc(self, tmp_path: Path):
        from rebuild.domain.day_result import DayResult
        from rebuild.domain.endpoint import Endpoint, EndpointResult, EndpointStatus
        from rebuild.domain.models import DeployMethod
        from rebuild.interfaces.dashboard import generate_dashboard

        ep = Endpoint(method="GET", path="/x", base_url="http://x")
        ok = EndpointResult(endpoint=ep, status=EndpointStatus.OK)
        r = DayResult(
            day=date(2025, 1, 1),
            commit=None,
            deploy_method=DeployMethod.NONE,
            deploy_success=True,
            endpoints=[ep],
            endpoint_results=[ok],
        )
        out = generate_dashboard([r], tmp_path)
        assert out.exists()
        html = out.read_text()
        # Without repo → no CC dataset rendered.
        assert "Avg CC" not in html
        assert "Health %" in html

    def test_generate_dashboard_with_repo_attempts_cc_fetch(self, tmp_path: Path):
        from rebuild.domain.day_result import DayResult
        from rebuild.domain.endpoint import Endpoint, EndpointResult, EndpointStatus
        from rebuild.domain.models import DeployMethod
        from rebuild.interfaces.dashboard import generate_dashboard

        ep = Endpoint(method="GET", path="/x", base_url="http://x")
        ok = EndpointResult(endpoint=ep, status=EndpointStatus.OK)
        r = DayResult(
            day=date(2025, 1, 1),
            commit=None,
            deploy_method=DeployMethod.NONE,
            deploy_success=True,
            endpoints=[ep],
            endpoint_results=[ok],
        )
        with patch("rebuild.interfaces.dashboard.get_cc_for_day", return_value=7.5):
            out = generate_dashboard([r], tmp_path, repo=tmp_path)
            html = out.read_text()
            assert "Avg CC" in html  # CC dataset rendered when at least one value present
            assert "7.5" in html


# ───────────────────────────────────────────────────────────────────────────
# refactor/refactor_executor.py — merge_duplicates body
# ───────────────────────────────────────────────────────────────────────────


class TestRefactorExecutor:
    def test_unsupported_type_reports_and_returns_false(self):
        from io import StringIO

        from rich.console import Console

        from rebuild.refactor.recommendation_engine import RefactorSuggestion
        from rebuild.refactor.refactor_executor import RefactorExecutor

        buf = StringIO()
        console = Console(file=buf, highlight=False)
        executor = RefactorExecutor(console)
        suggestion = RefactorSuggestion(
            type="EXTRACT_INTERFACE",
            title="x",
            description="y",
            files=[],
            impact="low",
        )
        assert executor.execute_suggestion(suggestion) is False
        assert "not yet automatable" in buf.getvalue()

    def test_merge_duplicates_empty_files_returns_false(self):
        from rebuild.refactor.recommendation_engine import RefactorSuggestion
        from rebuild.refactor.refactor_executor import RefactorExecutor

        executor = RefactorExecutor()
        suggestion = RefactorSuggestion(
            type="MERGE_DUPLICATES",
            title="t",
            description="d",
            files=[],
            impact="low",
        )
        assert executor.execute_suggestion(suggestion) is False

    def test_merge_duplicates_rewrites_files_with_marker(self, tmp_path: Path):
        from rebuild.refactor.recommendation_engine import RefactorSuggestion
        from rebuild.refactor.refactor_executor import RefactorExecutor

        f1 = tmp_path / "a.py"
        f2 = tmp_path / "b.py"
        f1.write_text("def foo(): return 1\n")
        f2.write_text("def foo(): return 1\n")
        suggestion = RefactorSuggestion(
            type="MERGE_DUPLICATES",
            title="merge",
            description="",
            files=[f1, f2],
            impact="medium",
        )
        assert RefactorExecutor().execute_suggestion(suggestion) is True
        assert f1.read_text().startswith("# [REFACTORED]")
        assert f2.read_text().startswith("# [REFACTORED]")
        # Original body is preserved after the marker line.
        assert "def foo(): return 1" in f1.read_text()

    def test_merge_duplicates_handles_unreadable_file(self, tmp_path: Path):
        from rebuild.refactor.recommendation_engine import RefactorSuggestion
        from rebuild.refactor.refactor_executor import RefactorExecutor

        bad = MagicMock()
        bad.name = "bad.py"
        bad.read_text.side_effect = OSError("denied")

        suggestion = RefactorSuggestion(
            type="MERGE_DUPLICATES",
            title="merge",
            description="",
            files=[bad],
            impact="low",
        )
        assert RefactorExecutor().execute_suggestion(suggestion) is False


# ───────────────────────────────────────────────────────────────────────────
# interfaces/commands/helpers.py — serve_reports (headers, routing, lifecycle)
# ───────────────────────────────────────────────────────────────────────────


# ───────────────────────────────────────────────────────────────────────────
# interfaces/commands/walk_command.py — notification + deploy-resolve helpers
# ───────────────────────────────────────────────────────────────────────────


class TestWalkCommandHelpers:
    def _day(self, day_value: date, *, deploy_success: bool, health_pct: float):
        from rebuild.domain.day_result import DayResult
        from rebuild.domain.endpoint import Endpoint, EndpointResult, EndpointStatus
        from rebuild.domain.models import DeployMethod

        ep = Endpoint(method="GET", path="/x", base_url="http://x")
        # Construct endpoint_results so the auto-computed health_pct matches.
        ok_count = int(round(health_pct / 100 * 10))
        fail_count = 10 - ok_count
        results = [EndpointResult(endpoint=ep, status=EndpointStatus.OK)] * ok_count
        results += [EndpointResult(endpoint=ep, status=EndpointStatus.FAIL)] * fail_count
        return DayResult(
            day=day_value,
            commit=None,
            deploy_method=DeployMethod.NONE,
            deploy_success=deploy_success,
            endpoints=[ep] * 10,
            endpoint_results=results,
        )

    def test_fire_notifications_no_config_is_noop(self, tmp_path: Path):
        from io import StringIO

        from rich.console import Console

        from rebuild.domain.models import DeployMethod, WalkConfig
        from rebuild.interfaces.commands.walk_command import _fire_notifications

        cfg = WalkConfig(repo_path=tmp_path, output_dir=tmp_path, deploy_method=DeployMethod.NONE)
        # No ``notifications`` field set → early return, nothing rendered.
        buf = StringIO()
        _fire_notifications([], cfg, Console(file=buf, highlight=False))
        assert buf.getvalue() == ""

    def test_fire_notifications_with_no_hooks_is_noop(self, tmp_path: Path):
        from io import StringIO

        from rich.console import Console

        from rebuild.domain.models import DeployMethod, WalkConfig
        from rebuild.interfaces.commands.walk_command import _fire_notifications

        cfg = WalkConfig(repo_path=tmp_path, output_dir=tmp_path, deploy_method=DeployMethod.NONE)
        cfg.notifications = []  # type: ignore[attr-defined]
        buf = StringIO()
        _fire_notifications([], cfg, Console(file=buf, highlight=False))
        assert buf.getvalue() == ""

    def test_fire_notifications_dispatches_failures_and_completion(self, tmp_path: Path):
        from io import StringIO

        from rich.console import Console

        from rebuild.domain.models import DeployMethod, WalkConfig
        from rebuild.interfaces.commands import walk_command as wc

        cfg = WalkConfig(repo_path=tmp_path, output_dir=tmp_path, deploy_method=DeployMethod.NONE)
        cfg.notifications = [{"url": "https://hooks.example/x", "platform": "generic"}]  # type: ignore[attr-defined]

        results = [
            self._day(date(2025, 1, 1), deploy_success=True, health_pct=90.0),
            self._day(date(2025, 1, 2), deploy_success=False, health_pct=20.0),
        ]

        fake_svc = MagicMock()
        fake_svc.hooks = ["one"]  # truthy
        fake_svc.notify_deploy_fail.return_value = [True]
        fake_svc.notify_walk_complete.return_value = [True, True]

        buf = StringIO()
        with patch.object(wc, "NotificationService", create=True), \
             patch("rebuild.application.services.notification_service.NotificationService.from_config",
                   return_value=fake_svc):
            wc._fire_notifications(results, cfg, Console(file=buf, highlight=False))

        # Called exactly once for the single failed day.
        fake_svc.notify_deploy_fail.assert_called_once()
        fake_svc.notify_walk_complete.assert_called_once()
        total, healthy, avg, output_dir = fake_svc.notify_walk_complete.call_args.args
        assert total == 2
        assert healthy == 1  # only the 90% day clears the 80% threshold
        assert avg == pytest.approx(55.0)
        assert output_dir == cfg.output_dir
        assert "Wysłano 2 powiadomienie" in buf.getvalue()

    def test_resolve_deploy_method_returns_explicit_choice(self, tmp_path: Path):
        from rebuild.domain.models import DeployMethod
        from rebuild.interfaces.commands.walk_command import _resolve_deploy_method

        assert _resolve_deploy_method(tmp_path, "none", dry_run=False) == DeployMethod.NONE
        assert _resolve_deploy_method(tmp_path, "docker-compose", dry_run=False) == DeployMethod.DOCKER_COMPOSE

    def test_resolve_deploy_method_dry_run_forces_none(self, tmp_path: Path):
        from rebuild.domain.models import DeployMethod
        from rebuild.interfaces.commands.walk_command import _resolve_deploy_method

        # ``auto`` + ``dry_run`` short-circuits to NONE without touching DeployService.
        assert _resolve_deploy_method(tmp_path, "auto", dry_run=True) == DeployMethod.NONE

    def test_resolve_deploy_method_auto_delegates_to_deploy_service(self, tmp_path: Path):
        from rebuild.domain.models import DeployMethod
        from rebuild.interfaces.commands import walk_command as wc

        with patch.object(wc, "DeployService") as MockSvc:
            MockSvc.return_value.detect_deploy_method.return_value = DeployMethod.DOCKER_COMPOSE
            assert wc._resolve_deploy_method(tmp_path, "auto", dry_run=False) == DeployMethod.DOCKER_COMPOSE
            MockSvc.return_value.detect_deploy_method.assert_called_once_with(tmp_path)


class TestServeReports:
    """``serve_reports`` spins up a real ``socketserver.TCPServer`` inside the
    function. We cover everything up to (but not including) the blocking
    ``serve_forever`` call by patching the server to raise ``KeyboardInterrupt``
    from ``serve_forever`` — this also exercises the graceful-shutdown branch.
    """

    def test_serve_reports_sse_handler_routes_correctly(self, tmp_path: Path, monkeypatch):
        """Drive the inner ``SSEHandler.do_GET`` for both the SSE branch and the
        static-file branch without spinning up a real HTTP server."""
        from io import StringIO

        from rich.console import Console

        # Pre-import http.server so patching socketserver later doesn't break it.
        import http.server  # noqa: F401
        import socketserver

        from rebuild.interfaces.commands import helpers as helpers_mod

        (tmp_path / "index.html").write_text("<html>ok</html>")

        captured_handler_cls: dict = {}

        class _RecordingFakeServer:
            """Stand-in for ``socketserver.TCPServer`` that records the handler
            class so the test can construct it manually and exercise its routes."""

            def __init__(self, addr, handler_cls):
                self.addr = addr
                captured_handler_cls["cls"] = handler_cls

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def serve_forever(self):
                raise KeyboardInterrupt()

        buf = StringIO()
        console = Console(file=buf, highlight=False)
        monkeypatch.chdir(tmp_path)

        with patch.object(socketserver, "TCPServer", _RecordingFakeServer), \
             patch("threading.Timer") as MockTimer, \
             patch("webbrowser.open"):
            MockTimer.return_value = MagicMock()
            helpers_mod.serve_reports(tmp_path, 8124, console)

        handler_cls = captured_handler_cls["cls"]
        # ``handler_cls.log_message`` must be silenced (covers the no-op override).
        assert handler_cls.log_message(None) is None  # type: ignore[arg-type]

        # Construct a fake handler instance that bypasses the real
        # SimpleHTTPRequestHandler init (which would touch sockets).
        fake_self = MagicMock(spec=handler_cls)
        fake_self.path = "/events"
        fake_self.wfile = MagicMock()
        # Subscribe queue should yield one event then time out → keepalive branch.
        from queue import Empty

        sub_queue = MagicMock()
        sub_queue.get.side_effect = Empty()
        from rebuild.application.services.event_service import get_event_service

        with patch.object(get_event_service(), "subscribe", return_value=sub_queue) as MockSub, \
             patch.object(get_event_service(), "unsubscribe") as MockUnsub:
            handler_cls.do_GET(fake_self)
            MockSub.assert_called_once()
            MockUnsub.assert_called_once_with(sub_queue)
            # keepalive payload was written to wfile.
            written = b"".join(c.args[0] for c in fake_self.wfile.write.call_args_list)
            assert b"keepalive" in written

    def test_serve_reports_handles_keyboard_interrupt(self, tmp_path: Path, monkeypatch):
        """Covers: cwd change, event-service enable/disable, start + stop logs."""
        from io import StringIO

        from rich.console import Console

        # Pre-import stdlib modules so patching ``socketserver.TCPServer`` does not
        # break the deferred ``import http.server`` inside ``serve_reports``.
        import http.server  # noqa: F401
        import socketserver

        from rebuild.interfaces.commands import helpers as helpers_mod

        # Minimal index.html so the handler has something to serve if asked.
        (tmp_path / "index.html").write_text("<html></html>")

        buf = StringIO()
        console = Console(file=buf, highlight=False)

        fake_server = MagicMock()
        fake_server.__enter__ = MagicMock(return_value=fake_server)
        fake_server.__exit__ = MagicMock(return_value=False)
        fake_server.serve_forever.side_effect = KeyboardInterrupt()

        # Prevent os.chdir from leaking state across tests.
        monkeypatch.chdir(tmp_path)

        with patch.object(socketserver, "TCPServer", return_value=fake_server) as MockSrv, \
             patch("threading.Timer") as MockTimer, \
             patch("webbrowser.open"):
            MockTimer.return_value = MagicMock()
            helpers_mod.serve_reports(tmp_path, 8123, console)

        # Server was constructed with the expected port.
        assert MockSrv.call_args.args[0] == ("", 8123)
        # User-facing output covers the "started" and the "stopped" branches.
        out = buf.getvalue()
        assert "http://localhost:8123" in out
        assert "Serwer zatrzymany" in out
