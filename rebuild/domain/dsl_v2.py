"""
rebuild DSL v2 — Pydantic-validated DSL with NLP support.

DSL syntax (key:value pairs after command name):
  walk repo:/my/app days:14 deploy:none dry-run
  analyze repo:/my/app type:duplicates min-lines:4 semantic
  snapshot dir:/snaps db:postgres name:daily max:10
  prune dir:/snaps keep:5
  plugins
  history dir:.rebuild limit:30
  help

NLP examples (mapped to DSL):
  "przeanalizuj duplikaty w /my/app od 14 dni"
  "walk the repo at /srv/app for the last 7 days without deploying"
  "show me the last 30 walk results"
"""
from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type

from pydantic import BaseModel, Field, ValidationError

from ..application.commands.base import Command
from ..application.commands.walk_commands import WalkCommand
from ..application.commands.analyze_commands import AnalyzeCommand
from ..application.commands.snapshot_commands import (
    CreateSnapshotCommand, PruneSnapshotsCommand,
)


# ─── DSL Schema (Pydantic) ────────────────────────────────────────────────────

class WalkDSL(BaseModel):
    repo: str = "."
    days: int = Field(30, ge=1)
    deploy: str = "auto"
    output: str = ".rebuild"
    health_url: str = "http://localhost:8000/health"
    base_url: str = "http://localhost:8000"
    screenshots: bool = False
    dry_run: bool = False
    replay: bool = False
    health_timeout: int = Field(60, ge=1)


class AnalyzeDSL(BaseModel):
    repo: str = "."
    type: str = "duplicates"
    min_lines: int = Field(6, ge=1)
    semantic: bool = False
    threshold: float = Field(0.85, ge=0.0, le=1.0)


class SnapshotDSL(BaseModel):
    dir: str
    db: str = "postgres"
    name: Optional[str] = None
    commit: Optional[str] = None
    max: int = Field(10, ge=0)
    db_name: str = "app"
    db_user: str = "postgres"
    container: str = "db"


class PruneDSL(BaseModel):
    dir: str
    keep: int = Field(5, ge=0)


class HistoryDSL(BaseModel):
    dir: str = ".rebuild"
    limit: int = Field(100, ge=1)
    date_from: Optional[str] = None
    date_to: Optional[str] = None


# ─── Token → schema mapping ───────────────────────────────────────────────────

_COMMAND_SCHEMAS: Dict[str, Tuple[str, Type[BaseModel]]] = {
    "walk": ("walk", WalkDSL),
    "analyze": ("analyze", AnalyzeDSL),
    "analyse": ("analyze", AnalyzeDSL),
    "snapshot": ("snapshot", SnapshotDSL),
    "prune": ("prune", PruneDSL),
    "history": ("history", HistoryDSL),
    "plugins": ("plugins", BaseModel),
    "help": ("help", BaseModel),
}

_ALIAS_MAP: Dict[str, str] = {
    "dry-run": "dry_run",
    "min-lines": "min_lines",
    "min_lines": "min_lines",
    "health-url": "health_url",
    "base-url": "base_url",
    "health-timeout": "health_timeout",
    "date-from": "date_from",
    "date-to": "date_to",
}


# ─── Parser ───────────────────────────────────────────────────────────────────

class DSLParseError(ValueError):
    pass


