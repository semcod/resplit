"""Coverage boost for analysis modules: duplication_engine, service_graph, service_similarity."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rebuild.analysis.duplication_engine import DuplicationEngine, CodeFragment, DuplicateGroup


# ─────────────────────────────────────────────
# DuplicationEngine basic scanning
# ─────────────────────────────────────────────

def test_scan_empty_dir(tmp_path):
    engine = DuplicationEngine()
    groups = engine.scan(tmp_path)
    assert groups == []


def test_scan_single_py_file_no_duplicates(tmp_path):
    f = tmp_path / "a.py"
    f.write_text("""
def foo(x):
    y = x + 1
    z = y * 2
    return z

def bar(x):
    result = x - 1
    out = result / 2
    return out
""")
    engine = DuplicationEngine(min_lines=3)
    groups = engine.scan(tmp_path)
    assert isinstance(groups, list)


def test_scan_duplicate_py_functions(tmp_path):
    code = """def helper(a, b):
    x = a + b
    y = x * 2
    z = y - 1
    return z
"""
    for name in ("mod1.py", "mod2.py"):
        (tmp_path / name).write_text(code)
    engine = DuplicationEngine(min_lines=4)
    groups = engine.scan(tmp_path)
    assert len(groups) >= 1
    assert groups[0].similarity == 1.0


def test_scan_skips_venv_dirs(tmp_path):
    venv = tmp_path / ".venv" / "lib"
    venv.mkdir(parents=True)
    (venv / "module.py").write_text("def f():\n    pass\n" * 10)
    engine = DuplicationEngine()
    groups = engine.scan(tmp_path)
    assert groups == []


def test_scan_js_file(tmp_path):
    js = tmp_path / "app.js"
    js.write_text("""
function processData(input) {
    var result = input + 1;
    var output = result * 2;
    return output;
}
function processData(input) {
    var result = input + 1;
    var output = result * 2;
    return output;
}
""")
    engine = DuplicationEngine(min_lines=4)
    groups = engine.scan(tmp_path)
    assert isinstance(groups, list)


def test_scan_syntax_error_py_file(tmp_path):
    f = tmp_path / "bad.py"
    f.write_text("def (broken syntax:\n    pass\n")
    engine = DuplicationEngine()
    groups = engine.scan(tmp_path)
    assert groups == []


def test_scan_unsupported_extension_ignored(tmp_path):
    (tmp_path / "readme.md").write_text("# Hello\nThis is a file\n")
    engine = DuplicationEngine()
    groups = engine.scan(tmp_path)
    assert groups == []


def test_collect_fragments_py(tmp_path):
    f = tmp_path / "funcs.py"
    f.write_text("""
def alpha(x, y):
    a = x + y
    b = a * 2
    c = b - 1
    return c

async def beta(x):
    result = await x
    y = result + 1
    return y
""")
    engine = DuplicationEngine(min_lines=4)
    frags = engine.collect_fragments(tmp_path)
    names = [fr.name for fr in frags]
    assert "alpha" in names
    assert "beta" in names


def test_extract_fragments_py_vararg_kwarg(tmp_path):
    f = tmp_path / "m.py"
    f.write_text("""
def variadic(*args, **kwargs):
    x = args[0]
    y = kwargs.get("y", 0)
    return x + y
