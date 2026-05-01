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
from rich.markdown import Markdown

from .. import __version__
from ..domain.models import DeployMethod, WalkConfig
from ..domain.day_result import DayResult
from ..application.pipeline import Pipeline
from ..application.accelerated_pipeline import AcceleratedPipeline
from ..application.services.history_service import HistoryService
from ..application.services.reporter_service import ReporterService
from ..application.services.deploy_service import DeployService
from ..application.services.restore_service import RestoreService
from ..infrastructure.config_loader import ConfigLoader

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
    force: bool = typer.Option(False, "--force", help="Nadpisz istniejące pliki"),
) -> None:
    """Zainicjuj nowy projekt rebuild i wygeneruj domyślną konfigurację."""
    # 1. rebuild.yaml
    config_file = path / "rebuild.yaml"
    if not config_file.exists() or force:
        template_path = Path(__file__).parent.parent / "infrastructure" / "config_template.yaml"
        config_content = template_path.read_text() if template_path.exists() else "project:\n  name: 'service'\n  repo: '.'"
        config_file.write_text(config_content)
        console.print(f"[green]✓ Wygenerowano {config_file}[/green]")

    # 2. .env template
    env_file = path / ".env"
    if not env_file.exists() or force:
        env_content = """# rebuild AI Configuration
OPENROUTER_API_KEY=
# Model (default: openrouter/qwen/qwen3-coder-next)
LLM_MODEL=openrouter/qwen/qwen3-coder-next
"""
        env_file.write_text(env_content)
        console.print(f"[green]✓ Wygenerowano {env_file}[/green]")

    console.print(f"\n[bold green]✓ Zainicjowano projekt w {path}[/bold green]")