class DSLParser:
    """
    Parse a DSL string into a validated Pydantic model,
    then optionally convert to a CQRS Command.

    >>> parser = DSLParser()
    >>> model = parser.parse("walk repo:/my/app days:7 dry-run")
    >>> isinstance(model, WalkDSL)
    True
    """

    def parse_tokens(self, dsl_string: str) -> Tuple[str, Dict[str, Any]]:
        """Return (command_name, raw_kwargs_dict)."""
        try:
            parts = shlex.split(dsl_string.strip())
        except ValueError as e:
            raise DSLParseError(f"DSL tokenize error: {e}") from e

        if not parts:
            raise DSLParseError("Empty DSL command")

        command_str = parts[0].lower()
        if command_str not in _COMMAND_SCHEMAS:
            raise DSLParseError(
                f"Unknown command '{command_str}'. "
                f"Valid: {sorted(_COMMAND_SCHEMAS)}"
            )

        kwargs: Dict[str, Any] = {}
        for token in parts[1:]:
            if ":" in token:
                key, _, val = token.partition(":")
                key = _ALIAS_MAP.get(key, key)
                # coerce booleans
                if val.lower() in ("true", "yes", "1"):
                    kwargs[key] = True
                elif val.lower() in ("false", "no", "0"):
                    kwargs[key] = False
                elif val.isdigit():
                    kwargs[key] = int(val)
                else:
                    try:
                        kwargs[key] = float(val)
                    except ValueError:
                        kwargs[key] = val
            elif "=" in token:
                key, _, val = token.partition("=")
                key = _ALIAS_MAP.get(key, key)
                kwargs[key] = val
            else:
                # bare flag → True
                key = _ALIAS_MAP.get(token, token)
                kwargs[key] = True

        return command_str, kwargs

    def parse(self, dsl_string: str) -> BaseModel:
        """Parse and validate DSL string. Returns the matching Pydantic schema."""
        command_str, kwargs = self.parse_tokens(dsl_string)
        _, schema_cls = _COMMAND_SCHEMAS[command_str]
        try:
            return schema_cls(**kwargs)
        except ValidationError as e:
            raise DSLParseError(
                f"DSL validation error for '{command_str}': {e}"
            ) from e

    def to_cqrs_command(self, dsl_string: str) -> Optional[Command]:
        """Parse DSL and convert to a CQRS Command (or None for non-command verbs)."""
        command_str, kwargs = self.parse_tokens(dsl_string)
        _, schema_cls = _COMMAND_SCHEMAS[command_str]

        try:
            model = schema_cls(**kwargs)
        except ValidationError as e:
            raise DSLParseError(f"Validation failed: {e}") from e

        if command_str == "walk":
            m: WalkDSL = model  # type: ignore
            return WalkCommand(
                repo=m.repo,
                days=m.days,
                deploy=m.deploy,
                output=m.output,
                health_url=m.health_url,
                base_url=m.base_url,
                screenshots=m.screenshots,
                dry_run=m.dry_run,
                replay=m.replay,
                health_timeout=m.health_timeout,
            )
        if command_str == "analyze":
            m2: AnalyzeDSL = model  # type: ignore
            return AnalyzeCommand(
                repo=m2.repo,
                analysis_type=m2.type,
                min_lines=m2.min_lines,
                semantic=m2.semantic,
                semantic_threshold=m2.threshold,
            )
        if command_str == "snapshot":
            m3: SnapshotDSL = model  # type: ignore
            return CreateSnapshotCommand(
                snapshot_dir=m3.dir,
                db_container=m3.container,
                db_type=m3.db,
                db_name=m3.db_name,
                db_user=m3.db_user,
                name=m3.name,
                commit_sha=m3.commit,
                max_snapshots=m3.max,
            )
        if command_str == "prune":
            m4: PruneDSL = model  # type: ignore
            return PruneSnapshotsCommand(snapshot_dir=m4.dir, keep=m4.keep)

        return None  # plugins, help, history → handled by query side


# ─── NLP Mapper ───────────────────────────────────────────────────────────────

_NLP_RULES: List[Tuple[str, str]] = [
    # English — walk
    (r"walk\s+(?:the\s+)?repo\s+(?:at\s+)?(\S+)", r"walk repo:\1"),
    (r"walk\s+(\S+)\s+for\s+(?:the\s+)?last\s+(\d+)\s+days?", r"walk repo:\1 days:\2"),
    (r"walk\s+(\S+)\s+days?[:\s]+(\d+)", r"walk repo:\1 days:\2"),
    (r"run\s+walk\s+on\s+(\S+)", r"walk repo:\1"),
    (r"without\s+deploy(?:ing)?", r"deploy:none"),
    (r"no\s+deploy", r"deploy:none"),
    (r"dry[- ]run", r"dry-run"),
    (r"dry\s+run", r"dry-run"),
    # English — analyze
    (r"analy[sz]e\s+duplicates?\s+in\s+(\S+)", r"analyze repo:\1 type:duplicates"),
    (r"find\s+duplicates?\s+in\s+(\S+)", r"analyze repo:\1 type:duplicates"),
    (r"check\s+services?\s+in\s+(\S+)", r"analyze repo:\1 type:services"),
    (r"analy[sz]e\s+(\S+)", r"analyze repo:\1"),
    # Polish — walk
    (r"przejdź\s+po\s+repo\s+(\S+)", r"walk repo:\1"),
    (r"walk\s+repo\s+(\S+)\s+przez\s+(\d+)\s+dni", r"walk repo:\1 days:\2"),
    (r"przez\s+ostatnie\s+(\d+)\s+dni", r"days:\1"),
    (r"bez\s+deploy(?:u)?", r"deploy:none"),
    # Polish — analyze
    (r"znajdź\s+duplikaty\s+w\s+(\S+)", r"analyze repo:\1 type:duplicates"),
    (r"przeanalizuj\s+duplikaty\s+w\s+(\S+)", r"analyze repo:\1 type:duplicates"),
    (r"przeanalizuj\s+(\S+)", r"analyze repo:\1"),
    # Snapshots
    (r"utwórz\s+snapshot", r"snapshot"),
    (r"create\s+snapshot\s+for\s+(\S+)", r"snapshot dir:\1"),
    (r"prune\s+snapshots?\s+(?:in\s+)?(\S+)\s+keep\s+(\d+)", r"prune dir:\1 keep:\2"),
    # History / plugins
    (r"pokaż\s+historię", r"history"),
    (r"show\s+(?:walk\s+)?history", r"history"),
    (r"list\s+plugins?", r"plugins"),
    (r"pokaż\s+pluginy", r"plugins"),
]