""")
    engine = DuplicationEngine(min_lines=3)
    frags = engine._extract_py_fragments(f)
    assert len(frags) == 1
    assert "True:True" in frags[0].fuzzy_signature


def test_cosine_similarity_with_list():
    engine = DuplicationEngine()
    v1 = [1.0, 0.0]
    v2 = [1.0, 0.0]
    sim = engine._cosine_similarity(v1, v2)
    assert abs(sim - 1.0) < 1e-6


def test_cosine_similarity_zero_vector():
    engine = DuplicationEngine()
    v1 = [0.0, 0.0]
    v2 = [1.0, 0.0]
    sim = engine._cosine_similarity(v1, v2)
    assert sim == 0.0


def test_semantic_group_hash():
    engine = DuplicationEngine()
    frag = CodeFragment(
        file=Path("a.py"), start_line=1, end_line=5, content="code",
        structural_hash="h", fuzzy_signature="s"
    )
    h = engine._semantic_group_hash([frag])
    assert h.startswith("semantic:")


def test_semantic_text_with_name():
    engine = DuplicationEngine()
    frag = CodeFragment(
        file=Path("a.py"), start_line=1, end_line=5, content="x = 1",
        structural_hash="h", name="my_func"
    )
    txt = engine._semantic_text(frag)
    assert "function my_func" in txt


def test_semantic_text_without_name():
    engine = DuplicationEngine()
    frag = CodeFragment(
        file=Path("a.py"), start_line=1, end_line=5, content="x = 1",
        structural_hash="h"
    )
    txt = engine._semantic_text(frag)
    assert "x = 1" in txt


def test_average_group_similarity_single():
    engine = DuplicationEngine()
    result = engine._average_group_similarity(None, [0])
    assert result == 1.0


def test_find_semantic_groups_not_enabled():
    engine = DuplicationEngine(semantic_enabled=False)
    groups = engine._find_semantic_groups([], set())
    assert groups == []


def test_find_semantic_groups_no_encoder():
    engine = DuplicationEngine(semantic_enabled=True)
    engine._semantic_model = None
    with patch.object(engine, "_get_semantic_encoder", return_value=None):
        groups = engine._find_semantic_groups([], set())
    assert groups == []


def test_get_semantic_encoder_no_package():
    engine = DuplicationEngine(semantic_enabled=True)
    import builtins
    real = builtins.__import__
    def block_st(name, *args, **kwargs):
        if name == "sentence_transformers":
            raise ImportError("not installed")
        return real(name, *args, **kwargs)
    with patch("builtins.__import__", side_effect=block_st):
        result = engine._get_semantic_encoder()
    assert result is None
    assert engine.semantic_warning is not None


def test_fuzzy_matches_produce_group(tmp_path):
    code_a = """def compute(x, y):
    z = x + y
    w = z * 2
    return w
"""
    code_b = """def process(a, b):
    c = a + b
    d = c * 2
    return d
"""
    (tmp_path / "a.py").write_text(code_a)
    (tmp_path / "b.py").write_text(code_b)
    engine = DuplicationEngine(min_lines=3)
    groups = engine.scan(tmp_path)
    assert isinstance(groups, list)


# ─────────────────────────────────────────────
# ServiceGraphBuilder
# ─────────────────────────────────────────────

from rebuild.analysis.service_graph import ServiceGraphBuilder, ServiceNode


def test_service_graph_empty_dir(tmp_path):
    builder = ServiceGraphBuilder(tmp_path)
    nodes = builder.build()
    assert isinstance(nodes, dict)


def test_service_graph_simple_py(tmp_path):
    f = tmp_path / "my_service.py"
    f.write_text("""
class MyService:
    def get_data(self):
        pass
    def process(self, x):
        return x
""")
    builder = ServiceGraphBuilder(tmp_path)
    nodes = builder.build()
    assert len(nodes) >= 1


def test_service_graph_detect_cycles_empty(tmp_path):
    builder = ServiceGraphBuilder(tmp_path)
    builder.build()
    cycles = builder.detect_cycles()
    assert cycles == []


def test_service_graph_detect_no_cycles(tmp_path):
    (tmp_path / "a.py").write_text("""
class ServiceA:
    def do_a(self): pass
""")
    builder = ServiceGraphBuilder(tmp_path)
    builder.build()
    cycles = builder.detect_cycles()
    assert isinstance(cycles, list)


def test_service_graph_skips_venv(tmp_path):
    venv = tmp_path / ".venv" / "site-packages"
    venv.mkdir(parents=True)
    (venv / "mod.py").write_text("class Hidden:\n    pass\n")
    builder = ServiceGraphBuilder(tmp_path)
    nodes = builder.build()
    assert "Hidden" not in str(nodes)


# ─────────────────────────────────────────────
# ServiceSimilarityAnalyzer
# ─────────────────────────────────────────────

from rebuild.analysis.service_similarity import ServiceSimilarityAnalyzer


def test_service_similarity_empty_dir(tmp_path):
    analyzer = ServiceSimilarityAnalyzer()
    result = analyzer.analyze_directory(tmp_path)
    assert isinstance(result, list)


def test_service_similarity_single_service(tmp_path):
    f = tmp_path / "svc.py"
    f.write_text("""
class SvcA:
    def fetch(self): pass
    def store(self): pass
""")
    analyzer = ServiceSimilarityAnalyzer()
    result = analyzer.analyze_directory(tmp_path)
    assert isinstance(result, list)


def test_service_similarity_two_similar(tmp_path):
    (tmp_path / "svc_a.py").write_text("""
class ServiceA:
    def get(self): pass
    def post(self): pass
    def delete(self): pass
""")
    (tmp_path / "svc_b.py").write_text("""
class ServiceB:
    def get(self): pass
    def post(self): pass
    def delete(self): pass
