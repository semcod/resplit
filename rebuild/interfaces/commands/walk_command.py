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
    _ensure_git_repo(repo, console)

    method = _resolve_deploy_method(repo, deploy, dry_run)
    config = _build_walk_config(
        repo,
        output,
        days,
        date_from,
        date_to,
        method,
        health_url,
        base_url,
        screenshots,
        dry_run,
        replay,
        service,
        accelerator,
        patch_dir,
        health_timeout,
    )
    _load_yaml_config(config, repo, console)
    _apply_cli_overrides(
        config,
        cli_overrides or {},
        output=output,
        days=days,
        date_from=date_from,
        date_to=date_to,
        method=method,
        replay=replay,
        service=service,
        health_url=health_url,
        base_url=base_url,
        screenshots=screenshots,
        dry_run=dry_run,
        accelerator=accelerator,
        patch_dir=patch_dir,
        health_timeout=health_timeout,
    )

    _print_walk_header(config, repo, console)
    all_results = Pipeline(config, console=console).run()
    _handle_walk_results(all_results, config, repo, serve, port, console)


def _ensure_git_repo(repo: Path, console: Console) -> None:
    if not (repo / ".git").exists():
        console.print(f"[red]✗ {repo} nie jest repozytorium git[/red]")
        raise typer.Exit(1)


def _resolve_deploy_method(repo: Path, deploy: str, dry_run: bool) -> DeployMethod:
    if deploy != "auto":
        return DeployMethod(deploy)
    if dry_run:
        return DeployMethod.NONE
    deploy_svc = DeployService(WalkConfig(repo_path=repo))
    return deploy_svc.detect_deploy_method(repo)


def _build_walk_config(
    repo: Path,
    output: Path,
    days: int,
    date_from: Optional[str],
    date_to: Optional[str],
    method: DeployMethod,
    health_url: str,
    base_url: str,
    screenshots: bool,
    dry_run: bool,
    replay: bool,
    service: Optional[str],
    accelerator: bool,
    patch_dir: Optional[Path],
    health_timeout: int,
) -> WalkConfig:
    return WalkConfig(
        repo_path=repo,
        output_dir=output,
        days=days,
        date_from=_parse_date(date_from),
        date_to=_parse_date(date_to),
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


def _parse_date(value: Optional[str]):
    return date.fromisoformat(value) if value else None


def _load_yaml_config(config: WalkConfig, repo: Path, console: Console) -> None:
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


def _apply_cli_overrides(config: WalkConfig, overrides: Dict[str, bool], **values) -> None:
    attr_values = {
        "output": ("output_dir", values["output"]),
        "days": ("days", values["days"]),
        "date_from": ("date_from", _parse_date(values["date_from"])),
        "date_to": ("date_to", _parse_date(values["date_to"])),
        "deploy": ("deploy_method", values["method"]),
        "replay": ("replay", values["replay"]),
        "service": ("app_service", values["service"]),
        "health_url": ("health_url", values["health_url"]),
        "base_url": ("base_url", values["base_url"]),
        "screenshots": ("screenshots", values["screenshots"]),
        "dry_run": ("dry_run", values["dry_run"]),
        "accelerator": ("accelerator", values["accelerator"]),
        "patch_dir": ("patch_dir", values["patch_dir"]),
        "health_timeout": ("health_timeout", values["health_timeout"]),
    }
    for key, (attr, value) in attr_values.items():
        if overrides.get(key):
            setattr(config, attr, value)


def _print_walk_header(config: WalkConfig, repo: Path, console: Console) -> None:
    from ... import __version__

    console.print(f"\n[bold]rebuild walk[/bold] v{__version__}")
    console.print(f"  repo:   {repo}")
    console.print(f"  output: {config.output_dir}")
    console.print(f"  deploy: {config.deploy_method.value} {'(REPLAY)' if config.replay else ''}")
    console.print(f"  days:   {config.days}\n")


def _handle_walk_results(
    all_results,
    config: WalkConfig,
    repo: Path,
    serve: bool,
    port: int,
    console: Console,
) -> None:
    if all_results:
        console.print("\n[bold green]✓ Gotowe![/bold green]")
        from ..dashboard import generate_dashboard

        generate_dashboard(all_results, config.output_dir, repo=repo)
        from ...application.services.reporting.reporter import ReporterService

        reporter = ReporterService()
        reporter.export_csv(all_results, config.output_dir)
        reporter.export_markdown(all_results, config.output_dir)
        from .helpers import print_report_links, print_summary_table, serve_reports

        print_report_links(config.output_dir, port if serve else None, console)
        print_summary_table(all_results, console)
        _fire_notifications(all_results, config, console)
        if serve:
            serve_reports(config.output_dir, port, console)
    else:
        console.print("[yellow]Brak wyników do wyświetlenia.[/yellow]")


def _fire_notifications(all_results, config, console: Console) -> None:
    from ...application.services.notification_service import NotificationService

    hooks_cfg = getattr(config, "notifications", None)
    if not hooks_cfg:
        return
    svc = NotificationService.from_config(hooks_cfg)
    if not svc.hooks:
        return
    failed = [r for r in all_results if not r.deploy_success]
    for r in failed:
        commit_sha = r.commit.sha if r.commit else None
        svc.notify_deploy_fail(r.day, commit_sha, r.deploy_error_category)
    total = len(all_results)
    healthy = sum(1 for r in all_results if r.health_pct >= 80)
    avg = sum(r.health_pct for r in all_results) / total if total else 0.0
    results = svc.notify_walk_complete(total, healthy, avg, config.output_dir)
    sent = sum(results)
    if sent:
        console.print(f"[dim]  📣 Wysłano {sent} powiadomienie(a)[/dim]")


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
        console.print("\n[bold green]✓ Accelerator done![/bold green]")
        from ..dashboard import generate_dashboard

        generate_dashboard(all_results, output, repo=repo)
        from .helpers import print_report_links, print_summary_table, serve_reports

        print_report_links(output, port if serve else None, console)
        print_summary_table(all_results, console)
        if serve:
            serve_reports(output, port, console)
    else:
        console.print("[yellow]Brak wyników.[/yellow]")