class NLPMapper:
    """
    Rule-based NLP → DSL mapper.

    Uses ordered regex substitution rules to convert natural language
    (English + Polish) into DSL strings parseable by DSLParser.

    For better results, replace with an LLM call (see _llm_fallback).
    """

    def __init__(self, use_llm: bool = False, llm_service: Any = None) -> None:
        self._use_llm = use_llm
        self._llm_service = llm_service
        self._compiled = [
            (re.compile(pattern, re.IGNORECASE), replacement)
            for pattern, replacement in _NLP_RULES
        ]

    def to_dsl(self, text: str) -> str:
        """Convert natural language text to a DSL string."""
        normalized = text.strip().lower()

        # Direct command pass-through
        first_word = normalized.split()[0] if normalized.split() else ""
        if first_word in _COMMAND_SCHEMAS:
            return text.strip()

        result = normalized
        for pattern, replacement in self._compiled:
            result = pattern.sub(replacement, result)

        # Collapse excess whitespace and clean up
        result = re.sub(r"\s+", " ", result).strip()

        if self._use_llm and self._llm_service and not self._looks_like_dsl(result):
            return self._llm_fallback(text)

        return result

    def _looks_like_dsl(self, text: str) -> bool:
        """Heuristic: does this look like a valid DSL string?"""
        first = text.split()[0] if text.split() else ""
        return first in _COMMAND_SCHEMAS

    def _llm_fallback(self, text: str) -> str:
        """Call LLM to convert natural language to DSL (optional)."""
        if self._llm_service is None:
            return text
        prompt = (
            "Convert this request to a rebuild DSL command. "
            "Valid commands: walk, analyze, snapshot, prune, history, plugins. "
            f"Request: {text}\n"
            "DSL:"
        )
        try:
            response = self._llm_service.complete(prompt)
            return response.strip()
        except Exception:
            return text


# ─── Shell REPL ───────────────────────────────────────────────────────────────

class DSLShell:
    """
    Interactive REPL for the rebuild DSL.

    Usage::

        shell = DSLShell(command_bus=bus, query_bus=qbus)
        shell.run()   # blocking
    """

    PROMPT = "rebuild> "
    HELP_TEXT = """
rebuild DSL Shell

Commands:
  walk repo:<path> [days:<n>] [deploy:<method>] [dry-run] [replay]
  analyze repo:<path> [type:<t>] [min-lines:<n>] [semantic]
  snapshot dir:<path> [db:<type>] [name:<n>] [max:<n>]
  prune dir:<path> [keep:<n>]
  history [dir:<path>] [limit:<n>]
  plugins
  help
  exit / quit

Natural language also works:
  "przeanalizuj duplikaty w /my/app"
  "walk /my/repo for the last 7 days without deploy"
"""

    def __init__(
        self,
        command_bus: Any = None,
        query_bus: Any = None,
        nlp: bool = True,
    ) -> None:
        self._parser = DSLParser()
        self._nlp = NLPMapper() if nlp else None
        self._command_bus = command_bus
        self._query_bus = query_bus

    def run(self) -> None:
        """Start blocking REPL."""
        print(self.HELP_TEXT)
        while True:
            try:
                line = input(self.PROMPT).strip()
            except (EOFError, KeyboardInterrupt):
                print("\nbye.")
                break

            if not line or line.startswith("#"):
                continue
            if line.lower() in ("exit", "quit", "q"):
                print("bye.")
                break
            if line.lower() == "help":
                print(self.HELP_TEXT)
                continue

            self._process(line)

    def _process(self, line: str) -> None:
        """Process one line — parse, dispatch, print result."""
        dsl_str = line
        if self._nlp:
            dsl_str = self._nlp.to_dsl(line)
            if dsl_str != line:
                print(f"  → DSL: {dsl_str}")

        try:
            cmd = self._parser.to_cqrs_command(dsl_str)
        except DSLParseError as e:
            print(f"  ✗ {e}")
            return

        if cmd is None:
            # Non-command verbs: plugins, history
            print(f"  → {dsl_str} (query — use REST API or CLI)")
            return

        if self._command_bus is None:
            print(f"  ✓ Parsed: {cmd.model_dump()}")
            return

        try:
            result = self._command_bus.dispatch(cmd)
            print(f"  ✓ {result.model_dump()}")
        except Exception as e:
            print(f"  ✗ Error: {e}")

    def process_line(self, line: str) -> Optional[Any]:
        """Process one line programmatically (for testing). Returns command or None."""
        dsl_str = self._nlp.to_dsl(line) if self._nlp else line
        try:
            return self._parser.to_cqrs_command(dsl_str)
        except DSLParseError:
            return None
