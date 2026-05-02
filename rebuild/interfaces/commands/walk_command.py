from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional, Dict

import typer
from rich.console import Console

from ...domain.models import DeployMethod, WalkConfig
from ...application.pipeline import Pipeline
from ...application.accelerated_pipeline import AcceleratedPipeline
from ...application.services.deploy_service import DeployService
from ...infrastructure.config_loader import ConfigLoader


def walk_command(
    repo: Path,
    days: int,
    date_from: Optional[str],
    date_to: Optional[str],
    output: Path,
    deploy: str,
    replay: bool,
    service: Optional[str],
    health_url: str,
    base_url: str,
    screenshots: bool,
    dry_run: bool,
    serve: bool,
    port: int,
    accelerator: bool,
    patch_dir: Optional[Path],
    console: Console,
    health_timeout: int = 60,
    cli_overrides: Optional[Dict[str, bool]] = None,
) -> None:
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
        patch_dir=patch_dir,
        health_timeout=health_timeout,
    )

    config_path = repo / "rebuild.yaml"
    if config_path.exists():
        yaml_data = ConfigLoader.load(config_path)
        if yaml_data:
            validation_errors = ConfigLoader.validate(yaml_data)
            if validation_errors:
                console.print("[bold red]✗ rebuild.yaml zawiera błędy:[/bold red]")
                for err in validation_errors:
                    console.print(f"  [red]• {err}[/red]")
                raise typer.Exit(1)
            ConfigLoader.apply_to_config(config, yaml_data)
    else:
        console.print("  [dim]Brak rebuild.yaml — używam tylko opcji CLI (bez auto-init).[/dim]")

    overrides = cli_overrides or {}
    if overrides.get("output"):
        config.output_dir = output
    if overrides.get("days"):
        config.days = days
    if overrides.get("date_from"):
        config.date_from = date.fromisoformat(date_from) if date_from else None
    if overrides.get("date_to"):
        config.date_to = date.fromisoformat(date_to) if date_to else None
    if overrides.get("deploy"):
        config.deploy_method = method
    if overrides.get("replay"):
        config.replay = replay
    if overrides.get("service"):
        config.app_service = service
    if overrides.get("health_url"):
        config.health_url = health_url
    if overrides.get("base_url"):
        config.base_url = base_url
    if overrides.get("screenshots"):
        config.screenshots = screenshots
    if overrides.get("dry_run"):
        config.dry_run = dry_run
    if overrides.get("accelerator"):
        config.accelerator = accelerator
    if overrides.get("patch_dir"):
        config.patch_dir = patch_dir
    if overrides.get("health_timeout"):
        config.health_timeout = health_timeout

    from ... import __version__
    console.print(f"\n[bold]rebuild walk[/bold] v{__version__}")
    console.print(f"  repo:   {repo}")
    console.print(f"  output: {config.output_dir}")
    console.print(f"  deploy: {config.deploy_method.value} {'(REPLAY)' if config.replay else ''}")
    console.print(f"  days:   {config.days}\n")

    pipeline = Pipeline(config, console=console)
    all_results = pipeline.run()

    if all_results:
        console.print(f"\n[bold green]✓ Gotowe![/bold green]")
        from ..dashboard import generate_dashboard
        generate_dashboard(all_results, config.output_dir, repo=repo)
        from ...application.services.reporting.reporter import ReporterService
        reporter = ReporterService()
        reporter.export_csv(all_results, config.output_dir)
        reporter.export_markdown(all_results, config.output_dir)
        from .helpers import print_report_links, print_summary_table, serve_reports
        print_report_links(config.output_dir, port if serve else None, console)
        print_summary_table(all_results, console)
        if serve:
            serve_reports(config.output_dir, port, console)
    else:
        console.print("[yellow]Brak wyników do wyświetlenia.[/yellow]")


def accelerator_command(
    repo: Path,
    days: int,
    date_from: Optional[str],
    date_to: Optional[str],
    output: Path,
    service: str,
    db_container: str,
    db_type: str,
    parallel: int,
    smart: bool,
    health_url: str,
    base_url: str,
    screenshots: bool,
    shutdown: bool,
    serve: bool,
    port: int,
    patch_dir: Optional[Path],
    console: Console,
) -> None:
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
        patch_dir=patch_dir,
    )

    from ... import __version__
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
        from ..dashboard import generate_dashboard
        generate_dashboard(all_results, output, repo=repo)
        from .helpers import print_report_links, print_summary_table, serve_reports
        print_report_links(output, port if serve else None, console)
        print_summary_table(all_results, console)
        if serve:
            serve_reports(output, port, console)
    else:
        console.print("[yellow]Brak wyników.[/yellow]")