@app.command()
def walk(
    repo: Path = typer.Argument(Path("."), help="Ścieżka do repozytorium"),
    days: int = typer.Option(30, help="Ile dni wstecz"),
    date_from: Optional[str] = typer.Option(None, "--from", help="Data od YYYY-MM-DD"),
    date_to: Optional[str] = typer.Option(None, "--to", help="Data do YYYY-MM-DD"),
    output: Path = typer.Option(Path(".rebuild"), help="Katalog wyjściowy"),
    deploy: str = typer.Option("auto", help="Metoda deploy: auto|docker-compose|uvicorn|none"),
    replay: bool = typer.Option(False, "--replay", help="Tryb Replay: stały Docker + szybki restart"),
    service: Optional[str] = typer.Option(None, "--service", help="Nazwa serwisu Docker do restartu (w trybie --replay)"),
    health_url: str = typer.Option("http://localhost:8003/api/health", help="URL health check"),
    base_url: str = typer.Option("http://localhost:8003", help="Bazowy URL usługi"),
    screenshots: bool = typer.Option(True, help="Rób zrzuty ekranu (wymaga playwright)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Tylko skanuj, bez deploy"),
    serve: bool = typer.Option(False, "--serve", help="Uruchom serwer HTTP po zakończeniu i otwórz przeglądarkę"),
    port: int = typer.Option(7821, "--port", help="Port serwera HTTP (--serve)"),
    accelerator: bool = typer.Option(False, "--accelerator", help="⚡ Przyspieszony tryb: użyj aktualnych node_modules i patchuj Dockerfile"),
    patch_dir: Optional[Path] = typer.Option(None, "--patch-dir", help="Folder z poprawkami do nałożenia na klon"),
) -> None:
    """Przejdź historię git dzień po dniu, deployuj i testuj endpointy."""
    repo = repo.resolve()
    output = output.resolve()
    if not (repo / ".git").exists():
        console.print(f"[red]✗ {repo} nie jest repozytorium git[/red]")
        raise typer.Exit(1)

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
        replay=replay,
        app_service=service,
        accelerator=accelerator,
        patch_dir=patch_dir
    )

    # Merge with rebuild.yaml only when present (walk never auto-runs init)
    config_path = repo / "rebuild.yaml"
    if config_path.exists():
        yaml_data = ConfigLoader.load(config_path)
        if yaml_data:
            ConfigLoader.apply_to_config(config, yaml_data)
    else:
        console.print("  [dim]Brak rebuild.yaml — używam tylko opcji CLI (bez auto-init).[/dim]")

    console.print(f"\n[bold]rebuild walk[/bold] v{__version__}")
    console.print(f"  repo:   {repo}")
    console.print(f"  output: {output}")
    console.print(f"  deploy: {method.value} {'(REPLAY)' if replay else ''}")
    console.print(f"  days:   {days}\n")

    pipeline = Pipeline(config, console=console)
    all_results = pipeline.run()

    if all_results:
        console.print(f"\n[bold green]✓ Gotowe![/bold green]")
        from .dashboard import generate_dashboard
        generate_dashboard(all_results, output, repo=repo)
        _print_report_links(output, port if serve else None)
        _print_summary_table(all_results)
        if serve:
            _serve_reports(output, port)
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
def accelerator(
    repo: Path = typer.Argument(Path("."), help="Ścieżka do repozytorium"),
    days: int = typer.Option(30, help="Ile dni wstecz"),
    date_from: Optional[str] = typer.Option(None, "--from", help="Data od YYYY-MM-DD"),
    date_to: Optional[str] = typer.Option(None, "--to", help="Data do YYYY-MM-DD"),
    output: Path = typer.Option(Path(".rebuild"), help="Katalog wyjściowy"),
    service: str = typer.Option("backend", help="Nazwa serwisu Docker (do przeładowania)"),
    db_container: str = typer.Option("db", help="Nazwa kontenera bazy danych"),
    db_type: str = typer.Option("postgres", help="Typ bazy: postgres|mysql|sqlite"),
    parallel: int = typer.Option(10, help="Maksymalna liczba równoległych testów"),
    smart: bool = typer.Option(True, help="Inteligentny wybór testów na podstawie git diff"),
    health_url: str = typer.Option("http://localhost:8003/api/health", help="URL health check"),
    base_url: str = typer.Option("http://localhost:8003", help="Bazowy URL usługi"),
    screenshots: bool = typer.Option(True, help="Rób zrzuty ekranu"),
    shutdown: bool = typer.Option(False, "--shutdown", help="Wyłącz infrastrukturę po zakończeniu"),
    serve: bool = typer.Option(False, "--serve", help="Uruchom serwer HTTP po zakończeniu"),
    port: int = typer.Option(7821, "--port", help="Port serwera HTTP"),
    patch_dir: Optional[Path] = typer.Option(None, "--patch-dir", help="Folder z poprawkami do nałożenia na klon"),
) -> None:
    """⚡ Ultra-szybki tryb 10x - worktree + hot reload + parallel testing.
    
    Zamiast restartować Docker per commit:
    - Kontenery działają cały czas
    - Kod podmieniany via git worktree + bind mount
    - Hot reload bez restartu procesów
    - Baza danycH przywracana z snapshotu
    - Testy równoległe z dependency graph
    """
    repo = repo.resolve()
    if not (repo / ".git").exists():
        console.print(f"[red]✗ {repo} nie jest repozytorium git[/red]")
        raise typer.Exit(1)

    config = WalkConfig(
        repo_path=repo,
        output_dir=output,
        days=days,
        date_from=date.fromisoformat(date_from) if date_from else None,
        date_to=date.fromisoformat(date_to) if date_to else None,
        deploy_method=DeployMethod.DOCKER_COMPOSE,
        health_url=health_url,
        base_url=base_url,
        screenshots=screenshots,
        dry_run=False,
        replay=False,
        app_service=service,
        accelerator=True,
        db_container=db_container,
        db_type=db_type,
        max_parallel_tests=parallel,
        smart_select=smart,
        keep_alive=not shutdown,
        shutdown_after=shutdown,
        patch_dir=patch_dir
    )

    console.print(f"\n[bold cyan]⚡ REBUILD ACCELERATOR[/bold cyan] v{__version__}")
    console.print(f"  repo:     {repo}")
    console.print(f"  output:   {output}")
    console.print(f"  service:  {service}")
    console.print(f"  db:       {db_container} ({db_type})")
    console.print(f"  parallel: {parallel} concurrent tests")
    console.print(f"  smart:    {'✓' if smart else '✗'} git-diff selection")
    console.print("")

    pipeline = AcceleratedPipeline(config, console=console)
    
    try:
        all_results = pipeline.run()
    finally:
        if shutdown:
            pipeline.cleanup()

    if all_results:
        console.print(f"\n[bold green]✓ Accelerator done![/bold green]")
        from .dashboard import generate_dashboard
        generate_dashboard(all_results, output, repo=repo)
        _print_report_links(output, port if serve else None)
        _print_summary_table(all_results)
        if serve:
            _serve_reports(output, port)
    else:
        console.print("[yellow]Brak wyników.[/yellow]")


