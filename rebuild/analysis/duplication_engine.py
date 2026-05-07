from __future__ import annotations
import ast
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Dict, Set, Optional

@dataclass
class CodeFragment:
    file: Path
    start_line: int
    end_line: int
    content: str
    structural_hash: str
    fuzzy_signature: str = ""
    docstring_hash: str = ""
    name: Optional[str] = None

@dataclass
class DuplicateGroup:
    fragments: List[CodeFragment]
    similarity: float
    representative_hash: str
    reason: str = "Exact structural match"

class DuplicationEngine:
    """
    Engine for detecting structural and semantic duplication in codebases.
    Supports Python (AST) and JS/TS (Regex-based structural normalization).
    """
    def __init__(
        self,
        min_lines: int = 4,
        semantic_enabled: bool = False,
        semantic_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        semantic_threshold: float = 0.82,
        semantic_max_fragments: int = 300,
    ):
        self.min_lines = min_lines
        self.semantic_enabled = semantic_enabled
        self.semantic_model_name = semantic_model_name
        self.semantic_threshold = semantic_threshold
        self.semantic_max_fragments = semantic_max_fragments
        self.semantic_warning: Optional[str] = None
        self._semantic_model: Optional[Any] = None

    def scan(self, path: Path) -> List[DuplicateGroup]:
        exact_matches: Dict[str, List[CodeFragment]] = {}
        fuzzy_matches: Dict[str, List[CodeFragment]] = {}
        self.semantic_warning = None

        all_fragments = self.collect_fragments(path)
        for frag in all_fragments:
            exact_matches.setdefault(frag.structural_hash, []).append(frag)
            if frag.fuzzy_signature:
                fuzzy_matches.setdefault(frag.fuzzy_signature, []).append(frag)

        groups = []
        for h, frags in exact_matches.items():
            if len(frags) > 1:
                groups.append(DuplicateGroup(frags, 1.0, h, "Exact structural match"))

        seen_frags = {id(f) for g in groups for f in g.fragments}
        for h, frags in fuzzy_matches.items():
            if len(frags) > 1:
                unseen = [f for f in frags if id(f) not in seen_frags]
                if len(unseen) > 1:
                    groups.append(DuplicateGroup(unseen, 0.8, h, "Fuzzy signature match"))
                    seen_frags.update(id(f) for f in unseen)

        semantic_groups = self._find_semantic_groups(all_fragments, seen_frags)
        groups.extend(semantic_groups)

        return sorted(groups, key=lambda g: len(g.fragments), reverse=True)

    def collect_fragments(self, path: Path) -> List[CodeFragment]:
        fragments: List[CodeFragment] = []
        files = list(path.rglob("*.*"))
        for f in files:
            if any(p in f.parts for p in (".venv", "venv", "__pycache__", ".rebuild", ".git", "node_modules")):
                continue

            if f.suffix not in (".py", ".js", ".ts", ".jsx", ".tsx"):
                continue

            try:
                fragments.extend(self._extract_fragments(f))
            except Exception:
                continue
        return fragments

    def _find_semantic_groups(self, fragments: List[CodeFragment], seen_frags: Set[int]) -> List[DuplicateGroup]:
        if not self.semantic_enabled:
            return []

        encoder = self._get_semantic_encoder()
        if encoder is None:
            return []

        candidates = self._semantic_candidates(fragments, seen_frags)
        if len(candidates) < 2:
            return []

        embeddings = self._encode_semantic_candidates(encoder, candidates)
        if embeddings is None:
            return []

        return self._semantic_duplicate_groups(candidates, embeddings, seen_frags)

    def _semantic_candidates(
        self, fragments: List[CodeFragment], seen_frags: Set[int]
    ) -> List[CodeFragment]:
        candidates = [fragment for fragment in fragments if id(fragment) not in seen_frags]
        return candidates[: self.semantic_max_fragments]

    def _encode_semantic_candidates(self, encoder, candidates: List[CodeFragment]):
        texts = [self._semantic_text(fragment) for fragment in candidates]
        try:
            return encoder.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        except Exception as exc:
            self.semantic_warning = f"embedding encode failed: {exc}"
            return None

    def _semantic_duplicate_groups(
        self,
        candidates: List[CodeFragment],
        embeddings: Any,
        seen_frags: Set[int],
    ) -> List[DuplicateGroup]:
        groups: List[DuplicateGroup] = []
        used_indices: Set[int] = set()
        for i in range(len(candidates)):
            if i in used_indices:
                continue

            members = self._semantic_group_members(i, candidates, embeddings, used_indices)
            if len(members) < 2:
                continue

            groups.append(self._build_semantic_group(candidates, embeddings, members))
            self._mark_semantic_group_seen(candidates, members, used_indices, seen_frags)

        return groups

    def _semantic_group_members(
        self,
        start_index: int,
        candidates: List[CodeFragment],
        embeddings: Any,
        used_indices: Set[int],
    ) -> List[int]:
        members = [start_index]
        for candidate_index in range(start_index + 1, len(candidates)):
            if candidate_index in used_indices:
                continue
            similarity = self._cosine_similarity(
                embeddings[start_index], embeddings[candidate_index]
            )
            if similarity >= self.semantic_threshold:
                members.append(candidate_index)
        return members

    def _build_semantic_group(
        self, candidates: List[CodeFragment], embeddings: Any, members: List[int]
    ) -> DuplicateGroup:
        grouped = [candidates[index] for index in members]
        return DuplicateGroup(
            fragments=grouped,
            similarity=self._average_group_similarity(embeddings, members),
            representative_hash=self._semantic_group_hash(grouped),
            reason=f"Semantic embedding match ({self.semantic_model_name})",
        )

    def _mark_semantic_group_seen(
        self,
        candidates: List[CodeFragment],
        members: List[int],
        used_indices: Set[int],
        seen_frags: Set[int],
    ) -> None:
        used_indices.update(members)
        seen_frags.update(id(candidates[index]) for index in members)

    def _get_semantic_encoder(self):
        if self._semantic_model is not None:
            return self._semantic_model

        try:
            from sentence_transformers import SentenceTransformer
        except Exception:
            self.semantic_warning = "package sentence-transformers not installed"
            return None

        try:
            self._semantic_model = SentenceTransformer(self.semantic_model_name)
        except Exception as exc:
            self.semantic_warning = f"cannot load model '{self.semantic_model_name}': {exc}"
            return None

        return self._semantic_model

    def _semantic_text(self, fragment: CodeFragment) -> str:
        if fragment.name:
            return f"function {fragment.name}\n{fragment.content}"
        return fragment.content

    def _semantic_group_hash(self, fragments: List[CodeFragment]) -> str:
        fingerprint = "|".join(
            f"{frag.file}:{frag.start_line}:{frag.end_line}" for frag in fragments
        )
        return f"semantic:{hashlib.md5(fingerprint.encode()).hexdigest()}"

    def _average_group_similarity(self, embeddings: Any, indices: List[int]) -> float:
        if len(indices) < 2:
            return 1.0

        total = 0.0
        count = 0
        for pos, i in enumerate(indices):
            for j in indices[pos + 1 :]:
                total += self._cosine_similarity(embeddings[i], embeddings[j])
                count += 1
        return total / count if count else 1.0

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

    def _extract_fragments(self, file_path: Path) -> List[CodeFragment]:
        if file_path.suffix == ".py":
            return self._extract_py_fragments(file_path)
        else:
            return self._extract_regex_fragments(file_path)

    def _extract_py_fragments(self, file_path: Path) -> List[CodeFragment]:
        content = file_path.read_text()
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return []

        fragments = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                lineno = getattr(node, 'lineno', 0)
                end_lineno = getattr(node, 'end_lineno', 0)

                if lineno and end_lineno and (end_lineno - lineno + 1) >= self.min_lines:
                    s_hash = self._compute_structural_hash_py(node)
                    f_sig = self._compute_fuzzy_signature_py(node)

                    lines = content.splitlines()[lineno-1:end_lineno]
                    fragments.append(CodeFragment(
                        file=file_path,
                        start_line=lineno,
                        end_line=end_lineno,
                        content="\n".join(lines),
                        structural_hash=s_hash,
                        fuzzy_signature=f_sig,
                        name=node.name
                    ))
        return fragments

    def _extract_regex_fragments(self, file_path: Path) -> List[CodeFragment]:
        """
        Fallback structural extraction for JS/TS using regex.
        Identifies blocks between braces and normalizes them.
        """
        content = file_path.read_text()
        fragments = []

        # Simple heuristic: find functions/methods via braces
        # This is a fallback and not as accurate as AST
        matches = re.finditer(r'(?:function|const|let|async)?\s*([a-zA-Z0-9_]+)\s*\(.*?\)\s*\{', content)
        for match in matches:
            name = match.group(1)
            start_pos = match.start()

            # Find matching closing brace
            brace_count = 0
            end_pos = -1
            for i in range(start_pos, len(content)):
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i + 1
                        break

            if end_pos != -1:
                frag_content = content[start_pos:end_pos]
                lines = frag_content.splitlines()
                if len(lines) >= self.min_lines:
                    # Normalize for hashing
                    normalized = re.sub(r'[a-zA-Z0-9_]+', 'ID', frag_content)
                    normalized = re.sub(r'\s+', '', normalized)
                    s_hash = hashlib.md5(normalized.encode()).hexdigest()

                    start_line = content.count('\n', 0, start_pos) + 1
                    fragments.append(CodeFragment(
                        file=file_path,
                        start_line=start_line,
                        end_line=start_line + len(lines) - 1,
                        content=frag_content,
                        structural_hash=s_hash,
                        name=name
                    ))
        return fragments

    def _compute_structural_hash_py(self, node: ast.AST) -> str:
        class StructuralNormalizer(ast.NodeTransformer):
            def visit_Name(self, n): return ast.Name(id="VAR", ctx=n.ctx)
            def visit_Constant(self, n): return ast.Constant(value="VAL")
            def visit_arg(self, n): return ast.arg(arg="ARG", annotation=None)
            def visit_FunctionDef(self, n):
                n.name = "FUNC"
                return self.generic_visit(n)
            def visit_AsyncFunctionDef(self, n):
                n.name = "FUNC"
                return self.generic_visit(n)

        import copy
        node_copy = copy.deepcopy(node)
        normalized = StructuralNormalizer().visit(node_copy)
        structure = ast.dump(normalized, annotate_fields=False, include_attributes=False)
        return hashlib.md5(structure.encode()).hexdigest()

    def _compute_fuzzy_signature_py(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        args = node.args
        return f"sig:{len(args.args)}:{args.vararg is not None}:{args.kwarg is not None}"
