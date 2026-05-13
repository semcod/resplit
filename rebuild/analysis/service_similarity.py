from __future__ import annotations
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Set


@dataclass
class ServiceSimilarity:
    service_a: str
    service_b: str
    overlap: float
    common_methods: List[str]


class ServiceSimilarityAnalyzer:
    """
    Analyzer for detecting overlapping responsibilities between services.
    """

    def analyze_directory(self, services_dir: Path) -> List[ServiceSimilarity]:
        services_data: Dict[str, Set[str]] = {}

        for f in services_dir.glob("*_service.py"):
            try:
                tree = ast.parse(f.read_text())
                methods = self._extract_methods(tree)
                if methods:
                    services_data[f.stem] = methods
            except Exception:
                continue

        results = []
        names = list(services_data.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                s1, s2 = names[i], names[j]
                m1, m2 = services_data[s1], services_data[s2]

                intersection = m1.intersection(m2)
                union = m1.union(m2)
                overlap = len(intersection) / len(union) if union else 0

                if overlap > 0:
                    results.append(
                        ServiceSimilarity(
                            service_a=s1,
                            service_b=s2,
                            overlap=overlap,
                            common_methods=list(intersection),
                        )
                    )

        return sorted(results, key=lambda r: r.overlap, reverse=True)

    def _extract_methods(self, tree: ast.AST) -> Set[str]:
        methods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Ignore dunder methods and base methods
                if not node.name.startswith("__") and node.name != "execute":
                    methods.add(node.name)
        return methods
