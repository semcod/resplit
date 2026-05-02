"""
rebuild CLI — główny punkt wejścia.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, List

import typer
from click.core import ParameterSource
from rich.console import Console

from .. import __version__
from ..application.services.history_service import HistoryService
from ..application.services.reporter_service import ReporterService
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
    force: bool = typer.Option(False, "--force", help="Nadpisz istniejące pliki"),
) -> None:
    """Zainicjuj nowy projekt rebuild i wygeneruj domyślną konfigurację."""
    config_file = path / "rebuild.yaml"
    if not config_file.exists() or force:
        template_path = Path(__file__).parent.parent / "infrastructure" / "config_template.yaml"
        config_content = template_path.read_text() if template_path.exists() else "project:\n  name: 'service'\n  repo: '.'"
        config_file.write_text(config_content)
        console.print(f"[green]✓ Wygenerowano {config_file}[/green]")

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
    ctx: typer.Context,
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
    health_timeout: int = typer.Option(60, "--health-timeout", help="Timeout health check w sekundach [default: 60]"),
) -> None:
    """Przejdź historię git dzień po dniu, deployuj i testuj endpointy."""
    cli_overrides = {
        "output": ctx.get_parameter_source("output") == ParameterSource.COMMANDLINE,
        "days": ctx.get_parameter_source("days") == ParameterSource.COMMANDLINE,
        "date_from": ctx.get_parameter_source("date_from") == ParameterSource.COMMANDLINE,
        "date_to": ctx.get_parameter_source("date_to") == ParameterSource.COMMANDLINE,
        "deploy": ctx.get_parameter_source("deploy") == ParameterSource.COMMANDLINE,
        "replay": ctx.get_parameter_source("replay") == ParameterSource.COMMANDLINE,
        "service": ctx.get_parameter_source("service") == ParameterSource.COMMANDLINE,
        "health_url": ctx.get_parameter_source("health_url") == ParameterSource.COMMANDLINE,
        "base_url": ctx.get_parameter_source("base_url") == ParameterSource.COMMANDLINE,
        "screenshots": ctx.get_parameter_source("screenshots") == ParameterSource.COMMANDLINE,
        "dry_run": ctx.get_parameter_source("dry_run") == ParameterSource.COMMANDLINE,
        "accelerator": ctx.get_parameter_source("accelerator") == ParameterSource.COMMANDLINE,
        "patch_dir": ctx.get_parameter_source("patch_dir") == ParameterSource.COMMANDLINE,
        "health_timeout": ctx.get_parameter_source("health_timeout") == ParameterSource.COMMANDLINE,
    }

    from .commands.walk_command import walk_command
    walk_command(repo, days, date_from, date_to, output, deploy, replay, service,
                 health_url, base_url, screenshots, dry_run, serve, port, accelerator, patch_dir, console,
                 health_timeout=health_timeout, cli_overrides=cli_overrides)


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
    """⚡ Ultra-szybki tryb 10x - worktree + hot reload + parallel testing."""
    from .commands.walk_command import accelerator_command
    accelerator_command(repo, days, date_from, date_to, output, service, db_container, db_type,
                        parallel, smart, health_url, base_url, screenshots, shutdown, serve, port,
                        patch_dir, console)


@app.command()
def serve(
    results_dir: Path = typer.Option(Path(".rebuild"), help="Katalog z wynikami walk"),
    port: int = typer.Option(7821, help="Port HTTP"),
) -> None:
    """Uruchom lokalny serwer HTTP z raportami i otwórz przeglądarkę."""
    if not results_dir.exists():
        console.print(f"[red]✗ Katalog {results_dir} nie istnieje. Uruchom najpierw 'rebuild walk'.[/red]")
        raise typer.Exit(1)
    from .commands.helpers import print_report_links, serve_reports
    print_report_links(results_dir, port, console)
    serve_reports(results_dir, port, console)


@app.command()
def tui() -> None:
    """Interaktywne menu TUI: wybór projektu → walk → historia → diff → restore."""
    from .tui import launch_tui
    launch_tui()


@app.command()
def version() -> None:
    """Pokaż wersję rebuild."""
    console.print(f"rebuild v{__version__}")


@app.command()
def auto_pr(
    analysis_file: Path = typer.Argument(..., help="Plik JSON z wynikami analizy (duplicates lub services)"),
    platform: str = typer.Option("github", help="Platforma: github lub gitlab"),
    token: Optional[str] = typer.Option(None, "--token", help="Token API GitHub/GitLab"),
    repo_owner: Optional[str] = typer.Option(None, "--repo-owner", help="Właściciel repozytorium"),
    repo_name: Optional[str] = typer.Option(None, "--repo-name", help="Nazwa repozytorium"),
    base_branch: str = typer.Option("main", help="Gałąź bazowa"),
    head_branch: str = typer.Option("rebuild-auto", help="Gałąź z propozycjami"),
    title: str = typer.Option("Rebuild: Automated Refactor", help="Tytuł PR"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Pokaż PR bez tworzenia"),
) -> None:
    """Utwórz Pull/Merge Request z AI-generated summary z wyników analizy."""
    from ..application.services.pr_service import PRService, PRConfig, Platform, load_config_from_env
    from ..application.services.summary_service import SummaryService

    if not analysis_file.exists():
        console.print(f"[red]✗ Plik {analysis_file} nie istnieje.[/red]")
        raise typer.Exit(1)

    try:
        analysis_data = json.loads(analysis_file.read_text())
    except Exception as e:
        console.print(f"[red]✗ Błąd wczytywania pliku analizy:[/red] {e}")
        raise typer.Exit(1)

    if token and repo_owner and repo_name:
        try:
            pr_platform = Platform(platform.lower())
        except ValueError:
            console.print(f"[red]✗ Nieobsługiwana platforma: {platform}[/red]")
            raise typer.Exit(1)
        pr_config = PRConfig(platform=pr_platform, token=token, repo_owner=repo_owner,
                             repo_name=repo_name, base_branch=base_branch,
                             head_branch=head_branch, title=title)
    else:
        pr_config = load_config_from_env()
        if not pr_config:
            console.print("[red]✗ Brak konfiguracji PR. Podaj --token, --repo-owner, --repo-name lub ustaw zmienne środowiskowe.[/red]")
            raise typer.Exit(1)

    summary_service = SummaryService()
    console.print("[bold cyan]Generowanie podsumowania...[/bold cyan]")

    if "duplicate_groups" in analysis_data:
        summary_result = summary_service.generate_from_duplication(analysis_data)
    elif "cycles" in analysis_data or "services" in analysis_data:
        summary_result = summary_service.generate_from_service_graph(analysis_data)
    else:
        console.print("[red]✗ Nieznany format pliku analizy.[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]Podsumowanie:[/bold]")
    console.print(summary_result.summary)
    console.print(f"\n[bold]Sugestie refactor ({len(summary_result.suggestions)}):[/bold]")
    for suggestion in summary_result.suggestions[:10]:
        console.print(f"  - [{suggestion.severity.upper()}] {suggestion.description}")
    if len(summary_result.suggestions) > 10:
        console.print(f"  ... i jeszcze {len(summary_result.suggestions) - 10}")

    if dry_run:
        console.print("\n[yellow]Dry run mode - PR nie został utworzony.[/yellow]")
        return

    console.print(f"\n[bold cyan]Tworzenie PR na {pr_config.platform.value}...[/bold cyan]")
    pr_service = PRService(pr_config)
    formatted_suggestions = summary_service.format_suggestions_for_pr(summary_result.suggestions)
    pr_result = pr_service.create_pr(summary_result.summary, formatted_suggestions)

    if pr_result.success:
        console.print(f"[green]✓ PR utworzony:[/green] {pr_result.pr_url}")
        console.print(f"  [dim]PR #{pr_result.pr_number}[/dim]")
    else:
        console.print(f"[red]✗ Błąd tworzenia PR:[/red] {pr_result.error}")
        raise typer.Exit(1)


@app.command()
def evolution(
    timeline_file: Path = typer.Argument(..., help="Plik JSON z timeline snapshots"),
    output: Path = typer.Option(Path("evolution.html"), help="Plik wyjściowy HTML"),
    title: str = typer.Option("Code Evolution", help="Tytuł wizualizacji"),
) -> None:
    """Generuj wizualizację D3.js Code Evolution playback z timeline snapshots."""
    from .evolution_viz import generate_evolution_html
    if not timeline_file.exists():
        console.print(f"[red]✗ Plik {timeline_file} nie istnieje.[/red]")
        raise typer.Exit(1)
    console.print("[bold cyan]Generowanie wizualizacji Code Evolution...[/bold cyan]")
    output_path = generate_evolution_html(timeline_file, output, title)
    console.print(f"[green]✓ Wizualizacja zapisana:[/green] {output_path}")
    console.print(f"  [dim]Otwórz w przeglądarce aby zobaczyć playback[/dim]")


@app.command()
def dsl(
    script: Optional[Path] = typer.Option(None, "--script", help="Plik DSL z komendami"),
    command: Optional[str] = typer.Option(None, "--command", help="Pojedyncza komenda DSL"),
    execute: bool = typer.Option(False, "--execute", help="Wykonaj komendy DSL (nie tylko parsuj)"),
) -> None:
    """Wykonaj DSL (Domain Specific Language) komendy rebuild."""
    from ..domain.dsl import DSLParser, DSLInterpreter
    if not script and not command:
        console.print("[red]✗ Podaj --script lub --command[/red]")
        raise typer.Exit(1)

    parser = DSLParser()
    interpreter = DSLInterpreter()

    if script:
        if not script.exists():
            console.print(f"[red]✗ Plik {script} nie istnieje.[/red]")
            raise typer.Exit(1)
        commands = parser.parse_file(script)
        console.print(f"[bold]Załadowano {len(commands)} komend DSL z {script}[/bold]")
        for cmd in commands:
            console.print(f"  - {cmd.command.value}: {cmd.parameters} {cmd.flags}")
            if execute:
                result = interpreter.execute(cmd)
                console.print(f"    [dim]Status: {result.get('status')}[/dim]")
    elif command:
        cmd = parser.parse(command)
        console.print(f"[bold]Komenda DSL:[/bold] {cmd.command.value}")
        console.print(f"  Parameters: {cmd.parameters}")
        console.print(f"  Flags: {cmd.flags}")
        if execute:
            result = interpreter.execute(cmd)
            console.print(f"  [dim]Status: {result.get('status')}[/dim]")
            console.print(f"  [green]✓ Zinterpretowano[/green]")


@app.command()
def nlp(
    text: str = typer.Argument(..., help="Tekst komendy w języku naturalnym"),
    to_dsl: bool = typer.Option(False, "--to-dsl", help="Konwertuj do DSL"),
    to_cli: bool = typer.Option(False, "--to-cli", help="Konwertuj do CLI args"),
) -> None:
    """Parsuj komendę w języku naturalnym i konwertuj na DSL/CLI."""
    from ..application.services.nlp_service import NLPService
    nlp_svc = NLPService()
    cmd = nlp_svc.parse(text)
    console.print(f"[bold]Zinterpretowana komenda:[/bold] {cmd.intent.value}")
    console.print(f"  Confidence: {cmd.confidence:.2f}")
    console.print(f"  Parameters: {cmd.parameters}")
    if to_dsl:
        dsl_out = nlp_svc.to_dsl(cmd)
        console.print(f"\n[bold]DSL:[/bold] {dsl_out}")
    if to_cli:
        cli_args = nlp_svc.to_cli_args(cmd)
        console.print(f"\n[bold]CLI args:[/bold] {' '.join(cli_args)}")


@app.command()
def mvp(
    host: str = typer.Option("0.0.0.0", help="Host dla MVP server"),
    port: int = typer.Option(8899, help="Port dla MVP server"),
) -> None:
    """Uruchom MVP protocol server."""
    from ..domain.mvp_protocol import MVPServer
    console.print(f"[bold cyan]Uruchamianie MVP Server...[/bold cyan]")
    console.print(f"  Host: {host}")
    console.print(f"  Port: {port}")
    console.print(f"  Protocol: JSON over HTTP")
    server = MVPServer(host=host, port=port)
    server.start()


# ──────────────────────────────────────────────
# analyze commands
# ──────────────────────────────────────────────

@analyze_app.command()
def duplicates(
    path: Path = typer.Argument(Path("."), help="Ścieżka do skanowania"),
    min_lines: int = typer.Option(4, help="Minimalna liczba linii dla duplikatu"),
    semantic: bool = typer.Option(False, "--semantic", help="Włącz semantyczne wykrywanie duplikatów (embeddings)"),
    semantic_model: str = typer.Option("sentence-transformers/all-MiniLM-L6-v2", "--semantic-model", help="Model sentence-transformers"),
    semantic_threshold: float = typer.Option(0.82, "--semantic-threshold", help="Próg podobieństwa kosinusowego"),
    semantic_max_fragments: int = typer.Option(300, "--semantic-max-fragments", help="Maksymalna liczba fragmentów"),
) -> None:
    """[Query] Znajdź strukturalne i semantyczne duplikaty kodu."""
    from .commands.analyze_command import duplicates_command
    duplicates_command(path, min_lines, semantic, semantic_model, semantic_threshold, semantic_max_fragments, console)


@analyze_app.command()
def vector_build(
    path: Path = typer.Argument(Path("."), help="Ścieżka do skanowania i indeksowania"),
    index: Path = typer.Option(Path(".rebuild/semantic_index.sqlite"), "--index", help="Plik SQLite z indeksem wektorowym"),
    min_lines: int = typer.Option(4, help="Minimalna liczba linii fragmentu"),
    model: str = typer.Option("sentence-transformers/all-MiniLM-L6-v2", "--model", help="Model sentence-transformers"),
) -> None:
    """[Query] Zbuduj lokalny indeks wektorowy fragmentów kodu."""
    from .commands.analyze_command import vector_build_command
    vector_build_command(path, index, min_lines, model, console)


@analyze_app.command()
def vector_query(
    query: str = typer.Argument(..., help="Zapytanie semantyczne"),
    index: Path = typer.Option(Path(".rebuild/semantic_index.sqlite"), "--index", help="Plik SQLite z indeksem wektorowym"),
    top_k: int = typer.Option(10, "--top-k", help="Liczba najlepszych wyników"),
    min_score: float = typer.Option(0.0, "--min-score", help="Minimalny score podobieństwa"),
    model: str = typer.Option("sentence-transformers/all-MiniLM-L6-v2", "--model", help="Model sentence-transformers"),
) -> None:
    """[Query] Wyszukaj semantycznie podobne fragmenty w indeksie wektorowym."""
    from .commands.analyze_command import vector_query_command
    vector_query_command(query, index, top_k, min_score, model, console)


@analyze_app.command()
def multi_repo(
    repos: List[Path] = typer.Argument(..., help="Lista repozytoriów do analizy (min 2)"),
    min_lines: int = typer.Option(6, help="Minimalna długość fragmentu dla clone detection"),
    export: Optional[Path] = typer.Option(None, "--export", help="Opcjonalny plik JSON z pełnym raportem"),
) -> None:
    """[Query] Analiza zależności i klonów kodu między wieloma repozytoriami."""
    from .commands.analyze_command import multi_repo_command
    multi_repo_command(repos, min_lines, export, console)


@analyze_app.command()
def services(
    path: Path = typer.Argument(Path("rebuild/application/services"), help="Katalog z serwisami"),
    export: bool = typer.Option(False, "--export", help="Wygeneruj interaktywny graf architecture.html"),
) -> None:
    """[Query] Wykryj nakładające się odpowiedzialności i powiązania między serwisami."""
    from .commands.analyze_command import services_command
    services_command(path, export, console)


@analyze_app.command()
def truth(
    file: Path = typer.Argument(..., help="Plik do analizy"),
    function: str = typer.Argument(..., help="Nazwa funkcji do analizy historii"),
    repo: Path = typer.Option(Path("."), help="Ścieżka do repo"),
) -> None:
    """[Query] Znajdź 'najprawdziwszą' wersję funkcji w historii git."""
    from .commands.analyze_command import truth_command
    truth_command(file, function, repo, console)


# ──────────────────────────────────────────────
# refactor commands
# ──────────────────────────────────────────────

@refactor_app.command()
def plan(
    path: Path = typer.Argument(Path("."), help="Ścieżka do projektu"),
    ai: bool = typer.Option(False, "--ai", help="Użyj LLM do podsumowania planu"),
) -> None:
    """[Query] Wygeneruj plan refaktoryzacji z opcjonalnym wsparciem AI."""
    from .commands.refactor_command import plan_command
    plan_command(path, ai, console)


@refactor_app.command()
def pr(
    path: Path = typer.Argument(Path("."), help="Ścieżka do projektu"),
) -> None:
    """[Query] Wygeneruj profesjonalny opis Pull Requesta (wymaga AI)."""
    from .commands.refactor_command import pr_command
    pr_command(path, console)


@refactor_app.command()
def execute(
    path: Path = typer.Argument(Path("."), help="Ścieżka do projektu"),
    force: bool = typer.Option(False, "--force", help="Wykonaj bez potwierdzenia"),
) -> None:
    """[Command] Wykonaj automatycznie plan refaktoryzacji."""
    from .commands.refactor_command import execute_command
    execute_command(path, force, console)


@app.command()
def plugins(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Pokaż szczegóły pluginów"),
) -> None:
    """Wylistuj zainstalowane pluginy (scanners, reporters)."""
    from ..plugins import load_plugins
    from rich.table import Table

    registry = load_plugins()

    table = Table(title="Rebuild Plugins", show_header=True)
    table.add_column("Type", style="bold cyan")
    table.add_column("Name", style="bold")
    table.add_column("Class")
    table.add_column("Description")

    for name, cls in sorted(registry.scanners.items()):
        desc = getattr(cls, "description", "") or ""
        table.add_row("scanner", name, cls.__qualname__, desc)

    for name, cls in sorted(registry.reporters.items()):
        desc = getattr(cls, "description", "") or ""
        table.add_row("reporter", name, cls.__qualname__, desc)

    if not registry.scanners and not registry.reporters:
        console.print("[dim]Brak zainstalowanych pluginów.[/dim]")
        console.print(
            "\n[dim]Zainstaluj pakiety z entry points w grupach "
            "[bold]rebuild.scanners[/bold] / [bold]rebuild.reporters[/bold].[/dim]"
        )
        return

    console.print(table)
    console.print(
        f"\n  [dim]{len(registry.scanners)} scanner(s), "
        f"{len(registry.reporters)} reporter(s)[/dim]"
    )