@app.command()
def serve(
    results_dir: Path = typer.Option(Path(".rebuild"), help="Katalog z wynikami walk"),
    port: int = typer.Option(7821, help="Port HTTP"),
) -> None:
    """Uruchom lokalny serwer HTTP z raportami i otwórz przeglądarkę."""
    if not results_dir.exists():
        console.print(f"[red]✗ Katalog {results_dir} nie istnieje. Uruchom najpierw 'rebuild walk'.[/red]")
        raise typer.Exit(1)
    _print_report_links(results_dir, port)
    _serve_reports(results_dir, port)


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
    semantic: bool = typer.Option(False, "--semantic", help="Włącz semantyczne wykrywanie duplikatów (embeddings)"),
    semantic_model: str = typer.Option(
        "sentence-transformers/all-MiniLM-L6-v2",
        "--semantic-model",
        help="Model sentence-transformers do porównań semantycznych",
    ),
    semantic_threshold: float = typer.Option(
        0.82,
        "--semantic-threshold",
        help="Próg podobieństwa kosinusowego dla grup semantycznych",
    ),
    semantic_max_fragments: int = typer.Option(
        300,
        "--semantic-max-fragments",
        help="Maksymalna liczba fragmentów do osadzeń (kontrola kosztu/czasu)",
    ),
) -> None:
    """[Query] Znajdź strukturalne i semantyczne duplikaty kodu."""
    from ..analysis.duplication_engine import DuplicationEngine
    
    engine = DuplicationEngine(
        min_lines=min_lines,
        semantic_enabled=semantic,
        semantic_model_name=semantic_model,
        semantic_threshold=semantic_threshold,
        semantic_max_fragments=semantic_max_fragments,
    )
    groups = engine.scan(path)

    if semantic and engine.semantic_warning:
        console.print(f"[yellow]⚠ Semantic mode warning:[/yellow] {engine.semantic_warning}")
    
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
def vector_build(
    path: Path = typer.Argument(Path("."), help="Ścieżka do skanowania i indeksowania"),
    index: Path = typer.Option(
        Path(".rebuild/semantic_index.sqlite"),
        "--index",
        help="Plik SQLite z indeksem wektorowym",
    ),
    min_lines: int = typer.Option(4, help="Minimalna liczba linii fragmentu"),
    model: str = typer.Option(
        "sentence-transformers/all-MiniLM-L6-v2",
        "--model",
        help="Model sentence-transformers dla osadzeń",
    ),
) -> None:
    """[Query] Zbuduj lokalny indeks wektorowy fragmentów kodu."""
    from ..analysis.vector_search import VectorSearchIndex

    index_path = index.resolve()
    vs = VectorSearchIndex(index_path, model_name=model)
    with console.status("[bold cyan]Budowanie indeksu wektorowego...[/bold cyan]"):
        inserted = vs.build_from_path(path.resolve(), min_lines=min_lines)

    if vs.warning:
        console.print(f"[yellow]⚠ Vector index warning:[/yellow] {vs.warning}")

    total = vs.count()
    console.print(
        f"[green]✓ Indexed[/green] {inserted} fragmentów. "
        f"[dim](total: {total}, db: {index_path})[/dim]"
    )


