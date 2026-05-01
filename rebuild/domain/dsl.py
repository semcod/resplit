"""
rebuild.dsl — Domain Specific Language for rebuild operations.

DSL Syntax Examples:
  walk repo:/path/to/repo days:7 deploy:docker-compose
  analyze repo:/path/to/repo type:duplicates min-lines:4
  evolution timeline:/path/to/timeline.json output:evolution.html
  auto-pr analysis:/path/to/analysis.json platform:github dry-run:true
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, List, Any
from pathlib import Path


class Command(Enum):
    """DSL command types."""
    WALK = "walk"
    ANALYZE = "analyze"
    EVOLUTION = "evolution"
    AUTO_PR = "auto_pr"
    ACCELERATOR = "accelerator"
    RESTORE = "restore"
    SERVE = "serve"


class AnalyzeType(Enum):
    """Analysis types for DSL."""
    DUPLICATES = "duplicates"
    SERVICES = "services"
    TRUTH = "truth"
    MULTI_REPO = "multi_repo"


@dataclass
class DSLCommand:
    """Parsed DSL command."""
    command: Command
    parameters: Dict[str, Any] = field(default_factory=dict)
    flags: Dict[str, bool] = field(default_factory=dict)


class DSLParser:
    """Parser for rebuild DSL syntax."""

    def __init__(self):
        pass

    def parse(self, dsl_string: str) -> DSLCommand:
        """Parse a DSL string into a DSLCommand."""
        parts = dsl_string.strip().split()
        if not parts:
            raise ValueError("Empty DSL command")

        command_str = parts[0].lower()
        try:
            command = Command(command_str.replace("-", "_"))
        except ValueError:
            raise ValueError(f"Unknown command: {command_str}")

        parameters = {}
        flags = {}

        for part in parts[1:]:
            if "=" in part:
                key, value = part.split("=", 1)
                # Handle boolean flags
                if value.lower() in ("true", "false"):
                    flags[key] = value.lower() == "true"
                # Handle numeric values
                elif value.isdigit():
                    parameters[key] = int(value)
                else:
                    parameters[key] = value
            elif ":" in part:
                key, value = part.split(":", 1)
                # Handle boolean flags
                if value.lower() in ("true", "false"):
                    flags[key] = value.lower() == "true"
                # Handle numeric values
                elif value.isdigit():
                    parameters[key] = int(value)
                else:
                    parameters[key] = value
            else:
                # Flag without value
                flags[part] = True

        return DSLCommand(command=command, parameters=parameters, flags=flags)

    def parse_file(self, dsl_file: Path) -> List[DSLCommand]:
        """Parse a DSL file with multiple commands."""
        content = dsl_file.read_text()
        commands = []
        for line in content.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                commands.append(self.parse(line))
        return commands


class DSLInterpreter:
    """Interpreter for executing parsed DSL commands."""

    def __init__(self):
        self._command_handlers = {
            Command.WALK: self._handle_walk,
            Command.ANALYZE: self._handle_analyze,
            Command.EVOLUTION: self._handle_evolution,
            Command.AUTO_PR: self._handle_auto_pr,
            Command.ACCELERATOR: self._handle_accelerator,
            Command.RESTORE: self._handle_restore,
            Command.SERVE: self._handle_serve,
        }

    def execute(self, command: DSLCommand) -> Dict[str, Any]:
        """Execute a DSL command."""
        handler = self._command_handlers.get(command.command)
        if not handler:
            raise ValueError(f"No handler for command: {command.command}")
        return handler(command)

    def execute_file(self, dsl_file: Path) -> List[Dict[str, Any]]:
        """Parse and execute a DSL file."""
        parser = DSLParser()
        commands = parser.parse_file(dsl_file)
        results = []
        for cmd in commands:
            results.append(self.execute(cmd))
        return results

    def _handle_walk(self, command: DSLCommand) -> Dict[str, Any]:
        """Handle walk command."""
        params = command.parameters
        flags = command.flags

        repo = params.get("repo", ".")
        days = params.get("days", 30)
        deploy = params.get("deploy", "auto")
        health_url = params.get("health_url", "http://localhost:8003/api/health")
        base_url = params.get("base_url", "http://localhost:8003")
        output = params.get("output", ".rebuild")
        dry_run = flags.get("dry_run", False)
        replay = flags.get("replay", False)

        return {
            "command": "walk",
            "repo": repo,
            "days": days,
            "deploy": deploy,
            "health_url": health_url,
            "base_url": base_url,
            "output": output,
            "dry_run": dry_run,
            "replay": replay,
            "status": "parsed",
        }

    def _handle_analyze(self, command: DSLCommand) -> Dict[str, Any]:
        """Handle analyze command."""
        params = command.parameters
        flags = command.flags

        repo = params.get("repo", ".")
        analyze_type = params.get("type", "duplicates")
        min_lines = params.get("min_lines", 4)
        semantic = flags.get("semantic", False)

        return {
            "command": "analyze",
            "repo": repo,
            "type": analyze_type,
            "min_lines": min_lines,
            "semantic": semantic,
            "status": "parsed",
        }

    def _handle_evolution(self, command: DSLCommand) -> Dict[str, Any]:
        """Handle evolution command."""
        params = command.parameters

        timeline = params.get("timeline")
        output = params.get("output", "evolution.html")
        title = params.get("title", "Code Evolution")

        return {
            "command": "evolution",
            "timeline": timeline,
            "output": output,
            "title": title,
            "status": "parsed",
        }

    def _handle_auto_pr(self, command: DSLCommand) -> Dict[str, Any]:
        """Handle auto-pr command."""
        params = command.parameters
        flags = command.flags

        analysis = params.get("analysis")
        platform = params.get("platform", "github")
        dry_run = flags.get("dry_run", False)

        return {
            "command": "auto_pr",
            "analysis": analysis,
            "platform": platform,
            "dry_run": dry_run,
            "status": "parsed",
        }

    def _handle_accelerator(self, command: DSLCommand) -> Dict[str, Any]:
        """Handle accelerator command."""
        params = command.parameters

        repo = params.get("repo", ".")
        days = params.get("days", 30)
        parallel = params.get("parallel", 10)

        return {
            "command": "accelerator",
            "repo": repo,
            "days": days,
            "parallel": parallel,
            "status": "parsed",
        }

    def _handle_restore(self, command: DSLCommand) -> Dict[str, Any]:
        """Handle restore command."""
        params = command.parameters

        endpoint = params.get("endpoint")
        repo = params.get("repo", ".")
        output = params.get("output", "./restored")

        return {
            "command": "restore",
            "endpoint": endpoint,
            "repo": repo,
            "output": output,
            "status": "parsed",
        }

    def _handle_serve(self, command: DSLCommand) -> Dict[str, Any]:
        """Handle serve command."""
        params = command.parameters

        results_dir = params.get("results_dir", ".rebuild")
        port = params.get("port", 7821)

        return {
            "command": "serve",
            "results_dir": results_dir,
            "port": port,
            "status": "parsed",
        }
