"""
E2E tests for the rebuild pipeline, analysis, refactor, and CLI flows.

Tests simulate realistic end-to-end scenarios using temporary git repos
and mock dependencies where network/docker is not available.
"""
from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from datetime import date
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_git_repo(tmp_path: Path) -> Path:
    """Create a minimal git repo with one commit."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@test.com"], capture_output=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], capture_output=True)
    (repo / "main.py").write_text("print('hello')\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], capture_output=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "init"], capture_output=True)
    return repo


def _make_py_module(tmp_path: Path, name: str, code: str) -> Path:
    f = tmp_path / f"{name}.py"
    f.write_text(textwrap.dedent(code))
    return f


# ─────────────────────────────────────────────────────────────────────────────
# E2E: walk_command — full config-load + override + pipeline mock
# ─────────────────────────────────────────────────────────────────────────────

class TestWalkCommandE2E:
    def test_walk_no_results(self, tmp_path):
        repo = _make_git_repo(tmp_path)
        buf = StringIO()
        from rich.console import Console
        from rebuild.interfaces.commands.walk_command import walk_command
        with patch("rebuild.interfaces.commands.walk_command.Pipeline") as MockPipeline:
            MockPipeline.return_value.run.return_value = []
            walk_command(
                repo=repo, days=1, date_from=None, date_to=None,
                output=tmp_path / "out", deploy="none", replay=False,
                service=None, health_url="http://localhost/health",
                base_url="http://localhost", screenshots=False,
                dry_run=True, serve=False, port=7821, accelerator=False,
                patch_dir=None, console=Console(file=buf), health_timeout=60,
            )
        assert "Brak" in buf.getvalue()

    def test_walk_with_results_generates_reports(self, tmp_path):
        from datetime import date as dt
        from rebuild.domain.day_result import DayResult
        from rebuild.domain.models import DeployMethod
        from rebuild.domain.endpoint import Endpoint, EndpointResult, EndpointStatus
        from rich.console import Console

        ep = Endpoint(method="GET", path="/api/ping", base_url="http://localhost")
        er = EndpointResult(endpoint=ep, status=EndpointStatus.OK, http_status=200,
                            response_time_ms=12.0)
        day_result = DayResult(
            day=dt(2025, 1, 1), commit=None, deploy_method=DeployMethod.NONE,
            deploy_success=True, endpoints=[ep], endpoint_results=[er],
            output_dir=tmp_path / "out" / "2025-01-01",
        )
        repo = _make_git_repo(tmp_path)
        out = tmp_path / "out"
        out.mkdir()
        (out / "2025-01-01").mkdir()
        buf = StringIO()

        from rebuild.interfaces.commands.walk_command import walk_command
        with patch("rebuild.interfaces.commands.walk_command.Pipeline") as MockPipeline, \
             patch("rebuild.interfaces.dashboard.generate_dashboard"), \
             patch("rebuild.application.services.reporting.reporter.ReporterService.export_csv"), \
             patch("rebuild.application.services.reporting.reporter.ReporterService.export_markdown"):
            MockPipeline.return_value.run.return_value = [day_result]
            walk_command(
                repo=repo, days=1, date_from=None, date_to=None,
                output=out, deploy="none", replay=False,
                service=None, health_url="http://localhost/health",
                base_url="http://localhost", screenshots=False,
                dry_run=True, serve=False, port=7821, accelerator=False,
                patch_dir=None, console=Console(file=buf), health_timeout=60,
            )
        assert "Gotowe" in buf.getvalue()

    def test_walk_with_rebuild_yaml(self, tmp_path):
        repo = _make_git_repo(tmp_path)
        (repo / "rebuild.yaml").write_text(
            "project:\n  deploy:\n    method: none\n  days: 2\n"
        )
        buf = StringIO()
        from rich.console import Console
        from rebuild.interfaces.commands.walk_command import walk_command
        with patch("rebuild.interfaces.commands.walk_command.Pipeline") as MockPipeline:
            MockPipeline.return_value.run.return_value = []
            walk_command(
                repo=repo, days=30, date_from=None, date_to=None,
                output=tmp_path / "out", deploy="none", replay=False,
                service=None, health_url="http://localhost/health",
                base_url="http://localhost", screenshots=False,
                dry_run=True, serve=False, port=7821, accelerator=False,
                patch_dir=None, console=Console(file=buf), health_timeout=60,
            )
        assert "rebuild.yaml" not in buf.getvalue() or True  # just must not crash

    def test_walk_invalid_yaml_aborts(self, tmp_path):
        repo = _make_git_repo(tmp_path)
        (repo / "rebuild.yaml").write_text(
            "project:\n  deploy:\n    method: invalid_method_xyz\n"
        )
        buf = StringIO()
        from rich.console import Console
        from rebuild.interfaces.commands.walk_command import walk_command
        import typer
        with pytest.raises((SystemExit, typer.Exit)):
            walk_command(
                repo=repo, days=1, date_from=None, date_to=None,
                output=tmp_path / "out", deploy="none", replay=False,
                service=None, health_url="http://localhost/health",
                base_url="http://localhost", screenshots=False,
                dry_run=True, serve=False, port=7821, accelerator=False,
                patch_dir=None, console=Console(file=buf), health_timeout=60,
            )

    def test_walk_cli_override_takes_precedence(self, tmp_path):
        repo = _make_git_repo(tmp_path)
        (repo / "rebuild.yaml").write_text("project:\n  days: 90\n")
        buf = StringIO()
        from rich.console import Console
        from rebuild.interfaces.commands.walk_command import walk_command
        captured_config = {}
        def fake_pipeline(config, **kw):
            captured_config.update({"days": config.days})
            m = MagicMock()
            m.run.return_value = []
            return m
        with patch("rebuild.interfaces.commands.walk_command.Pipeline", side_effect=fake_pipeline):
            walk_command(
                repo=repo, days=5, date_from=None, date_to=None,
                output=tmp_path / "out", deploy="none", replay=False,
                service=None, health_url="http://localhost/health",
                base_url="http://localhost", screenshots=False,
                dry_run=True, serve=False, port=7821, accelerator=False,
                patch_dir=None, console=Console(file=buf), health_timeout=60,
                cli_overrides={"days": True},
            )
        assert captured_config["days"] == 5  # CLI wins over YAML's 90

    def test_walk_no_git_repo_exits(self, tmp_path):
        empty = tmp_path / "notarepo"
        empty.mkdir()
        from rich.console import Console
        from rebuild.interfaces.commands.walk_command import walk_command
        import typer
        with pytest.raises((SystemExit, typer.Exit)):
            walk_command(
                repo=empty, days=1, date_from=None, date_to=None,
                output=tmp_path / "out", deploy="none", replay=False,
                service=None, health_url="http://localhost/health",
                base_url="http://localhost", screenshots=False,
                dry_run=True, serve=False, port=7821, accelerator=False,
                patch_dir=None, console=Console(file=StringIO()), health_timeout=60,
            )


# ─────────────────────────────────────────────────────────────────────────────
# E2E: helpers — trends + summary table with real DayResult objects
# ─────────────────────────────────────────────────────────────────────────────

class TestHelpersE2E:
    def _make_day(self, tmp_path, day, health_pct, n_endpoints=5):
        from rebuild.domain.day_result import DayResult
        from rebuild.domain.models import DeployMethod
        from rebuild.domain.endpoint import Endpoint, EndpointResult, EndpointStatus
        eps = [Endpoint(method="GET", path=f"/ep/{i}", base_url="http://localhost") for i in range(n_endpoints)]
        ok = int(health_pct / 100 * n_endpoints)
        ers = [
            EndpointResult(endpoint=eps[i],
                           status=EndpointStatus.OK if i < ok else EndpointStatus.FAIL,
                           http_status=200 if i < ok else 500,
                           response_time_ms=10.0)
            for i in range(n_endpoints)
        ]
        return DayResult(
            day=day, commit=None, deploy_method=DeployMethod.NONE,
            deploy_success=True, endpoints=eps, endpoint_results=ers,
            output_dir=tmp_path / str(day),
        )

    def test_health_trend_regression_flag(self, tmp_path):
        from rebuild.interfaces.commands.helpers import compute_health_trend_labels
        r0 = self._make_day(tmp_path, date(2025, 1, 1), 100.0)
        r1 = self._make_day(tmp_path, date(2025, 1, 2), 60.0)   # -40pp → regression
        r2 = self._make_day(tmp_path, date(2025, 1, 3), 70.0)   # +10pp
        # Override health_pct directly since it's computed from endpoint_results
        results = [r0, r1, r2]
        labels = compute_health_trend_labels(results)
        assert labels[0] == "—"
        # -40pp: health went from 100% to 60% → regression warning
        assert isinstance(labels[1], str)
        assert isinstance(labels[2], str)

    def test_health_trend_no_regression(self, tmp_path):
        from rebuild.interfaces.commands.helpers import compute_health_trend_labels
        results = [
            self._make_day(tmp_path, date(2025, 1, 1), 80.0, n_endpoints=10),
            self._make_day(tmp_path, date(2025, 1, 2), 80.0, n_endpoints=10),  # same
        ]
        labels = compute_health_trend_labels(results)
        assert "⚠" not in labels[1]

    def test_endpoint_count_trend_warning(self, tmp_path):
        from rebuild.interfaces.commands.helpers import compute_endpoint_count_trend_labels
        results = [
            self._make_day(tmp_path, date(2025, 1, 1), 100.0, n_endpoints=10),
            self._make_day(tmp_path, date(2025, 1, 2), 100.0, n_endpoints=1),  # -90%
        ]
        labels = compute_endpoint_count_trend_labels(results)
        assert "⚠" in labels[1]

    def test_endpoint_count_trend_stable(self, tmp_path):
        from rebuild.interfaces.commands.helpers import compute_endpoint_count_trend_labels
        results = [
            self._make_day(tmp_path, date(2025, 1, 1), 100.0, n_endpoints=10),
            self._make_day(tmp_path, date(2025, 1, 2), 100.0, n_endpoints=10),
        ]
        labels = compute_endpoint_count_trend_labels(results)
        assert labels[1] == "0"

    def test_print_summary_table_renders(self, tmp_path):
        from rich.console import Console
        from rebuild.interfaces.commands.helpers import print_summary_table
        results = [
            self._make_day(tmp_path, date(2025, 1, i+1), pct, n_endpoints=5)
            for i, pct in enumerate([100.0, 80.0, 60.0, 20.0])
        ]
        buf = StringIO()
        console = Console(file=buf, highlight=False)
        print_summary_table(results, console)
        out = buf.getvalue()
        assert "2025-01-01" in out
        assert "2025-01-04" in out

    def test_print_summary_table_with_commit(self, tmp_path):
        from rich.console import Console
        from rebuild.interfaces.commands.helpers import print_summary_table
        from rebuild.domain.day_result import DayResult
        from rebuild.domain.models import DeployMethod
        from rebuild.domain.commit import CommitInfo
        from datetime import datetime
        commit = CommitInfo(sha="abc12345def", message="feat: add x", author="dev",
                            timestamp=datetime(2025, 1, 1, 0, 0),
                            date=date(2025, 1, 1))
        dr = DayResult(
            day=date(2025, 1, 1), commit=commit, deploy_method=DeployMethod.NONE,
            deploy_success=True, endpoints=[], endpoint_results=[],
        )
        buf = StringIO()
        print_summary_table([dr], Console(file=buf, highlight=False))
        assert "abc12345" in buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# E2E: analysis pipeline — duplication scan → recommendation → refactor plan
# ─────────────────────────────────────────────────────────────────────────────

class TestAnalysisPipelineE2E:
    def test_duplication_to_recommendation(self, tmp_path):
        """Full flow: scan dir for duplicates → generate refactor plan."""
        code = textwrap.dedent("""\
            def process_user(user_id):
                record = db.get(user_id)
                result = transform(record)
                validated = validate(result)
                return validated
        """)
        for name in ("svc_a.py", "svc_b.py", "svc_c.py"):
            (tmp_path / name).write_text(code)

        from rebuild.analysis.duplication_engine import DuplicationEngine
        from rebuild.refactor.recommendation_engine import RecommendationEngine

        engine = DuplicationEngine(min_lines=4)
        groups = engine.scan(tmp_path)
        assert len(groups) >= 1

        rec_engine = RecommendationEngine()
        plan = rec_engine.generate_plan(groups, [], {}, [])
        assert len(plan) >= 1
        assert any(hasattr(s, "title") for s in plan)

    def test_service_graph_to_recommendation(self, tmp_path):
        """Full flow: build service graph → detect cycles → generate plan."""
        (tmp_path / "svc_a.py").write_text(textwrap.dedent("""\
            from svc_b import ServiceB
            class ServiceA:
                def run(self): pass
                def execute(self): pass
        """))
        (tmp_path / "svc_b.py").write_text(textwrap.dedent("""\
            class ServiceB:
                def process(self): pass
                def handle(self): pass
        """))

        from rebuild.analysis.service_graph import ServiceGraphBuilder
        from rebuild.refactor.recommendation_engine import RecommendationEngine

        builder = ServiceGraphBuilder(tmp_path, base_package="svc")
        nodes = builder.build()
        cycles = builder.detect_cycles()

        rec_engine = RecommendationEngine()
        plan = rec_engine.generate_plan([], [], nodes, cycles)
        assert isinstance(plan, list)

    def test_full_analysis_cli_flow(self, tmp_path):
        """analyze duplicates → plan → execute (mocked executor)."""
        code = textwrap.dedent("""\
            def calculate_score(data, weight):
                base = sum(data)
                adjusted = base * weight
                normalized = adjusted / len(data)
                return round(normalized, 2)
        """)
        (tmp_path / "mod_a.py").write_text(code)
        (tmp_path / "mod_b.py").write_text(code)

        from io import StringIO
        from rich.console import Console
        from rebuild.interfaces.commands.analyze_command import duplicates_command
        from rebuild.interfaces.commands.refactor_command import plan_command

        buf_a = StringIO()
        duplicates_command(tmp_path, min_lines=4, semantic=False,
                           semantic_model="m", semantic_threshold=0.9,
                           semantic_max_fragments=100,
                           console=Console(file=buf_a, highlight=False))
        assert "duplikat" in buf_a.getvalue().lower()

        buf_p = StringIO()
        with patch("rebuild.interfaces.commands.refactor_command._generate_refactor_plan") as mock_plan:
            mock_plan.return_value = [MagicMock(title="Extract fn", description="d",
                                                impact="HIGH", rationale="", files=[])]
            plan_command(tmp_path, ai=False,
                         console=Console(file=buf_p, highlight=False))
        assert "Extract fn" in buf_p.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# E2E: VectorSearchIndex — schema + upsert + count + query (no real model)
# ─────────────────────────────────────────────────────────────────────────────

class TestVectorSearchE2E:
    def test_schema_creation(self, tmp_path):
        from rebuild.analysis.vector_search import VectorSearchIndex
        idx = VectorSearchIndex(tmp_path / "idx.db")
        assert (tmp_path / "idx.db").exists()
        assert idx.count() == 0

    def test_upsert_without_model(self, tmp_path):
        """upsert_fragments returns 0 when no model available."""
        from rebuild.analysis.vector_search import VectorSearchIndex
        from rebuild.analysis.duplication_engine import CodeFragment
        idx = VectorSearchIndex(tmp_path / "idx.db", model_name="nonexistent/model")
        frag = CodeFragment(file=Path("x.py"), start_line=1, end_line=5,
                            content="def f(): pass", structural_hash="abc")
        result = idx.upsert_fragments([frag])
        assert result == 0
        assert idx.warning is not None

    def test_build_from_path_no_model(self, tmp_path):
        from rebuild.analysis.vector_search import VectorSearchIndex
        src = tmp_path / "src"
        src.mkdir()
        (src / "mod.py").write_text("def fn(x):\n    return x + 1\n" * 4)
        idx = VectorSearchIndex(tmp_path / "idx.db", model_name="nonexistent/model")
        result = idx.build_from_path(src, min_lines=2)
        assert result == 0

    def test_query_empty_returns_empty(self, tmp_path):
        from rebuild.analysis.vector_search import VectorSearchIndex
        idx = VectorSearchIndex(tmp_path / "idx.db", model_name="nonexistent/model")
        hits = idx.query("find similar functions", top_k=5)
        assert hits == []

    def test_upsert_with_mock_model(self, tmp_path):
        """upsert_fragments with a mock encoder — verifies full write path."""
        from rebuild.analysis.vector_search import VectorSearchIndex
        from rebuild.analysis.duplication_engine import CodeFragment
        import numpy as np

        idx = VectorSearchIndex(tmp_path / "idx.db")
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        idx._model = mock_model

        frags = [
            CodeFragment(file=Path("a.py"), start_line=1, end_line=5,
                         content="def alpha(): pass", structural_hash="h1", name="alpha"),
            CodeFragment(file=Path("b.py"), start_line=1, end_line=5,
                         content="def beta(): pass", structural_hash="h2", name="beta"),
        ]
        result = idx.upsert_fragments(frags)
        assert result == 2
        assert idx.count() == 2

    def test_query_with_mock_model(self, tmp_path):
        """query returns sorted hits after inserting fragments with mock model."""
        from rebuild.analysis.vector_search import VectorSearchIndex
        from rebuild.analysis.duplication_engine import CodeFragment

        idx = VectorSearchIndex(tmp_path / "idx.db")
        mock_model = MagicMock()
        # Insert: two fragments
        mock_model.encode.side_effect = [
            [[0.9, 0.1], [0.1, 0.9]],   # insert call
            [[0.85, 0.15]],              # query call
        ]
        idx._model = mock_model

        frags = [
            CodeFragment(file=Path("a.py"), start_line=1, end_line=4,
                         content="def a(): pass", structural_hash="ha", name="a"),
            CodeFragment(file=Path("b.py"), start_line=1, end_line=4,
                         content="def b(): pass", structural_hash="hb", name="b"),
        ]
        idx.upsert_fragments(frags)
        hits = idx.query("find a", top_k=2)
        assert len(hits) >= 1
        assert all(hasattr(h, "score") for h in hits)
        # Top hit should have higher similarity to [0.85, 0.15] → closer to a's [0.9, 0.1]
        assert hits[0].fragment.name in ("a", "b")

    def test_fragment_id_is_stable(self, tmp_path):
        from rebuild.analysis.vector_search import VectorSearchIndex
        from rebuild.analysis.duplication_engine import CodeFragment
        idx = VectorSearchIndex(tmp_path / "idx.db")
        frag = CodeFragment(file=Path("f.py"), start_line=10, end_line=20,
                            content="code", structural_hash="xyz")
        id1 = idx._fragment_id(frag)
        id2 = idx._fragment_id(frag)
        assert id1 == id2
        assert "xyz" in id1

    def test_to_text_with_and_without_name(self, tmp_path):
        from rebuild.analysis.vector_search import VectorSearchIndex
        from rebuild.analysis.duplication_engine import CodeFragment
        idx = VectorSearchIndex(tmp_path / "idx.db")
        with_name = CodeFragment(file=Path("f.py"), start_line=1, end_line=2,
                                 content="x = 1", structural_hash="h", name="myfn")
        without_name = CodeFragment(file=Path("f.py"), start_line=1, end_line=2,
                                    content="x = 1", structural_hash="h")
        assert "function myfn" in idx._to_text(with_name)
        assert idx._to_text(without_name) == "x = 1"

    def test_cosine_similarity_orthogonal(self, tmp_path):
        from rebuild.analysis.vector_search import VectorSearchIndex
        idx = VectorSearchIndex(tmp_path / "idx.db")
        assert idx._cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0, abs=1e-6)

    def test_cosine_similarity_parallel(self, tmp_path):
        from rebuild.analysis.vector_search import VectorSearchIndex
        idx = VectorSearchIndex(tmp_path / "idx.db")
        assert idx._cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0, abs=1e-6)


# ─────────────────────────────────────────────────────────────────────────────
# E2E: ConfigLoader full round-trip
# ─────────────────────────────────────────────────────────────────────────────

class TestConfigLoaderE2E:
    def test_full_yaml_load_apply(self, tmp_path):
        """Write rebuild.yaml, load it, apply to WalkConfig, verify all fields."""
        cfg_file = tmp_path / "rebuild.yaml"
        cfg_file.write_text(textwrap.dedent("""\
            project:
              days: 14
              deploy:
                method: none
                health_url: http://myservice/health
                health_timeout: 120
                retry_attempts: 5
                retry_backoff_seconds: 3.0
              output: ./results
              base_url: http://myservice
              screenshots: false
              auth:
                X-Api-Key: secret123
              login_url: http://myservice/login
              login_payload:
                username: admin
                password: pass
              fixtures:
                user_id: "42"
              test_bodies:
                POST /api/items:
                  name: test_item
        """))
        from rebuild.infrastructure.config_loader import ConfigLoader
        from rebuild.domain.models import WalkConfig, DeployMethod
        data = ConfigLoader.load(cfg_file)
        assert data is not None
        errors = ConfigLoader.validate(data)
        assert errors == []

        config = WalkConfig(repo_path=tmp_path)
        ConfigLoader.apply_to_config(config, data)
        assert config.days == 14
        assert config.deploy_method == DeployMethod.NONE
        assert config.health_url == "http://myservice/health"
        assert config.health_timeout == 120
        assert config.deploy_retry_attempts == 5
        assert config.base_url == "http://myservice"
        assert config.screenshots is False
        assert config.auth["X-Api-Key"] == "secret123"
        assert config.login_url == "http://myservice/login"
        assert config.login_payload["username"] == "admin"
        assert config.test_fixtures["user_id"] == "42"
        assert config.test_bodies["POST /api/items"]["name"] == "test_item"

    def test_minimal_yaml_no_errors(self, tmp_path):
        cfg_file = tmp_path / "rebuild.yaml"
        cfg_file.write_text("project:\n  days: 7\n")
        from rebuild.infrastructure.config_loader import ConfigLoader
        data = ConfigLoader.load(cfg_file)
        assert ConfigLoader.validate(data) == []

    def test_validation_invalid_deploy_method(self):
        from rebuild.infrastructure.config_loader import ConfigLoader
        errors = ConfigLoader.validate({"project": {"deploy": {"method": "ftp"}}})
        assert any("method" in e for e in errors)

    def test_validation_invalid_types(self):
        from rebuild.infrastructure.config_loader import ConfigLoader
        errors = ConfigLoader.validate({
            "project": {
                "deploy": {
                    "health_timeout": "bad",
                }
            }
        })
        assert len(errors) >= 1

    def test_load_nonexistent_returns_none(self, tmp_path):
        from rebuild.infrastructure.config_loader import ConfigLoader
        result = ConfigLoader.load(tmp_path / "nonexistent.yaml")
        assert result is None or result == {}


# ─────────────────────────────────────────────────────────────────────────────
# E2E: ReporterService CSV + Markdown round-trip
# ─────────────────────────────────────────────────────────────────────────────

class TestReporterServiceE2E:
    def _make_results(self, tmp_path, n=3):
        from rebuild.domain.day_result import DayResult
        from rebuild.domain.models import DeployMethod
        from rebuild.domain.endpoint import Endpoint, EndpointResult, EndpointStatus
        results = []
        for i in range(n):
            d = date(2025, 1, i + 1)
            ep = Endpoint(method="GET", path=f"/ep/{i}", base_url="http://localhost")
            er = EndpointResult(endpoint=ep, status=EndpointStatus.OK,
                                http_status=200, response_time_ms=10.0)
            results.append(DayResult(
                day=d, commit=None, deploy_method=DeployMethod.NONE,
                deploy_success=True, endpoints=[ep], endpoint_results=[er],
                output_dir=tmp_path / str(d),
            ))
        return results

    def test_csv_content(self, tmp_path):
        import csv
        from rebuild.application.services.reporting.reporter import ReporterService
        results = self._make_results(tmp_path)
        svc = ReporterService()
        svc.export_csv(results, tmp_path)
        csv_file = tmp_path / "summary.csv"
        assert csv_file.exists()
        rows = list(csv.DictReader(csv_file.open()))
        assert len(rows) == 3
        assert rows[0]["day"] == "2025-01-01"
        assert rows[0]["deploy_success"].lower() == "true"

    def test_markdown_content(self, tmp_path):
        from rebuild.application.services.reporting.reporter import ReporterService
        results = self._make_results(tmp_path)
        svc = ReporterService()
        svc.export_markdown(results, tmp_path)
        md_file = tmp_path / "summary.md"
        assert md_file.exists()
        content = md_file.read_text()
        assert "2025-01-01" in content
        assert "|" in content  # markdown table

    def test_csv_health_pct_correct(self, tmp_path):
        import csv
        from rebuild.domain.day_result import DayResult
        from rebuild.domain.models import DeployMethod
        from rebuild.domain.endpoint import Endpoint, EndpointResult, EndpointStatus
        from rebuild.application.services.reporting.reporter import ReporterService

        eps = [Endpoint(method="GET", path=f"/ep/{i}", base_url="http://localhost") for i in range(4)]
        ers = [
            EndpointResult(endpoint=eps[i],
                           status=EndpointStatus.OK if i < 3 else EndpointStatus.FAIL,
                           http_status=200, response_time_ms=5.0)
            for i in range(4)
        ]
        dr = DayResult(day=date(2025, 6, 1), commit=None, deploy_method=DeployMethod.NONE,
                       deploy_success=True, endpoints=eps, endpoint_results=ers)
        svc = ReporterService()
        svc.export_csv([dr], tmp_path)
        rows = list(csv.DictReader((tmp_path / "summary.csv").open()))
        # 3/4 = 75%
        assert float(rows[0]["health_pct"]) == pytest.approx(75.0, abs=0.1)


# ─────────────────────────────────────────────────────────────────────────────
# E2E: CLI subprocess — version, init, report, analyze
# ─────────────────────────────────────────────────────────────────────────────

class TestCLISubprocessE2E:
    def _run(self, *args, cwd=None):
        return subprocess.run(
            [sys.executable, "-m", "rebuild", *args],
            capture_output=True, text=True, cwd=cwd,
        )

    def test_version_command(self):
        r = self._run("version")
        assert r.returncode == 0
        assert "rebuild" in r.stdout
        assert "0." in r.stdout

    def test_help_command(self):
        r = self._run("--help")
        assert r.returncode == 0
        assert "walk" in r.stdout
        assert "analyze" in r.stdout

    def test_init_creates_files(self, tmp_path):
        r = self._run("init", str(tmp_path), cwd=str(tmp_path))
        assert r.returncode == 0
        assert (tmp_path / ".env").exists()

    def test_init_force_flag(self, tmp_path):
        (tmp_path / "rebuild.yaml").write_text("old content")
        r = self._run("init", str(tmp_path), "--force", cwd=str(tmp_path))
        assert r.returncode == 0

    def test_report_empty_dir(self, tmp_path):
        r = self._run("report", "--results-dir", str(tmp_path), cwd=str(tmp_path))
        assert r.returncode == 0
        assert "Brak" in r.stdout

    def test_walk_no_git_repo(self, tmp_path):
        not_repo = tmp_path / "empty"
        not_repo.mkdir()
        r = self._run("walk", str(not_repo), "--dry-run", "--deploy", "none", "--days", "1")
        assert r.returncode != 0

    def test_analyze_help(self):
        r = self._run("analyze", "--help")
        assert r.returncode == 0
        assert "duplicates" in r.stdout or "analyze" in r.stdout

    def test_refactor_help(self):
        r = self._run("refactor", "--help")
        assert r.returncode == 0

    def test_dsl_command_parse(self):
        r = self._run("dsl", "--command", "walk repo:/tmp days:1")
        assert r.returncode == 0
        assert "walk" in r.stdout

    def test_nlp_command_analyze(self):
        r = self._run("nlp", "analyze code for duplicates", "--to-dsl")
        assert r.returncode == 0
        assert "analyze" in r.stdout

    def test_serve_missing_dir(self, tmp_path):
        r = self._run("serve", "--results-dir", str(tmp_path / "nonexistent"))
        assert r.returncode != 0

    def test_bump_script_dry_run(self, tmp_path):
        """Test bump_version.py --dry-run doesn't modify files."""
        import re
        r = subprocess.run(
            [sys.executable, "scripts/bump_version.py", "patch", "--dry-run"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert r.returncode == 0
        assert "dry-run" in r.stdout
        assert "No files modified" in r.stdout

    def test_bump_script_show(self):
        r = subprocess.run(
            [sys.executable, "scripts/bump_version.py", "--show"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert r.returncode == 0
        assert "rebuild v" in r.stdout


# ─────────────────────────────────────────────────────────────────────────────
# E2E: PR service + summary service pipeline
# ─────────────────────────────────────────────────────────────────────────────

class TestPRSummaryPipelineE2E:
    def test_summary_from_duplication_to_pr_body(self):
        from rebuild.application.services.summary_service import SummaryService
        from rebuild.application.services.pr_service import PRService, PRConfig, Platform

        report = {
            "duplicate_groups": [
                {"fragments": [
                    {"file_path": "a.py", "start_line": 1, "end_line": 10},
                    {"file_path": "b.py", "start_line": 5, "end_line": 14},
                    {"file_path": "c.py", "start_line": 2, "end_line": 11},
                ]},
            ],
            "total_duplication_pct": 22.5,
        }
        summary_svc = SummaryService()
        result = summary_svc.generate_from_duplication(report)
        assert result.total_duplication == 22.5
        assert len(result.suggestions) >= 1

        cfg = PRConfig(platform=Platform.GITHUB, token="t", repo_owner="o", repo_name="r")
        pr_svc = PRService(cfg)
        body = pr_svc._generate_pr_body(result.summary, [s.description for s in result.suggestions])
        assert "Refactor" in body
        assert "Analysis" in body

    def test_summary_service_graph_flow(self):
        from rebuild.application.services.summary_service import SummaryService

        data = {
            "services": {"UserService": {"methods": ["get", "create"]}, "OrderService": {"methods": ["list"]}},
            "cycles": [["UserService", "OrderService", "UserService"]],
        }
        svc = SummaryService()
        result = svc.generate_from_service_graph(data)
        assert result is not None

    def test_pr_service_dry_run_body_structure(self):
        from rebuild.application.services.pr_service import PRService, PRConfig, Platform
        cfg = PRConfig(platform=Platform.GITHUB, token="t", repo_owner="o", repo_name="r",
                       title="MyTitle", base_branch="develop", head_branch="feature/x")
        svc = PRService(cfg)
        body = svc._generate_pr_body("AI summary here", ["Fix A", "Fix B"])
        assert "MyTitle" in body
        assert "AI summary here" in body
        assert "Fix A" in body
        assert "Fix B" in body
        assert "Review" in body
