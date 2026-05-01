from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Set, Optional
from enum import Enum


class SnapshotType(Enum):
    """Type of dependency snapshot."""
    FULL = "full"
    INCREMENTAL = "incremental"


@dataclass
class DependencyEdge:
    """A single dependency relationship between modules."""
    source: str
    target: str
    edge_type: str  # "import", "function_call", "class_inheritance", etc.


@dataclass
class ModuleNode:
    """A module in the dependency graph."""
    name: str
    file_path: str
    complexity: float = 0.0
    lines_of_code: int = 0


@dataclass
class GraphSnapshot:
    """A snapshot of the dependency graph at a specific point in time."""
    timestamp: str
    commit_sha: Optional[str] = None
    nodes: List[ModuleNode] = field(default_factory=list)
    edges: List[DependencyEdge] = field(default_factory=list)
    snapshot_type: SnapshotType = SnapshotType.FULL
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "commit_sha": self.commit_sha,
            "nodes": [
                {
                    "name": n.name,
                    "file_path": n.file_path,
                    "complexity": n.complexity,
                    "lines_of_code": n.lines_of_code,
                }
                for n in self.nodes
            ],
            "edges": [
                {"source": e.source, "target": e.target, "edge_type": e.edge_type}
                for e in self.edges
            ],
            "snapshot_type": self.snapshot_type.value,
            "metadata": self.metadata,
        }


@dataclass
class Timeline:
    """Timeline of dependency graph snapshots for evolution playback."""
    repo_path: str
    snapshots: List[GraphSnapshot] = field(default_factory=list)

    def add_snapshot(self, snapshot: GraphSnapshot) -> None:
        """Add a snapshot to the timeline."""
        self.snapshots.append(snapshot)

    def get_snapshot_at_index(self, index: int) -> Optional[GraphSnapshot]:
        """Get snapshot by index."""
        if 0 <= index < len(self.snapshots):
            return self.snapshots[index]
        return None

    def get_snapshot_by_commit(self, commit_sha: str) -> Optional[GraphSnapshot]:
        """Get snapshot by commit SHA."""
        for snapshot in self.snapshots:
            if snapshot.commit_sha == commit_sha:
                return snapshot
        return None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "repo_path": self.repo_path,
            "snapshots": [s.to_dict() for s in self.snapshots],
        }

    def save(self, output_path: str) -> None:
        """Save timeline to JSON file."""
        import json
        from pathlib import Path

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, input_path: str) -> "Timeline":
        """Load timeline from JSON file."""
        import json
        from pathlib import Path

        with open(input_path) as f:
            data = json.load(f)

        timeline = cls(repo_path=data["repo_path"])
        for snap_data in data["snapshots"]:
            nodes = [
                ModuleNode(
                    name=n["name"],
                    file_path=n["file_path"],
                    complexity=n.get("complexity", 0.0),
                    lines_of_code=n.get("lines_of_code", 0),
                )
                for n in snap_data["nodes"]
            ]
            edges = [
                DependencyEdge(
                    source=e["source"], target=e["target"], edge_type=e["edge_type"]
                )
                for e in snap_data["edges"]
            ]
            snapshot = GraphSnapshot(
                timestamp=snap_data["timestamp"],
                commit_sha=snap_data.get("commit_sha"),
                nodes=nodes,
                edges=edges,
                snapshot_type=SnapshotType(snap_data.get("snapshot_type", "full")),
                metadata=snap_data.get("metadata", {}),
            )
            timeline.add_snapshot(snapshot)

        return timeline