@analyze_app.command()
def vector_query(
    query: str = typer.Argument(..., help="Zapytanie semantyczne"),
    index: Path = typer.Option(
        Path(".rebuild/semantic_index.sqlite"),
        "--index",
        help="Plik SQLite z indeksem wektorowym",
    ),
    top_k: int = typer.Option(10, "--top-k", help="Liczba najlepszych wyników"),
    min_score: float = typer.Option(0.0, "--min-score", help="Minimalny score podobieństwa"),
    model: str = typer.Option(
        "sentence-transformers/all-MiniLM-L6-v2",
        "--model",
        help="Model sentence-transformers dla zapytania",
    ),
) -> None:
    """[Query] Wyszukaj semantycznie podobne fragmenty w indeksie wektorowym."""
    from ..analysis.vector_search import VectorSearchIndex

    index_path = index.resolve()
    if not index_path.exists():
        console.print(f"[red]✗ Brak indeksu:[/red] {index_path}")
        raise typer.Exit(1)

    vs = VectorSearchIndex(index_path, model_name=model)
    hits = vs.query(query, top_k=top_k)

    if vs.warning:
        console.print(f"[yellow]⚠ Vector query warning:[/yellow] {vs.warning}")

    filtered = [h for h in hits if h.score >= min_score]
    if not filtered:
        console.print("[yellow]Brak wyników dla podanych kryteriów.[/yellow]")
        return

    table = Table(show_header=True)
    table.add_column("Score", justify="right", style="green")
    table.add_column("File", style="cyan")
    table.add_column("Line", justify="right")
    table.add_column("Name")
    table.add_column("Preview", style="dim")

    for hit in filtered:
        first_line = hit.fragment.content.strip().splitlines()
        preview = first_line[0][:80] if first_line else ""
        table.add_row(
            f"{hit.score:.3f}",
            str(hit.fragment.file),
            str(hit.fragment.start_line),
            hit.fragment.name or "block",
            preview,
        )

    console.print(table)


@analyze_app.command()
def multi_repo(
    repos: List[Path] = typer.Argument(..., help="Lista repozytoriów do analizy (min 2)"),
    min_lines: int = typer.Option(6, help="Minimalna długość fragmentu dla clone detection"),
    export: Optional[Path] = typer.Option(
        None,
        "--export",
        help="Opcjonalny plik JSON z pełnym raportem",
    ),
) -> None:
    """[Query] Analiza zależności i klonów kodu między wieloma repozytoriami."""
    from ..analysis.service_graph import MultiRepoAnalyzer

    if len(repos) < 2:
        console.print("[red]✗ Podaj co najmniej 2 repozytoria.[/red]")
        raise typer.Exit(1)

    normalized = [p.resolve() for p in repos]
    missing = [str(p) for p in normalized if not p.exists()]
    if missing:
        console.print("[red]✗ Nie znaleziono repozytoriów:[/red]")
        for path in missing:
            console.print(f"  - {path}")
        raise typer.Exit(1)

    analyzer = MultiRepoAnalyzer(normalized, min_lines=min_lines)
    with console.status("[bold cyan]Analiza multi-repo...[/bold cyan]"):
        report = analyzer.analyze()

    console.print("\n[bold]Repositories[/bold]")
    repo_table = Table(show_header=True)
    repo_table.add_column("Key", style="cyan")
    repo_table.add_column("Path", style="dim")
    for key, path in report.repositories.items():
        repo_table.add_row(key, path)
    console.print(repo_table)

    console.print("\n[bold]Cross-Repo Dependencies[/bold]")
    if not report.dependencies:
        console.print("[yellow]Brak wykrytych zależności cross-repo.[/yellow]")
    else:
        dep_table = Table(show_header=True)
        dep_table.add_column("From", style="cyan")
        dep_table.add_column("To", style="cyan")
        dep_table.add_column("Imports", justify="right", style="green")
        for dep in report.dependencies:
            dep_table.add_row(dep.source_repo, dep.target_repo, str(dep.imports_count))
        console.print(dep_table)

    console.print("\n[bold]Shared Structural Clones[/bold]")
    if not report.clone_groups:
        console.print("[yellow]Brak współdzielonych klonów strukturalnych.[/yellow]")
    else:
        clone_table = Table(show_header=True)
        clone_table.add_column("Hash", style="dim")
        clone_table.add_column("Repos", style="cyan")
        clone_table.add_column("Fragments", justify="right", style="green")
        for group in report.clone_groups[:20]:
            clone_table.add_row(
                group.structural_hash[:12],
                ", ".join(group.repositories),
                str(group.fragments_count),
            )
        console.print(clone_table)
        if len(report.clone_groups) > 20:
            console.print(f"[dim]... i {len(report.clone_groups) - 20} więcej grup[/dim]")

    if export:
        out = export.resolve()
        analyzer.export_json(out, report)
        console.print(f"\n[green]✓ Export:[/green] {out}")

