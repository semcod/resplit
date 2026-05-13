from __future__ import annotations
import ast
import os
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Set, Tuple

from .duplication_engine import DuplicationEngine


@dataclass
class ServiceNode:
    name: str
    path: Path
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    methods: List[str] = field(default_factory=list)


class ServiceGraphBuilder:
    """
    Builds a dependency graph of services within the application layer.
    """

    def __init__(self, services_dir: Path, base_package: str = "rebuild"):
        self.services_dir = services_dir
        self.base_package = base_package
        self.nodes: Dict[str, ServiceNode] = {}

    def build(self) -> Dict[str, ServiceNode]:
        # 1. Discover all services
        for f in self.services_dir.glob("**/*.py"):
            if f.name == "__init__.py":
                continue
            if any(
                p in f.parts
                for p in (".git", ".venv", "venv", "__pycache__", "node_modules", ".rebuild")
            ):
                continue

            # Use relative path as name (e.g. services.git_service)
            rel = f.relative_to(self.services_dir.parent)
            name = str(rel).replace(os.sep, ".").replace(".py", "")

            node = ServiceNode(name=name, path=f)
            self._analyze_file(node)
            self.nodes[name] = node

        # 2. Build cross-references (dependents)
        for name, node in self.nodes.items():
            for dep in node.dependencies:
                if dep in self.nodes:
                    self.nodes[dep].dependents.add(name)

        return self.nodes

    def _analyze_file(self, node: ServiceNode):
        try:
            content = node.path.read_text()
            tree = ast.parse(content)
        except Exception:
            return

        for subnode in ast.walk(tree):
            # Track imports
            if isinstance(subnode, ast.Import):
                for alias in subnode.names:
                    if self.base_package in alias.name and alias.name != node.name:
                        node.dependencies.add(alias.name)
            elif isinstance(subnode, ast.ImportFrom):
                if subnode.module and (self.base_package in subnode.module or subnode.level > 0):
                    # Handle relative imports (approximate)
                    module_name = subnode.module
                    if subnode.level > 0:
                        # Simple relative import resolver
                        parts = node.name.split(".")
                        module_name = (
                            ".".join(parts[: -subnode.level]) + "." + (subnode.module or "")
                        )
                    resolved = module_name.strip(".")
                    # Skip self-dependencies (e.g., when a module file coexists
                    # with a same-named package and uses relative imports).
                    if resolved and resolved != node.name:
                        node.dependencies.add(resolved)

            # Track methods
            if isinstance(subnode, ast.FunctionDef):
                if not subnode.name.startswith("__"):
                    node.methods.append(subnode.name)

    def detect_cycles(self) -> List[List[str]]:
        cycles = []
        visited = set()
        stack = []

        def visit(name: str):
            if name in stack:
                cycle_start = stack.index(name)
                cycles.append(stack[cycle_start:] + [name])
                return
            if name in visited:
                return

            visited.add(name)
            stack.append(name)
            node = self.nodes.get(name)
            if node:
                for dep in node.dependencies:
                    visit(dep)
            stack.pop()

        for name in self.nodes:
            visit(name)
        return cycles


@dataclass
class CrossRepoDependency:
    source_repo: str
    target_repo: str
    imports_count: int


@dataclass
class CrossRepoCloneGroup:
    structural_hash: str
    repositories: List[str]
    fragments_count: int


@dataclass
class MultiRepoReport:
    repositories: Dict[str, str]
    dependencies: List[CrossRepoDependency]
    clone_groups: List[CrossRepoCloneGroup]

    def to_dict(self) -> Dict[str, object]:
        return {
            "repositories": self.repositories,
            "dependencies": [
                {
                    "source_repo": dep.source_repo,
                    "target_repo": dep.target_repo,
                    "imports_count": dep.imports_count,
                }
                for dep in self.dependencies
            ],
            "clone_groups": [
                {
                    "structural_hash": group.structural_hash,
                    "repositories": group.repositories,
                    "fragments_count": group.fragments_count,
                }
                for group in self.clone_groups
            ],
        }


