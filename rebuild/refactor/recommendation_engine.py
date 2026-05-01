from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict

from ..analysis.duplication_engine import DuplicateGroup
from ..analysis.service_similarity import ServiceSimilarity
from ..analysis.service_graph import ServiceNode

@dataclass
class RefactorSuggestion:
    type: str  # "MERGE_DUPLICATES" | "EXTRACT_SERVICE" | "DECOUPLE_CYCLES" | "SPLIT_GOD_SERVICE"
    title: str
    description: str
    impact: str  # "HIGH" | "MEDIUM" | "LOW"
    files: List[Path]
    rationale: str = ""

class RecommendationEngine:
    """
    Generates actionable refactoring plans based on analysis results.
    Integrates architectural insights from the Service Graph.
    """
    def generate_plan(
        self, 
        duplicates: List[DuplicateGroup], 
        similarities: List[ServiceSimilarity],
        graph: Dict[str, ServiceNode],
        cycles: List[List[str]]
    ) -> List[RefactorSuggestion]:
        suggestions = []
        
        # 1. Duplicates suggestions (Semantic & Structural)
        for i, group in enumerate(duplicates):
            files = list(set(f.file for f in group.fragments))
            names = list(set(f.name or "block" for f in group.fragments))
            
            if group.similarity >= 1.0:
                suggestions.append(RefactorSuggestion(
                    type="MERGE_DUPLICATES",
                    title=f"Merge exact duplicates: {', '.join(names[:3])}",
                    description=f"Found {len(group.fragments)} structurally identical blocks. {group.reason}.",
                    impact="HIGH" if len(group.fragments) > 2 else "MEDIUM",
                    files=files,
                    rationale="Direct structural identity across multiple locations increases maintenance cost."
                ))
            elif group.similarity >= 0.8:
                suggestions.append(RefactorSuggestion(
                    type="MERGE_DUPLICATES",
                    title=f"Unify similar signatures: {', '.join(names[:3])}",
                    description=f"Found {len(group.fragments)} functions with identical parameter patterns. {group.reason}.",
                    impact="MEDIUM",
                    files=files,
                    rationale="Signature overlap suggests a missing interface or shared base class."
                ))

        # 2. Service Graph Insights: Cycles
        if cycles:
            for cycle in cycles:
                suggestions.append(RefactorSuggestion(
                    type="DECOUPLE_CYCLES",
                    title=f"Break dependency cycle: {' -> '.join(cycle)}",
                    description="Circular dependencies between services make the system rigid and hard to test.",
                    impact="HIGH",
                    files=[graph[name].path for name in cycle if name in graph],
                    rationale="Cycles violate the Directed Acyclic Graph (DAG) principle of clean architecture."
                ))

        # 3. Service Graph Insights: God Services
        for name, node in graph.items():
            if len(node.methods) > 15:
                suggestions.append(RefactorSuggestion(
                    type="SPLIT_GOD_SERVICE",
                    title=f"Refactor God Service: {name}",
                    description=f"Service has {len(node.methods)} methods. This suggests too many responsibilities.",
                    impact="MEDIUM",
                    files=[node.path],
                    rationale="Violates Single Responsibility Principle (SRP). Consider splitting into smaller services."
                ))

        # 4. Service Similarity Analysis
        for sim in similarities:
            if sim.overlap > 0.6:
                suggestions.append(RefactorSuggestion(
                    type="EXTRACT_SERVICE",
                    title=f"Extract shared logic: {sim.service_a} & {sim.service_b}",
                    description=f"Services share {len(sim.common_methods)} method names: {', '.join(sim.common_methods)}.",
                    impact="HIGH" if sim.overlap > 0.8 else "MEDIUM",
                    files=[graph[sim.service_a].path, graph[sim.service_b].path] if sim.service_a in graph and sim.service_b in graph else [],
                    rationale=f"Overlap of {sim.overlap*100:.0f}% suggests these services should be merged or share a common utility."
                ))
                
        return suggestions