@analyze_app.command()
def services(
    path: Path = typer.Argument(Path("rebuild/application/services"), help="Katalog z serwisami"),
    export: bool = typer.Option(False, "--export", help="Wygeneruj interaktywny graf architecture.html"),
) -> None:
    """[Query] Wykryj nakładające się odpowiedzialności i powiązania między serwisami."""
    from ..analysis.service_graph import ServiceGraphBuilder
    from ..analysis.service_similarity import ServiceSimilarityAnalyzer
    from ..analysis.graph_exporter import GraphExporter
    
    console.print("\n[bold cyan]Budowanie grafu usług...[/bold cyan]")
    builder = ServiceGraphBuilder(path.resolve())
    nodes = builder.build()
    
    if export:
        exporter = GraphExporter(nodes)
        out = Path("architecture.html")
        exporter.export_html(out)
        console.print(f"[green]✓ Wyeksportowano interaktywny graf do: {out.resolve()}[/green]")
    else:
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
    ai: bool = typer.Option(False, "--ai", help="Użyj LLM do podsumowania planu"),
) -> None:
    """[Query] Wygeneruj plan refaktoryzacji z opcjonalnym wsparciem AI."""
    suggestions = _generate_refactor_plan(path)
    
    if not suggestions:
        console.print("[green]✓ System nie znalazł krytycznych problemów wymagających refaktoru.[/green]")
        return
        
    if ai:
        from ..application.services.llm_service import LLMService
        llm = LLMService(console)
        if llm.is_available():
            with console.status("[bold cyan]AI analizuje plan...[/bold cyan]"):
                plan_text = "\n".join([f"- {s.title}: {s.description}" for s in suggestions])
                summary = llm.summarize_refactor_plan(plan_text)
                console.print(Panel(summary, title="[bold cyan]AI Executive Summary[/bold cyan]", border_style="cyan"))

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
def pr(
    path: Path = typer.Argument(Path("."), help="Ścieżka do projektu"),
) -> None:
    """[Query] Wygeneruj profesjonalny opis Pull Requesta (wymaga AI)."""
    suggestions = _generate_refactor_plan(path)
    if not suggestions:
        console.print("[yellow]Brak zmian do opisania.[/yellow]")
        return

    from ..application.services.llm_service import LLMService
    llm = LLMService(console)
    if not llm.is_available():
        console.print("[red]✗ AI Service niedostępny. Sprawdź .env i OPENROUTER_API_KEY.[/red]")
        return

    with console.status("[bold cyan]Generowanie opisu PR...[/bold cyan]"):
        plan_text = "\n".join([f"- {s.title}: {s.description} (Rationale: {s.rationale})" for s in suggestions])
        description = llm.generate_pr_description(plan_text)
        
    console.print("\n[bold green]Gotowy opis Pull Requesta:[/bold green]\n")
    console.print(Markdown(description))

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


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _print_report_links(output: Path, port: Optional[int]) -> None:
    base = f"http://localhost:{port}" if port else str(output.resolve())
    console.print("")
    console.print(f"  [bold cyan]Timeline:[/bold cyan]   {base}/index.html")
    console.print(f"  [bold cyan]Dashboard:[/bold cyan]  {base}/dashboard.html")
    console.print(f"  [dim]Per-day:     {base}/YYYY-MM-DD/report.html[/dim]")


def _serve_reports(output: Path, port: int) -> None:
    import http.server
    import socketserver
    import threading
    import webbrowser
    import os

    os.chdir(output)
    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *a: None

    with socketserver.TCPServer(("", port), handler) as httpd:
        url = f"http://localhost:{port}/index.html"
        console.print(f"\n[bold green]Serwer HTTP uruchomiony:[/bold green] {url}")
        console.print("  [dim]Ctrl+C aby zatrzymać[/dim]\n")
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            console.print("\n[dim]Serwer zatrzymany.[/dim]")


def _print_summary_table(results: list[DayResult]) -> None:
    table = Table(title="Podsumowanie walk", show_header=True)
    table.add_column("Dzień", style="bold")
    table.add_column("Commit")
    table.add_column("Health", justify="right")
    table.add_column("OK/Total", justify="right")
    table.add_column("Deploy")
    table.add_column("Czas")

    for r in sorted(results, key=lambda x: x.day):
        color = "green" if r.health_pct >= 80 else "yellow" if r.health_pct >= 50 else "red"
        table.add_row(
            str(r.day),
            r.commit.sha[:8] if r.commit else "—",
            f"[{color}]{r.health_pct}%[/{color}]",
            f"{r.ok_count}/{len(r.endpoints)}",
            "✓" if r.deploy_success else "✗",
            f"{r.duration_seconds:.2f}s"
        )

    console.print(table)
