from __future__ import annotations
import ast
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional

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
    def __init__(self, min_lines: int = 4):
        self.min_lines = min_lines

    def scan(self, path: Path) -> List[DuplicateGroup]:
        exact_matches: Dict[str, List[CodeFragment]] = {}
        fuzzy_matches: Dict[str, List[CodeFragment]] = {}
        
        files = list(path.rglob("*.*"))
        for f in files:
            if any(p in f.parts for p in (".venv", "venv", "__pycache__", ".rebuild", ".git", "node_modules")):
                continue
            
            if f.suffix not in (".py", ".js", ".ts", ".jsx", ".tsx"):
                continue
                
            try:
                fragments = self._extract_fragments(f)
                for frag in fragments:
                    exact_matches.setdefault(frag.structural_hash, []).append(frag)
                    if frag.fuzzy_signature:
                        fuzzy_matches.setdefault(frag.fuzzy_signature, []).append(frag)
            except Exception:
                continue

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

        return sorted(groups, key=lambda g: len(g.fragments), reverse=True)

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
                if content[i] == '{': brace_count += 1
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