class MultiRepoAnalyzer:
    """Analyze cross-repo dependencies and shared structural code clones."""

    def __init__(self, repo_paths: List[Path], min_lines: int = 6):
        cleaned = [p.resolve() for p in repo_paths]
        self.repos = self._normalize_repo_keys(cleaned)
        self.min_lines = min_lines

    def analyze(self) -> MultiRepoReport:
        dependencies = self._analyze_dependencies()
        clone_groups = self._analyze_shared_clones()
        repositories = {key: str(path) for key, path in self.repos.items()}
        return MultiRepoReport(
            repositories=repositories,
            dependencies=dependencies,
            clone_groups=clone_groups,
        )

    def export_json(self, output: Path, report: MultiRepoReport) -> None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")

    def _normalize_repo_keys(self, repo_paths: List[Path]) -> Dict[str, Path]:
        used: Set[str] = set()
        out: Dict[str, Path] = {}
        for path in repo_paths:
            base = path.name.replace("-", "_") or "repo"
            key = base
            idx = 2
            while key in used:
                key = f"{base}_{idx}"
                idx += 1
            used.add(key)
            out[key] = path
        return out

    def _repo_aliases(self) -> Dict[str, Set[str]]:
        aliases: Dict[str, Set[str]] = {}
        for key, repo in self.repos.items():
            names = {key}
            pyproject = repo / "pyproject.toml"
            if pyproject.exists():
                try:
                    content = pyproject.read_text(encoding="utf-8", errors="ignore")
                    for line in content.splitlines():
                        line = line.strip()
                        if line.startswith("name") and "=" in line:
                            value = line.split("=", 1)[1].strip().strip('"').strip("'")
                            if value:
                                names.add(value.replace("-", "_"))
                            break
                except Exception:
                    pass

            try:
                for item in repo.iterdir():
                    if item.is_dir() and (item / "__init__.py").exists():
                        names.add(item.name)
            except Exception:
                pass

            aliases[key] = {name for name in names if name}
        return aliases

    def _analyze_dependencies(self) -> List[CrossRepoDependency]:
        aliases = self._repo_aliases()
        alias_to_repo: Dict[str, str] = {}
        for repo_key, names in aliases.items():
            for name in names:
                alias_to_repo.setdefault(name, repo_key)

        counts: Dict[Tuple[str, str], int] = {}
        for source_key, source_repo in self.repos.items():
            for py_file in self._iter_python_files(source_key, source_repo):
                for imported_root in self._import_roots(py_file):
                    target_key = alias_to_repo.get(imported_root)
                    if not target_key or target_key == source_key:
                        continue
                    edge = (source_key, target_key)
                    counts[edge] = counts.get(edge, 0) + 1

        edges = [CrossRepoDependency(src, dst, amount) for (src, dst), amount in counts.items()]
        edges.sort(key=lambda dep: dep.imports_count, reverse=True)
        return edges

    def _import_roots(self, py_file: Path) -> Set[str]:
        roots: Set[str] = set()
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content)
        except Exception:
            return roots

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".", 1)[0]
                    if root:
                        roots.add(root)
            elif isinstance(node, ast.ImportFrom):
                if node.level > 0:
                    continue
                if node.module:
                    root = node.module.split(".", 1)[0]
                    if root:
                        roots.add(root)
        return roots

    def _analyze_shared_clones(self) -> List[CrossRepoCloneGroup]:
        engine = DuplicationEngine(min_lines=self.min_lines)
        by_hash: Dict[str, Set[str]] = {}
        counts: Dict[str, int] = {}

        for repo_key, repo_path in self.repos.items():
            for code_file in self._iter_fragment_files(repo_key, repo_path):
                try:
                    fragments = engine._extract_fragments(code_file)
                except Exception:
                    continue
                for fragment in fragments:
                    by_hash.setdefault(fragment.structural_hash, set()).add(repo_key)
                    counts[fragment.structural_hash] = counts.get(fragment.structural_hash, 0) + 1

        groups: List[CrossRepoCloneGroup] = []
        for structural_hash, repos in by_hash.items():
            if len(repos) < 2:
                continue
            groups.append(
                CrossRepoCloneGroup(
                    structural_hash=structural_hash,
                    repositories=sorted(repos),
                    fragments_count=counts.get(structural_hash, 0),
                )
            )

        groups.sort(
            key=lambda group: (len(group.repositories), group.fragments_count), reverse=True
        )
        return groups

    def _iter_python_files(self, source_key: str, repo_path: Path) -> List[Path]:
        files: List[Path] = []
        for file_path in self._iter_code_files(repo_path, exts={".py"}):
            if self._belongs_to_other_repo(source_key, file_path):
                continue
            files.append(file_path)
        return files

    def _iter_fragment_files(self, source_key: str, repo_path: Path) -> List[Path]:
        files: List[Path] = []
        exts = {".py", ".js", ".ts", ".jsx", ".tsx"}
        for file_path in self._iter_code_files(repo_path, exts=exts):
            if self._belongs_to_other_repo(source_key, file_path):
                continue
            files.append(file_path)
        return files

    def _iter_code_files(self, repo_path: Path, exts: Set[str]) -> List[Path]:
        if (repo_path / ".git").exists():
            result = subprocess.run(
                ["git", "-C", str(repo_path), "ls-files"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                tracked: List[Path] = []
                for rel in result.stdout.splitlines():
                    if not rel:
                        continue
                    p = (repo_path / rel).resolve()
                    if p.suffix in exts and p.exists() and p.is_file():
                        tracked.append(p)
                return tracked

        fallback: List[Path] = []
        for f in repo_path.rglob("*"):
            if not f.is_file():
                continue
            if f.suffix not in exts:
                continue
            if any(
                p in f.parts
                for p in (".git", ".venv", "venv", "__pycache__", "node_modules", ".rebuild")
            ):
                continue
            fallback.append(f.resolve())
        return fallback

    def _belongs_to_other_repo(self, source_key: str, file_path: Path) -> bool:
        for other_key, other_repo in self.repos.items():
            if other_key == source_key:
                continue
            try:
                file_path.relative_to(other_repo)
                return True
            except ValueError:
                continue
        return False
