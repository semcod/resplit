"""
rebuild CLI — główny punkt wejścia.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel

from .. import __version__
from ..domain.models import DeployMethod, WalkConfig
from ..domain.day_result import DayResult
from ..application.pipeline import Pipeline
from ..application.services.history_service import HistoryService
from ..application.services.reporter_service import ReporterService
from ..application.services.deploy_service import DeployService
from ..application.services.restore_service import RestoreService

app = typer.Typer(
    name="rebuild",
    help="Historical deployment analysis — walk git history, test endpoints, capture screenshots.",
    rich_markup_mode="markdown",
    no_args_is_help=True,
)
analyze_app = typer.Typer(help="Analyze codebase for duplicates, quality, and evolution.")
refactor_app = typer.Typer(help="Generate and execute refactoring plans.")

app.add_typer(analyze_app, name="analyze")
app.add_typer(refactor_app, name="refactor")

console = Console()


@app.command()
def init(
    path: Path = typer.Argument(Path("."), help="Katalog w którym zainicjować projekt"),
    force: bool = typer.Option(False, "--force", help="Nadpisz istniejący rebuild.yaml"),
) -> None:
    """Zainicjuj nowy projekt rebuild i wygeneruj domyślną konfigurację."""
    config_file = path / "rebuild.yaml"
    if config_file.exists() and not force:
        console.print(f"[yellow]⚠ {config_file} już istnieje. Użyj --force aby nadpisać.[/yellow]")
        return

    template_path = Path(__file__).parent.parent / "infrastructure" / "config_template.yaml"
    if not template_path.exists():
        # Fallback if template missing
        config_content = "project:\n  name: 'service'\n  repo: '.'"
    else:
        config_content = template_path.read_text()

    config_file.write_text(config_content)
    console.print(f"[green]✓ Zainicjowano projekt w {path}[/green]")
    console.print(f"  Konfiguracja: {config_file}")
    console.print("  Edytuj plik aby dopasować workflow i metody deploy.")


@app.command()
def walk(
    repo: Path = typer.Argument(Path("."), help="Ścieżka do repozytorium"),
    days: int = typer.Option(30, help="Ile dni wstecz"),
    date_from: Optional[str] = typer.Option(None, "--from", help="Data od YYYY-MM-DD"),
    date_to: Optional[str] = typer.Option(None, "--to", help="Data do YYYY-MM-DD"),
    output: Path = typer.Option(Path(".rebuild"), help="Katalog wyjściowy"),
    deploy: str = typer.Option("auto", help="Metoda deploy: auto|docker-compose|uvicorn|none"),
    health_url: str = typer.Option("http://localhost:8003/api/health", help="URL health check"),
    base_url: str = typer.Option("http://localhost:8003", help="Bazowy URL usługi"),
    screenshots: bool = typer.Option(True, help="Rób zrzuty ekranu (wymaga playwright)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Tylko skanuj, bez deploy"),
) -> None:
    """Przejdź historię git dzień po dniu, deployuj i testuj endpointy."""
    repo = repo.resolve()
    if not (repo / ".git").exists():
        console.print(f"[red]✗ {repo} nie jest repozytorium git[/red]")
        raise typer.Exit(1)

    # Auto-init if config missing
    if not (repo / "rebuild.yaml").exists():
        console.print("[dim]rebuild.yaml nie istnieje. Generowanie domyślnej konfiguracji...[/dim]")
        init(repo)

    # Wykrywanie metody deploy
    deploy_svc = DeployService(WalkConfig(repo_path=repo))
    if deploy == "auto":
        method = deploy_svc.detect_deploy_method(repo) if not dry_run else DeployMethod.NONE
    else:
        method = DeployMethod(deploy)

    config = WalkConfig(
        repo_path=repo,
        output_dir=output,
        days=days,
        date_from=date.fromisoformat(date_from) if date_from else None,
        date_to=date.fromisoformat(date_to) if date_to else None,
        deploy_method=method,
        health_url=health_url,
        base_url=base_url,
        screenshots=screenshots,
        dry_run=dry_run,
    )

    console.print(f"\n[bold]rebuild walk[/bold] v{__version__}")
    console.print(f"  repo:   {repo}")
    console.print(f"  output: {output}")
    console.print(f"  deploy: {method.value}")
    console.print(f"  days:   {days}\n")

    pipeline = Pipeline(config, console=console)
    all_results = pipeline.run()

    if all_results:
        console.print(f"\n[bold green]✓ Gotowe![/bold green]  Raport: {output / 'index.html'}")
        _print_summary_table(all_results)
    else:
        console.print("[yellow]Brak wyników do wyświetlenia.[/yellow]")


@app.command()
def restore(
    endpoint: str = typer.Argument(help="Ścieżka endpointu np. /api/health"),
    repo: Path = typer.Argument(Path("."), help="Repozytorium"),
    output: Path = typer.Option(Path("restored"), help="Katalog docelowy projektu"),
    results_dir: Path = typer.Option(Path(".rebuild"), help="Katalog z wynikami walk"),
) -> None:
    """Przywróć działający endpoint jako izolowany projekt."""
    restore_svc = RestoreService(repo, console=console)
    day = restore_svc.find_last_working_day(endpoint, results_dir)
    if not day:
        console.print(f"[red]✗ Nie znaleziono działającego dnia dla {endpoint}[/red]")
        raise typer.Exit(1)

    console.print(f"Ostatni działający dzień: [bold]{day}[/bold]")
    target = output / endpoint.strip("/").replace("/", "-")
    restore_svc.extract_endpoint(endpoint, day, target)
    console.print(f"[green]✓ Przywrócono do: {target}[/green]")


@app.command()
def report(
    results_dir: Path = typer.Option(Path(".rebuild"), help="Katalog z wynikami walk"),
) -> None:
    """Wygeneruj zbiorczy raport z istniejących wyników."""
    history_svc = HistoryService()
    reporter_svc = ReporterService()
    
    all_results = history_svc.execute(results_dir)
    if not all_results:
        console.print("[yellow]Brak wyników do raportowania.[/yellow]")
        return

    reporter_svc.save_timeline_index(all_results, results_dir)
    console.print(f"[green]✓ Wygenerowano: {results_dir / 'index.html'}[/green]")


@app.command()
def dashboard(
    results_dir: Path = typer.Option(Path(".rebuild"), help="Katalog z wynikami walk"),
    repo: Optional[Path] = typer.Option(None, help="Repo do pobrania CC (opcjonalnie)"),
) -> None:
    """Wygeneruj dashboard porównawczy: timeline health% + CC."""
    from .dashboard import generate_dashboard
    history_svc = HistoryService()
    
    all_results = history_svc.execute(results_dir)
    if not all_results:
        console.print("[yellow]Brak wyników w katalogu.[/yellow]")
        raise typer.Exit(0)

    out = generate_dashboard(all_results, results_dir, repo=repo)
    console.print(f"[green]✓ Dashboard: {out}[/green]")


@app.command()
def tui() -> None:
    """Interaktywne menu TUI: wybór projektu → walk → historia → diff → restore."""
    from .tui import launch_tui
    launch_tui()


@app.command()
def version() -> None:
    """Pokaż wersję rebuild."""
    console.print(f"rebuild v{__version__}")


# ──────────────────────────────────────────────
# analyze commands (Queries)
# ──────────────────────────────────────────────

@analyze_app.command()
def duplicates(
    path: Path = typer.Argument(Path("."), help="Ścieżka do skanowania"),
    min_lines: int = typer.Option(4, help="Minimalna liczba linii dla duplikatu"),
) -> None:
    """[Query] Znajdź strukturalne i semantyczne duplikaty kodu."""
    from ..analysis.duplication_engine import DuplicationEngine
    
    engine = DuplicationEngine(min_lines=min_lines)
    groups = engine.scan(path)
    
    if not groups:
        console.print("[green]✓ Nie znaleziono duplikatów.[/green]")
        return
        
    console.print(f"\n[bold red]Znaleziono {len(groups)} grup duplikatów:[/bold red]\n")
    for i, group in enumerate(groups, 1):
        console.print(f"[bold]Grupa {i} (Similarity: {group.similarity:.2f}, Reason: {group.reason})[/bold]")
        for frag in group.fragments:
            console.print(f"  - {frag.file}:{frag.start_line} ([cyan]{frag.name or 'block'}[/cyan])")
        console.print("")

@analyze_app.command()
def services(
    path: Path = typer.Argument(Path("rebuild/application/services"), help="Katalog z serwisami"),
) -> None:
    """[Query] Wykryj nakładające się odpowiedzialności i powiązania między serwisami."""
    from ..analysis.service_graph import ServiceGraphBuilder
    from ..analysis.service_similarity import ServiceSimilarityAnalyzer
    
    console.print("\n[bold cyan]Budowanie grafu usług...[/bold cyan]")
    builder = ServiceGraphBuilder(path.resolve())
    nodes = builder.build()
    
    tree = Tree("[bold yellow]Architecture Graph[/bold yellow]")
    for name, node in nodes.items():
        branch = tree.add(f"[bold cyan]{name}[/bold cyan] ({len(node.methods)} methods)")
        if node.dependencies:
            deps = branch.add("[dim]Dependencies[/dim]")
            for d in node.dependencies:
                deps.add(f"[blue]{d}[/blue]")
    console.print(tree)
    
    cycles = builder.detect_cycles()
    if cycles:
        console.print("\n[bold red]⚠️ Wykryto cykle w zależnościach:[/bold red]")
        for c in cycles:
            console.print(f"  {' → '.join(c)}")
            
    analyzer = ServiceSimilarityAnalyzer()
    similarities = analyzer.analyze_directory(path)
    if similarities:
        console.print(f"\n[bold yellow]Wykryto {len(similarities)} nakładających się usług:[/bold yellow]")
        for sim in similarities:
            console.print(f"  [bold]{sim.service_a}[/bold] ↔ [bold]{sim.service_b}[/bold] (Overlap: [red]{sim.overlap:.2f}[/red])")

@analyze_app.command()
def truth(
    file: Path = typer.Argument(..., help="Plik do analizy"),
    function: str = typer.Argument(..., help="Nazwa funkcji do analizy historii"),
    repo: Path = typer.Option(Path("."), help="Ścieżka do repo"),
) -> None:
    """[Query] Znajdź 'najprawdziwszą' wersję funkcji w historii git."""
    from ..analysis.git_truth_analyzer import GitTruthAnalyzer
    
    analyzer = GitTruthAnalyzer(repo.resolve())
    qualities = analyzer.analyze_function_history(file, function)
    
    if not qualities:
        console.print(f"[yellow]Nie znaleziono historii dla funkcji {function} w pliku {file}[/yellow]")
        return
        
    console.print(f"\n[bold green]Historia jakości funkcji {function}:[/bold green]\n")
    table = Table(show_header=True)
    table.add_column("Commit", style="cyan")
    table.add_column("Data", style="dim")
    table.add_column("Complexity", justify="right")
    table.add_column("Lines", justify="right")
    table.add_column("PassRate", justify="right")
    table.add_column("Score", justify="right", style="bold green")
    
    for q in qualities:
        table.add_row(
            q.commit_sha[:8],
            q.timestamp.strftime("%Y-%m-%d"),
            str(q.complexity),
            str(q.size_lines),
            f"{q.test_pass_rate*100:.0f}%",
            f"{q.score:.1f}"
        )
    console.print(table)


# ──────────────────────────────────────────────
# refactor commands (Commands)
# ──────────────────────────────────────────────

@refactor_app.command()
def plan(
    path: Path = typer.Argument(Path("."), help="Ścieżka do projektu"),
) -> None:
    """[Query] Wygeneruj plan refaktoryzacji."""
    suggestions = _generate_refactor_plan(path)
    
    if not suggestions:
        console.print("[green]✓ System nie znalazł krytycznych problemów wymagających refaktoru.[/green]")
        return
        
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

@refactor_app.command()
def execute(
    path: Path = typer.Argument(Path("."), help="Ścieżka do projektu"),
    force: bool = typer.Option(False, "--force", help="Wykonaj bez potwierdzenia"),
) -> None:
    """[Command] Wykonaj automatycznie plan refaktoryzacji."""
    from ..refactor.refactor_executor import RefactorExecutor
    
    suggestions = _generate_refactor_plan(path)
    if not suggestions:
        console.print("[green]Brak działań do wykonania.[/green]")
        return

    executor = RefactorExecutor(console)
    for s in suggestions:
        if not force:
            confirm = typer.confirm(f"Czy wykonać: {s.title}?")
            if not confirm: continue
            
        success = executor.execute_suggestion(s)
        if success:
            console.print(f"[green]✓ Wykonano: {s.title}[/green]")
        else:
            console.print(f"[red]✗ Błąd wykonania: {s.title}[/red]")

def _generate_refactor_plan(path: Path):
    from ..analysis.duplication_engine import DuplicationEngine
    from ..analysis.service_similarity import ServiceSimilarityAnalyzer
    from ..analysis.service_graph import ServiceGraphBuilder
    from ..refactor.recommendation_engine import RecommendationEngine
    
    # 1. Gather analysis (Queries)
    dup_engine = DuplicationEngine()
    duplicates = dup_engine.scan(path)
    
    services_path = path / "rebuild/application/services"
    sim_analyzer = ServiceSimilarityAnalyzer()
    similarities = sim_analyzer.analyze_directory(services_path) if services_path.exists() else []
    
    graph_builder = ServiceGraphBuilder(services_path.resolve()) if services_path.exists() else None
    graph = graph_builder.build() if graph_builder else {}
    cycles = graph_builder.detect_cycles() if graph_builder else []
    
    # 2. Generate recommendations
    rec_engine = RecommendationEngine()
    return rec_engine.generate_plan(duplicates, similarities, graph, cycles)


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _print_summary_table(results: list[DayResult]) -> None:
    table = Table(title="Podsumowanie walk", show_header=True)
    table.add_column("Dzień", style="bold")
    table.add_column("Commit")
    table.add_column("Health", justify="right")
    table.add_column("OK/Total", justify="right")
    table.add_column("Deploy")

    for r in sorted(results, key=lambda x: x.day):
        color = "green" if r.health_pct >= 80 else "yellow" if r.health_pct >= 50 else "red"
        table.add_row(
            str(r.day),
            r.commit.sha[:8] if r.commit else "—",
            f"[{color}]{r.health_pct}%[/{color}]",
            f"{r.ok_count}/{len(r.endpoints)}",
            "✓" if r.deploy_success else "✗",
        )

    console.print(table)
