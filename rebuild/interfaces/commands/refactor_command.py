from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel


def _generate_refactor_plan(path: Path):
    from ...analysis.duplication_engine import DuplicationEngine
    from ...analysis.service_similarity import ServiceSimilarityAnalyzer
    from ...analysis.service_graph import ServiceGraphBuilder
    from ...refactor.recommendation_engine import RecommendationEngine

    dup_engine = DuplicationEngine()
    duplicates = dup_engine.scan(path)

    services_path = path / "rebuild/application/services"
    sim_analyzer = ServiceSimilarityAnalyzer()
    similarities = sim_analyzer.analyze_directory(services_path) if services_path.exists() else []

    graph_builder = ServiceGraphBuilder(services_path.resolve()) if services_path.exists() else None
    graph = graph_builder.build() if graph_builder else {}
    cycles = graph_builder.detect_cycles() if graph_builder else []

    rec_engine = RecommendationEngine()
    return rec_engine.generate_plan(duplicates, similarities, graph, cycles)


def plan_command(path: Path, ai: bool, console: Console) -> None:
    suggestions = _generate_refactor_plan(path)

    if not suggestions:
        console.print(
            "[green]✓ System nie znalazł krytycznych problemów wymagających refaktoru.[/green]"
        )
        return

    if ai:
        from ...application.services.llm_service import LLMService

        llm = LLMService(console)
        if llm.is_available():
            with console.status("[bold cyan]AI analizuje plan...[/bold cyan]"):
                plan_text = "\n".join([f"- {s.title}: {s.description}" for s in suggestions])
                summary = llm.summarize_refactor_plan(plan_text)
                console.print(
                    Panel(
                        summary,
                        title="[bold cyan]AI Executive Summary[/bold cyan]",
                        border_style="cyan",
                    )
                )

    console.print(f"\n[bold yellow]Zaproponowane działania ({len(suggestions)}):[/bold yellow]\n")
    for i, s in enumerate(suggestions, 1):
        color = "red" if s.impact == "HIGH" else "yellow" if s.impact == "MEDIUM" else "blue"
        console.print(f"{i}. [bold]{s.title}[/bold] (Impact: [{color}]{s.impact}[/{color}])")
        console.print(f"   {s.description}")
        if s.rationale:
            console.print(f"   [dim]Racja: {s.rationale}[/dim]")
        if s.files:
            console.print(f"   Pliki: {', '.join(str(f.name) for f in s.files[:5])}")
        console.print("")


def pr_command(path: Path, console: Console) -> None:
    suggestions = _generate_refactor_plan(path)
    if not suggestions:
        console.print("[yellow]Brak zmian do opisania.[/yellow]")
        return

    from ...application.services.llm_service import LLMService

    llm = LLMService(console)
    if not llm.is_available():
        console.print("[red]✗ AI Service niedostępny. Sprawdź .env i OPENROUTER_API_KEY.[/red]")
        return

    with console.status("[bold cyan]Generowanie opisu PR...[/bold cyan]"):
        plan_text = "\n".join(
            [f"- {s.title}: {s.description} (Rationale: {s.rationale})" for s in suggestions]
        )
        description = llm.generate_pr_description(plan_text)

    console.print("\n[bold green]Gotowy opis Pull Requesta:[/bold green]\n")
    console.print(Markdown(description))


def execute_command(path: Path, force: bool, console: Console) -> None:
    from ...refactor.refactor_executor import RefactorExecutor

    suggestions = _generate_refactor_plan(path)
    if not suggestions:
        console.print("[green]Brak działań do wykonania.[/green]")
        return

    executor = RefactorExecutor(console)
    for s in suggestions:
        if not force:
            confirm = typer.confirm(f"Czy wykonać: {s.title}?")
            if not confirm:
                continue
        success = executor.execute_suggestion(s)
        if success:
            console.print(f"[green]✓ Wykonano: {s.title}[/green]")
        else:
            console.print(f"[red]✗ Błąd wykonania: {s.title}[/red]")
