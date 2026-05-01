from __future__ import annotations
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RefactorSuggestion:
    """A single refactor suggestion."""
    file_path: str
    line_start: int
    line_end: int
    description: str
    severity: str  # "low", "medium", "high"
    suggestion_type: str  # "duplicate", "complexity", "naming", "structure"


@dataclass
class SummaryResult:
    """Result of AI summary generation."""
    summary: str
    suggestions: List[RefactorSuggestion]
    total_duplication: float
    high_priority_count: int


class SummaryService:
    """Service for generating AI summaries and refactor suggestions from analysis results."""

    def __init__(self):
        pass

    def generate_from_duplication(
        self,
        duplication_report: Dict,
        repo_path: Optional[Path] = None,
    ) -> SummaryResult:
        """Generate refactor suggestions from duplication analysis results."""
        suggestions: List[RefactorSuggestion] = []

        # Extract duplicate groups
        duplicate_groups = duplication_report.get("duplicate_groups", [])
        total_duplication = duplication_report.get("total_duplication_pct", 0.0)

        for group in duplicate_groups:
            fragments = group.get("fragments", [])
            if len(fragments) < 2:
                continue

            # Generate suggestion for this duplicate group
            for fragment in fragments:
                file_path = fragment.get("file_path", "")
                line_start = fragment.get("start_line", 0)
                line_end = fragment.get("end_line", line_start)

                severity = "high" if len(fragments) > 3 else "medium" if len(fragments) > 2 else "low"

                suggestion = RefactorSuggestion(
                    file_path=file_path,
                    line_start=line_start,
                    line_end=line_end,
                    description=f"Duplicate code found in {len(fragments)} locations. Consider extracting to a shared function.",
                    severity=severity,
                    suggestion_type="duplicate",
                )
                suggestions.append(suggestion)

        # Count high priority suggestions
        high_priority_count = sum(1 for s in suggestions if s.severity == "high")

        # Generate summary
        summary = self._generate_summary_text(suggestions, total_duplication)

        return SummaryResult(
            summary=summary,
            suggestions=suggestions,
            total_duplication=total_duplication,
            high_priority_count=high_priority_count,
        )

    def _generate_summary_text(self, suggestions: List[RefactorSuggestion], total_duplication: float) -> str:
        """Generate human-readable summary text."""
        total_suggestions = len(suggestions)
        high_count = sum(1 for s in suggestions if s.severity == "high")
        medium_count = sum(1 for s in suggestions if s.severity == "medium")
        low_count = sum(1 for s in suggestions if s.severity == "low")

        summary = f"""Code Analysis Summary
=====================

Overall duplication: {total_duplication:.1f}%
Total refactor suggestions: {total_suggestions}

Severity breakdown:
- High priority: {high_count}
- Medium priority: {medium_count}
- Low priority: {low_count}

This analysis identified opportunities to improve code quality through:
- Extracting duplicate code into shared functions
- Simplifying complex functions
- Improving naming conventions
- Restructuring code for better maintainability

"""
        return summary

    def format_suggestions_for_pr(self, suggestions: List[RefactorSuggestion]) -> List[str]:
        """Format suggestions for PR body."""
        formatted = []
        for suggestion in suggestions:
            formatted.append(
                f"- **{suggestion.severity.upper()}** [{suggestion.file_path}:{suggestion.line_start}-{suggestion.line_end}] "
                f"{suggestion.description}"
            )
        return formatted

    def generate_from_service_graph(self, service_graph: Dict) -> SummaryResult:
        """Generate refactor suggestions from service dependency analysis."""
        suggestions: List[RefactorSuggestion] = []

        # Extract dependency issues
        cycles = service_graph.get("cycles", [])
        for cycle in cycles:
            severity = "high"
            suggestion = RefactorSuggestion(
                file_path="",
                line_start=0,
                line_end=0,
                description=f"Circular dependency detected: {' -> '.join(cycle)}",
                severity=severity,
                suggestion_type="structure",
            )
            suggestions.append(suggestion)

        # Extract high coupling
        high_coupling = service_graph.get("high_coupling", [])
        for item in high_coupling:
            severity = "medium"
            suggestion = RefactorSuggestion(
                file_path=item.get("file", ""),
                line_start=0,
                line_end=0,
                description=f"High coupling detected: {item.get('name')} depends on {item.get('dependencies_count')} modules",
                severity=severity,
                suggestion_type="structure",
            )
            suggestions.append(suggestion)

        high_priority_count = sum(1 for s in suggestions if s.severity == "high")

        summary = f"""Service Analysis Summary
========================

Total structural issues: {len(suggestions)}
High priority: {high_priority_count}

Issues found:
- Circular dependencies: {len(cycles)}
- High coupling modules: {len(high_coupling)}

"""
        return SummaryResult(
            summary=summary,
            suggestions=suggestions,
            total_duplication=0.0,
            high_priority_count=high_priority_count,
        )
