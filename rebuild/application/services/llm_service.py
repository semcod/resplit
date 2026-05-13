from __future__ import annotations
import os
from typing import Optional
import litellm
from dotenv import load_dotenv
from rich.console import Console


class LLMService:
    """
    Service for interacting with LLMs via LiteLLM.
    Supports summarizing refactor plans and generating PR descriptions.
    """

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        load_dotenv()
        self.model = os.getenv("LLM_MODEL", "openrouter/qwen/qwen3-coder-next")
        self.api_key = os.getenv("OPENROUTER_API_KEY")

        if not self.api_key:
            self.console.print(
                "[yellow]⚠ OPENROUTER_API_KEY nie został znaleziony w .env. Funkcje AI będą wyłączone.[/yellow]"
            )

    def is_available(self) -> bool:
        return bool(self.api_key)

    def summarize_refactor_plan(self, suggestions_data: str) -> str:
        if not self.is_available():
            return "AI Summary unavailable (no API key)."

        prompt = f"""
        Analyze the following refactoring suggestions for a codebase and provide a concise,
        high-level executive summary. Focus on the architectural impact and the "why".

        Suggestions:
        {suggestions_data}

        Summary:
        """

        try:
            response = litellm.completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                api_key=self.api_key,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating summary: {e}"

    def generate_pr_description(self, plan_data: str) -> str:
        if not self.is_available():
            return "AI PR Description unavailable."

        prompt = f"""
        Generate a professional Pull Request description in Markdown based on this refactoring plan.
        Include:
        1. Overview of changes
        2. Rationale (why this is needed)
        3. Key components affected
        4. Verification steps

        Plan:
        {plan_data}

        PR Description:
        """

        try:
            response = litellm.completion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                api_key=self.api_key,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating PR description: {e}"
