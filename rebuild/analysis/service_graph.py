from __future__ import annotations
import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Set, Optional

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
            if f.name == "__init__.py": continue
            
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
                    if self.base_package in alias.name:
                        node.dependencies.add(alias.name)
            elif isinstance(subnode, ast.ImportFrom):
                if subnode.module and (self.base_package in subnode.module or subnode.level > 0):
                    # Handle relative imports (approximate)
                    module_name = subnode.module
                    if subnode.level > 0:
                        # Simple relative import resolver
                        parts = node.name.split(".")
                        module_name = ".".join(parts[: -subnode.level]) + "." + (subnode.module or "")
                    node.dependencies.add(module_name.strip("."))

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
