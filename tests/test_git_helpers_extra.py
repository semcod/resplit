"""
Coverage boost: git_service, helpers, dsl edge cases, analysis modules.
"""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from rebuild.domain.models import WalkConfig
from rebuild.domain.commit import CommitInfo
from rebuild.domain.endpoint import Endpoint, EndpointResult, EndpointStatus
from rebuild.domain.day_result import DayResult, DeployErrorCategory


# ─────────────────────────────────────────────────────────────
# GitService — uncovered branches
# ─────────────────────────────────────────────────────────────

from rebuild.application.services.git_service import GitService


def _shell_ok(stdout="", stderr=""):
    s = MagicMock()
    r = MagicMock()
    r.returncode = 0
    r.stdout = stdout
    r.stderr = stderr
    s.run.return_value = r
    return s


def _shell_fail(stderr="err"):
    s = MagicMock()
    r = MagicMock()
    r.returncode = 1
    r.stdout = ""
    r.stderr = stderr
    s.run.return_value = r
    return s


def test_git_checkout(tmp_path):
    shell = _shell_ok()
    svc = GitService(tmp_path, shell=shell)
    svc.checkout("abc123")
    shell.run.assert_called_once()
    args = shell.run.call_args[0][0]
    assert "checkout" in args


def test_git_restore_head_default(tmp_path):
    shell = _shell_ok()
    svc = GitService(tmp_path, shell=shell)
    svc.restore_head()
    args = shell.run.call_args[0][0]
    assert "HEAD" in args


def test_git_restore_head_sha(tmp_path):
    shell = _shell_ok()
    svc = GitService(tmp_path, shell=shell)
    svc.restore_head("deadbeef")
    args = shell.run.call_args[0][0]
    assert "deadbeef" in args


def test_git_get_current_sha(tmp_path):
    shell = _shell_ok(stdout="abc123def456\n")
    svc = GitService(tmp_path, shell=shell)
    sha = svc.get_current_sha()
    assert sha == "abc123def456"


def test_git_diff_names_success(tmp_path):
    shell = _shell_ok(stdout="file1.py\nfile2.py\n")
    svc = GitService(tmp_path, shell=shell)
    files = svc.diff_names("sha1", "sha2")
    assert files == ["file1.py", "file2.py"]


def test_git_diff_names_error(tmp_path):
    shell = _shell_fail()
    svc = GitService(tmp_path, shell=shell)
    result = svc.diff_names("sha1", "sha2")
    assert result is None


def test_git_days_with_commits_date_filter(tmp_path):
    line1 = "abc123|2025-01-01|msg1|author|2025-01-01T12:00:00+00:00"
    line2 = "def456|2025-01-15|msg2|author|2025-01-15T12:00:00+00:00"
    shell = _shell_ok(stdout=f"{line1}\n{line2}\n")
    svc = GitService(tmp_path, shell=shell)
    cfg = WalkConfig(
        repo_path=tmp_path,
        days=10,
        date_from=date(2025, 1, 10),
        date_to=date(2025, 1, 31),
    )
    results = svc.days_with_commits(cfg)
    assert len(results) == 1
    assert results[0][0] == date(2025, 1, 15)


def test_git_days_with_commits_deduplicates_per_day(tmp_path):
    line1 = "abc123|2025-01-01|msg1|author|2025-01-01T10:00:00+00:00"
    line2 = "def456|2025-01-01|msg2|author|2025-01-01T14:00:00+00:00"
    shell = _shell_ok(stdout=f"{line1}\n{line2}\n")
    svc = GitService(tmp_path, shell=shell)
    cfg = WalkConfig(repo_path=tmp_path, days=10)
    results = svc.days_with_commits(cfg)
    assert len(results) == 1


def test_git_days_with_commits_git_error(tmp_path):
    shell = _shell_fail()
    svc = GitService(tmp_path, shell=shell)
    cfg = WalkConfig(repo_path=tmp_path)
    results = svc.days_with_commits(cfg)
    assert results == []


def test_git_clone_for_walk_existing(tmp_path):
    clone_path = tmp_path / "repo"
    clone_path.mkdir()
    (clone_path / ".git").mkdir()
    shell = _shell_ok()
    svc = GitService(tmp_path, shell=shell)
    result = svc.clone_for_walk(tmp_path)
    assert isinstance(result, GitService)


def test_git_clone_for_walk_new(tmp_path):
    shell = _shell_ok()
    svc = GitService(tmp_path, shell=shell)
    out = tmp_path / "out"
    result = svc.clone_for_walk(out)
    assert isinstance(result, GitService)


# ─────────────────────────────────────────────────────────────
# helpers — print_report_links
# ─────────────────────────────────────────────────────────────

from rebuild.interfaces.commands.helpers import print_report_links, print_summary_table


def test_print_report_links_with_port(tmp_path):
    console = MagicMock()
    print_report_links(tmp_path, 8080, console)
    printed = " ".join(str(c) for c in console.print.call_args_list)
    assert "8080" in printed or "localhost" in printed


def test_print_report_links_no_port(tmp_path):
    console = MagicMock()
    print_report_links(tmp_path, None, console)
    assert console.print.called


def test_print_summary_table_with_data():
    from rebuild.domain.models import DeployMethod
    ep = Endpoint(method="GET", path="/h", base_url="http://x")
    er = EndpointResult(endpoint=ep, status=EndpointStatus.OK, http_status=200)
    dr = DayResult(
        day=date(2025, 1, 1),
        commit=CommitInfo(sha="abc12345", message="m", author="a",
                          timestamp="t", date=date(2025, 1, 1)),
        deploy_method=DeployMethod.NONE,
        deploy_success=True,
        endpoints=[ep],
        endpoint_results=[er],
    )
    console = MagicMock()
    print_summary_table([dr], console)
    console.print.assert_called()


# ─────────────────────────────────────────────────────────────
# DSL edge cases
# ─────────────────────────────────────────────────────────────

from rebuild.domain.dsl import DSLParser, DSLInterpreter, Command


def test_dsl_parse_restore():
    cmd = DSLParser().parse("restore endpoint:/api/health repo:/tmp")
    assert cmd.command == Command.RESTORE


def test_dsl_parse_serve():
    cmd = DSLParser().parse("serve results_dir:.rebuild port:7821")
    assert cmd.command == Command.SERVE


def test_dsl_parse_accelerator():
    cmd = DSLParser().parse("accelerator repo:/tmp days:5 parallel:2")
    assert cmd.command == Command.ACCELERATOR


def test_dsl_parse_auto_pr():
    cmd = DSLParser().parse("auto_pr repo:/tmp branch:fix/broken")
    assert cmd.command == Command.AUTO_PR


def test_dsl_interpreter_auto_pr():
    cmd = DSLParser().parse("auto_pr repo:/tmp branch:main")
    result = DSLInterpreter().execute(cmd)
    assert result["command"] == "auto_pr"


def test_dsl_parse_file_ignores_comments(tmp_path):
    script = tmp_path / "test.dsl"
    script.write_text("# full comment line\nwalk repo:/tmp days:3\n   # another comment\n")
    cmds = DSLParser().parse_file(script)
    assert len(cmds) == 1
    assert cmds[0].command == Command.WALK


def test_dsl_parse_float_value():
    cmd = DSLParser().parse("walk repo:/tmp health_timeout:60.5")
    assert cmd.parameters["health_timeout"] in (60.5, "60.5")


def test_dsl_parse_string_with_colon_in_value():
    cmd = DSLParser().parse("walk repo:/tmp base_url:http://localhost:8003")
    assert "localhost" in cmd.parameters["base_url"]