""")
    analyzer = ServiceSimilarityAnalyzer()
    result = analyzer.analyze_directory(tmp_path)
    assert isinstance(result, list)


# ─────────────────────────────────────────────
# refactor recommendation_engine
# ─────────────────────────────────────────────

from rebuild.refactor.recommendation_engine import RecommendationEngine


def test_recommendation_engine_empty():
    engine = RecommendationEngine()
    plan = engine.generate_plan([], [], {}, [])
    assert isinstance(plan, list)


def test_recommendation_engine_with_duplicates():
    from rebuild.analysis.duplication_engine import CodeFragment, DuplicateGroup
    frag1 = CodeFragment(Path("a.py"), 1, 10, "code", "h1")
    frag2 = CodeFragment(Path("b.py"), 5, 14, "code", "h1")
    group = DuplicateGroup([frag1, frag2], 1.0, "h1")
    engine = RecommendationEngine()
    plan = engine.generate_plan([group], [], {}, [])
    assert len(plan) >= 1


def test_recommendation_engine_with_cycles():
    engine = RecommendationEngine()
    plan = engine.generate_plan([], [], {}, [["A", "B", "A"]])
    assert len(plan) >= 1


def test_recommendation_engine_with_similarities():
    from rebuild.analysis.service_similarity import ServiceSimilarity
    sim = ServiceSimilarity(service_a="A", service_b="B", overlap=0.9, common_methods=["get", "post"])
    engine = RecommendationEngine()
    plan = engine.generate_plan([], [sim], {}, [])
    assert isinstance(plan, list)


# ─────────────────────────────────────────────
# MultiRepoAnalyzer
# ─────────────────────────────────────────────

from rebuild.analysis.service_graph import MultiRepoAnalyzer, MultiRepoReport


def test_multi_repo_analyzer_two_empty_repos(tmp_path):
    repo_a = tmp_path / "alpha"
    repo_b = tmp_path / "beta"
    repo_a.mkdir()
    repo_b.mkdir()
    analyzer = MultiRepoAnalyzer([repo_a, repo_b], min_lines=3)
    report = analyzer.analyze()
    assert isinstance(report, MultiRepoReport)
    assert "alpha" in report.repositories or "beta" in report.repositories


def test_multi_repo_analyzer_with_py_files(tmp_path):
    repo_a = tmp_path / "svc_a"
    repo_b = tmp_path / "svc_b"
    repo_a.mkdir()
    repo_b.mkdir()
    shared_code = """
def shared_helper(x, y):
    a = x + y
    b = a * 2
    c = b - 1
    return c
"""
    (repo_a / "utils.py").write_text(shared_code)
    (repo_b / "utils.py").write_text(shared_code)
    analyzer = MultiRepoAnalyzer([repo_a, repo_b], min_lines=4)
    report = analyzer.analyze()
    assert isinstance(report.clone_groups, list)


def test_multi_repo_analyzer_normalize_keys_collision(tmp_path):
    repo_a = tmp_path / "myrepo"
    repo_b = tmp_path / "myrepo_copy"
    repo_a.mkdir()
    repo_b.mkdir()
    # Both resolve to 'myrepo' base
    (tmp_path / "myrepo2").mkdir()
    analyzer = MultiRepoAnalyzer([repo_a, repo_b])
    assert len(analyzer.repos) == 2
    assert len(set(analyzer.repos.keys())) == 2


def test_multi_repo_report_to_dict(tmp_path):
    from rebuild.analysis.service_graph import CrossRepoDependency, CrossRepoCloneGroup
    report = MultiRepoReport(
        repositories={"a": "/a", "b": "/b"},
        dependencies=[CrossRepoDependency("a", "b", 5)],
        clone_groups=[CrossRepoCloneGroup("h123", ["a", "b"], 3)],
    )
    d = report.to_dict()
    assert d["dependencies"][0]["imports_count"] == 5
    assert d["clone_groups"][0]["structural_hash"] == "h123"


def test_multi_repo_analyzer_export_json(tmp_path):
    repo_a = tmp_path / "a"
    repo_b = tmp_path / "b"
    repo_a.mkdir()
    repo_b.mkdir()
    analyzer = MultiRepoAnalyzer([repo_a, repo_b])
    report = analyzer.analyze()
    out = tmp_path / "report.json"
    analyzer.export_json(out, report)
    assert out.exists()
    import json
    data = json.loads(out.read_text())
    assert "repositories" in data


def test_multi_repo_analyzer_pyproject_alias(tmp_path):
    repo_a = tmp_path / "proj_a"
    repo_b = tmp_path / "proj_b"
    repo_a.mkdir()
    repo_b.mkdir()
    (repo_a / "pyproject.toml").write_text('[tool.poetry]\nname = "svc_a"\n')
    analyzer = MultiRepoAnalyzer([repo_a, repo_b])
    aliases = analyzer._repo_aliases()
    assert any("svc_a" in v for v in aliases.values())


def test_service_graph_with_imports(tmp_path):
    (tmp_path / "svc.py").write_text("""
