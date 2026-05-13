from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional

from ..analysis.duplication_engine import DuplicateGroup
from ..analysis.service_similarity import ServiceSimilarity
from ..analysis.service_graph import ServiceNode


@dataclass
class RefactorSuggestion:
    title: str
    description: str
    impact: str  # HIGH, MEDIUM, LOW
    type: str  # MERGE_DUPLICATES, SPLIT_SERVICE, EXTRACT_INTERFACE, ADAPTER_PATTERN
    files: List[Path] = field(default_factory=list)
    rationale: Optional[str] = None


class RecommendationEngine:
    """
    Synthesizes analysis data into prioritized refactor suggestions.
    Recognizes architectural patterns (Adapter, Interface, etc.).
    """

    def generate_plan(
        self,
        duplicates: List[DuplicateGroup],
        similarities: List[ServiceSimilarity],
        graph: Dict[str, ServiceNode],
        cycles: List[List[str]],
    ) -> List[RefactorSuggestion]:
        suggestions = []
        suggestions.extend(self._duplicate_suggestions(duplicates))
        suggestions.extend(self._similarity_suggestions(similarities))
        suggestions.extend(self._adapter_suggestions(graph))
        suggestions.extend(self._cycle_suggestions(cycles))
        return sorted(suggestions, key=lambda x: x.impact, reverse=True)

    def _duplicate_suggestions(self, duplicates: List[DuplicateGroup]) -> List[RefactorSuggestion]:
        suggestions = []
        for group in duplicates:
            if group.similarity >= 0.9:
                suggestions.append(
                    RefactorSuggestion(
                        title=f"Merge Duplicates: {group.fragments[0].name or 'block'}",
                        description=f"Found {len(group.fragments)} exact or near-exact duplicates.",
                        impact="HIGH" if len(group.fragments) > 2 else "MEDIUM",
                        type="MERGE_DUPLICATES",
                        files=[f.file for f in group.fragments],
                        rationale=f"Structural similarity: {group.similarity:.2f}. Reason: {group.reason}",
                    )
                )
        return suggestions

    def _similarity_suggestions(
        self, similarities: List[ServiceSimilarity]
    ) -> List[RefactorSuggestion]:
        suggestions = []
        for sim in similarities:
            if sim.overlap > 0.4:
                suggestions.append(
                    RefactorSuggestion(
                        title=f"Consolidate Services: {sim.service_a} & {sim.service_b}",
                        description="These services share significant structural logic.",
                        impact="HIGH" if sim.overlap > 0.7 else "MEDIUM",
                        type="MERGE_SERVICES",
                        files=[Path(sim.service_a), Path(sim.service_b)],
                        rationale=f"Method overlap: {sim.overlap:.2f}",
                    )
                )
        return suggestions

    def _adapter_suggestions(self, graph: Dict[str, ServiceNode]) -> List[RefactorSuggestion]:
        suggestions = []
        for name, node in graph.items():
            infra_deps = self._infra_dependencies(node)
            if len(infra_deps) >= 2:
                suggestions.append(
                    RefactorSuggestion(
                        title=f"Apply Adapter Pattern to {name.split('.')[-1]}",
                        description="Service depends directly on multiple infrastructure components.",
                        impact="MEDIUM",
                        type="ADAPTER_PATTERN",
                        files=[Path(name.replace(".", "/") + ".py")],
                        rationale=f"Direct dependencies on: {', '.join(infra_deps)}. This hinders mockability.",
                    )
                )
        return suggestions

    def _infra_dependencies(self, node: ServiceNode) -> List[str]:
        markers = ["git", "http", "docker", "subprocess"]
        return [
            dep for dep in node.dependencies if any(marker in dep.lower() for marker in markers)
        ]

    def _cycle_suggestions(self, cycles: List[List[str]]) -> List[RefactorSuggestion]:
        suggestions = []
        for cycle in cycles:
            suggestions.append(
                RefactorSuggestion(
                    title=f"Break Circular Dependency: {' -> '.join(cycle)}",
                    description="Found an architectural cycle between these services.",
                    impact="HIGH",
                    type="EXTRACT_INTERFACE",
                    files=[Path(c.replace(".", "/") + ".py") for c in cycle],
                    rationale="Cycles prevent modularity and lead to fragile builds.",
                )
            )
        return suggestions
