from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .duplication_engine import CodeFragment, DuplicationEngine


@dataclass
class VectorSearchHit:
    fragment: CodeFragment
    score: float


class VectorSearchIndex:
    """SQLite-backed vector index for semantic lookup of code fragments."""

    def __init__(
        self,
        db_path: Path,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        self.db_path = db_path
        self.model_name = model_name
        self._model: Optional[Any] = None
        self.warning: Optional[str] = None
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS vectors (
                    id TEXT PRIMARY KEY,
                    file TEXT NOT NULL,
                    start_line INTEGER NOT NULL,
                    end_line INTEGER NOT NULL,
                    name TEXT,
                    structural_hash TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_vectors_file ON vectors(file)")
            conn.commit()

    def build_from_path(self, path: Path, min_lines: int = 4) -> int:
        engine = DuplicationEngine(min_lines=min_lines)
        fragments = engine.collect_fragments(path)
        return self.upsert_fragments(fragments)

    def upsert_fragments(self, fragments: List[CodeFragment]) -> int:
        model = self._get_model()
        if model is None:
            return 0
        if not fragments:
            return 0

        texts = [self._to_text(frag) for frag in fragments]
        try:
            vectors = model.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        except Exception as exc:
            self.warning = f"embedding encode failed: {exc}"
            return 0

        rows = []
        for fragment, vector in zip(fragments, vectors):
            rows.append(
                (
                    self._fragment_id(fragment),
                    str(fragment.file),
                    int(fragment.start_line),
                    int(fragment.end_line),
                    fragment.name,
                    fragment.structural_hash,
                    fragment.content,
                    json.dumps([float(x) for x in vector]),
                )
            )

        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO vectors(
                    id, file, start_line, end_line, name,
                    structural_hash, content, embedding
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            conn.commit()

        return len(rows)

    def query(self, text: str, top_k: int = 10) -> List[VectorSearchHit]:
        model = self._get_model()
        if model is None:
            return []

        try:
            q_vec = model.encode(
                [text],
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )[0]
        except Exception as exc:
            self.warning = f"query embedding failed: {exc}"
            return []

        hits: List[VectorSearchHit] = []
        for row in self._load_rows():
            embedding = row["embedding"]
            score = self._cosine_similarity(q_vec, embedding)
            hits.append(
                VectorSearchHit(
                    fragment=CodeFragment(
                        file=Path(row["file"]),
                        start_line=row["start_line"],
                        end_line=row["end_line"],
                        content=row["content"],
                        structural_hash=row["structural_hash"],
                        name=row["name"],
                    ),
                    score=score,
                )
            )

        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[: max(1, int(top_k))]

    def count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT COUNT(*) FROM vectors")
            row = cur.fetchone()
            return int(row[0] if row else 0)

    def _load_rows(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT file, start_line, end_line, name,
                       structural_hash, content, embedding
                FROM vectors
                """
            ).fetchall()

        out: List[Dict[str, Any]] = []
        for row in rows:
            out.append(
                {
                    "file": row["file"],
                    "start_line": int(row["start_line"]),
                    "end_line": int(row["end_line"]),
                    "name": row["name"],
                    "structural_hash": row["structural_hash"],
                    "content": row["content"],
                    "embedding": json.loads(row["embedding"]),
                }
            )
        return out

    def _get_model(self):
        if self._model is not None:
            return self._model

        try:
            from sentence_transformers import SentenceTransformer
        except Exception:
            self.warning = "package sentence-transformers not installed"
            return None

        try:
            self._model = SentenceTransformer(self.model_name)
        except Exception as exc:
            self.warning = f"cannot load model '{self.model_name}': {exc}"
            return None

        return self._model

    def _fragment_id(self, fragment: CodeFragment) -> str:
        return (
            f"{fragment.file}:{fragment.start_line}:{fragment.end_line}:{fragment.structural_hash}"
        )

    def _to_text(self, fragment: CodeFragment) -> str:
        if fragment.name:
            return f"function {fragment.name}\n{fragment.content}"
        return fragment.content

    def _cosine_similarity(self, left: Any, right: Any) -> float:
        try:
            return float(left @ right)
        except Exception:
            dot = sum(float(a) * float(b) for a, b in zip(left, right))
            norm_left = sum(float(a) * float(a) for a in left) ** 0.5
            norm_right = sum(float(b) * float(b) for b in right) ** 0.5
            if norm_left == 0.0 or norm_right == 0.0:
                return 0.0
            return dot / (norm_left * norm_right)