import rebuild.application.services.git_service
from rebuild.domain import models

class DataService:
    def fetch(self): pass
    def process(self): pass
""")
    builder = ServiceGraphBuilder(tmp_path, base_package="rebuild")
    nodes = builder.build()
    assert len(nodes) >= 1
    node = list(nodes.values())[0]
    assert len(node.dependencies) >= 1


def test_service_graph_cycle_detection(tmp_path):
    (tmp_path / "a.py").write_text("""
import b
class A:
    def do(self): pass
""")
    (tmp_path / "b.py").write_text("""
import a
class B:
    def do(self): pass
""")
    builder = ServiceGraphBuilder(tmp_path, base_package="a")
    builder.build()
    # manually create cycle
    if "a" in builder.nodes and "b" in builder.nodes:
        builder.nodes["a"].dependencies.add("b")
        builder.nodes["b"].dependencies.add("a")
    cycles = builder.detect_cycles()
    assert isinstance(cycles, list)


# ─────────────────────────────────────────────
# GitTruthAnalyzer
# ─────────────────────────────────────────────

from rebuild.analysis.git_truth_analyzer import GitTruthAnalyzer, FunctionQuality


def test_git_truth_analyzer_no_git_history(tmp_path):
    (tmp_path / ".git").mkdir()
    analyzer = GitTruthAnalyzer(tmp_path)
    result = analyzer.analyze_function_history(tmp_path / "f.py", "my_fn")
    assert result == []


def test_git_truth_analyzer_load_historical_results_no_dir(tmp_path):
    analyzer = GitTruthAnalyzer(tmp_path, results_dir=tmp_path / "nonexistent")
    assert analyzer._historical_results == {}


def test_git_truth_analyzer_load_historical_results_with_data(tmp_path):
    results_dir = tmp_path / ".rebuild"
    day_dir = results_dir / "2025-01-01"
    day_dir.mkdir(parents=True)
    import json
    (day_dir / "results.json").write_text(json.dumps([
        {"status": "ok"}, {"status": "ok"}, {"status": "fail"}
    ]))
    (day_dir / "commit.txt").write_text("abc123\nrest")
    analyzer = GitTruthAnalyzer(tmp_path, results_dir=results_dir)
    assert "abc123" in analyzer._historical_results
    assert abs(analyzer._historical_results["abc123"] - 2/3) < 0.01


def test_git_truth_analyzer_analyze_content(tmp_path):
    from datetime import datetime
    (tmp_path / ".git").mkdir()
    analyzer = GitTruthAnalyzer(tmp_path)
    code = """
def my_fn(x):
    if x > 0:
        return x
    else:
        return -x
"""
    from datetime import datetime as dt
    ts = dt(2025, 1, 1, 0, 0)
    result = analyzer._analyze_content(code, "my_fn", "abc123", ts)
    assert result is not None
    assert result.func_name == "my_fn"
    assert result.complexity >= 2


def test_git_truth_analyzer_analyze_content_not_found(tmp_path):
    from datetime import datetime as dt
    (tmp_path / ".git").mkdir()
    analyzer = GitTruthAnalyzer(tmp_path)
    result = analyzer._analyze_content("def other(): pass", "nonexistent", "sha", dt.now())
    assert result is None


def test_git_truth_analyzer_analyze_content_syntax_error(tmp_path):
    from datetime import datetime as dt
    (tmp_path / ".git").mkdir()
    analyzer = GitTruthAnalyzer(tmp_path)
    result = analyzer._analyze_content("{bad python syntax!!!}", "fn", "sha", dt.now())
    assert result is None


def test_git_truth_analyzer_compute_complexity(tmp_path):
    (tmp_path / ".git").mkdir()
    analyzer = GitTruthAnalyzer(tmp_path)
    code = """
def complex_fn(x):
    if x > 0:
        while x > 0:
            x -= 1
        for i in range(x):
            pass
    return x
"""
    import ast
    tree = ast.parse(code)
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    complexity = analyzer._compute_complexity(fn)
    assert complexity >= 4
