"""
rebuild.nlp_service — Natural Language Processing for rebuild commands.

Converts natural language commands to DSL or CLI commands.

Examples:
  "analyze code for duplicates" -> analyze type:duplicates
  "walk last 7 days" -> walk days:7
  "generate evolution timeline" -> evolution
  "create PR with analysis" -> auto-pr
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple
from enum import Enum


class Intent(Enum):
    """Intents for natural language commands."""

    WALK = "walk"
    ANALYZE = "analyze"
    EVOLUTION = "evolution"
    AUTO_PR = "auto_pr"
    ACCELERATOR = "accelerator"
    RESTORE = "restore"
    SERVE = "serve"
    HELP = "help"


@dataclass
class NLPCommand:
    """Parsed natural language command."""

    intent: Intent
    parameters: Dict[str, str]
    confidence: float


class NLPService:
    """Service for parsing natural language commands into DSL/CLI commands."""

    def __init__(self):
        self._intent_patterns = {
            Intent.WALK: [
                r"walk",
                r"history",
                r"analyze history",
                r"test history",
            ],
            Intent.ANALYZE: [
                r"analyze",
                r"scan",
                r"check",
                r"duplicate",
                r"complexity",
                r"service",
            ],
            Intent.EVOLUTION: [
                r"evolution",
                r"timeline",
                r"code evolution",
                r"dependency graph",
            ],
            Intent.AUTO_PR: [
                r"pr",
                r"pull request",
                r"merge request",
                r"create pr",
                r"auto pr",
            ],
            Intent.ACCELERATOR: [
                r"accelerator",
                r"fast",
                r"quick",
                r"ultra",
            ],
            Intent.RESTORE: [
                r"restore",
                r"recover",
                r"recreate",
            ],
            Intent.SERVE: [
                r"serve",
                r"server",
                r"dashboard",
                r"report",
            ],
            Intent.HELP: [
                r"help",
                r"how to",
                r"what",
            ],
        }

        self._parameter_patterns = {
            "days": [
                r"(\d+)\s*days?",
                r"last\s+(\d+)\s*days?",
                r"past\s+(\d+)\s*days?",
            ],
            "repo": [
                r"repo[:\s]+([^\s]+)",
                r"repository[:\s]+([^\s]+)",
                r"project[:\s]+([^\s]+)",
            ],
            "type": [
                r"type[:\s]+(\w+)",
                r"analyze\s+(\w+)",
                r"scan\s+(\w+)",
            ],
            "platform": [
                r"platform[:\s]+(\w+)",
                r"on\s+(github|gitlab)",
            ],
            "dry_run": [
                r"dry[-\s]?run",
                r"test mode",
                r"no deploy",
            ],
            "semantic": [
                r"semantic",
                r"embedding",
            ],
        }

    def parse(self, text: str) -> NLPCommand:
        """Parse natural language command into structured command."""
        text_lower = text.lower().strip()

        # Detect intent
        intent, confidence = self._detect_intent(text_lower)

        # Extract parameters
        parameters = self._extract_parameters(text_lower)

        return NLPCommand(intent=intent, parameters=parameters, confidence=confidence)

    def _detect_intent(self, text: str) -> Tuple[Intent, float]:
        """Detect the intent from natural language text."""
        scores = {}
        for intent, patterns in self._intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text):
                    score += 1
            scores[intent] = score

        if not scores or max(scores.values()) == 0:
            return Intent.HELP, 0.5

        best_intent = max(scores, key=scores.get)
        confidence = min(scores[best_intent] / len(self._intent_patterns[best_intent]), 1.0)
        return best_intent, confidence

    def _extract_parameters(self, text: str) -> Dict[str, str]:
        """Extract parameters from natural language text."""
        parameters = {}

        for param_name, patterns in self._parameter_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    if param_name == "dry_run":
                        parameters[param_name] = "true"
                    elif param_name == "semantic":
                        parameters[param_name] = "true"
                    else:
                        parameters[param_name] = match.group(1)
                    break

        return parameters

    def to_dsl(self, command: NLPCommand) -> str:
        """Convert NLP command to DSL string."""
        dsl_parts = [command.intent.value]

        for key, value in command.parameters.items():
            if value == "true":
                dsl_parts.append(f"--{key}")
            else:
                dsl_parts.append(f"{key}:{value}")

        return " ".join(dsl_parts)

    def to_cli_args(self, command: NLPCommand) -> List[str]:
        """Convert NLP command to CLI arguments."""
        args = [command.intent.value]

        for key, value in command.parameters.items():
            if value == "true":
                args.append(f"--{key.replace('_', '-')}")
            else:
                args.append(f"--{key.replace('_', '-')}")
                args.append(value)

        return args
