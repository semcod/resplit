"""
``rebuild watch`` — long-running mode powered by the ``wup`` library.

Activates on file changes in the target repo and re-runs ``rebuild walk
--dry-run`` (or a configured callback) so contributors get instant feedback
on endpoint count, deploy success, and health regressions while iterating.

The integration is intentionally thin: ``wup`` owns the file-watching,
debouncing, CPU-throttling, and dependency-mapping logic; rebuild owns the
walk-and-report logic. They meet at a single callback (``on_change``).

The ``wup`` package is an **optional dependency**. Install with
``pip install 'rebuild[watch]'`` or ``pip install wup``.
"""

from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Callable, List, Optional

from rich.console import Console


def _require_wup() -> Any:
    """Import wup or raise a friendly error."""
    try:
        import wup  # noqa: F401

        return wup
    except ImportError as exc:
        raise RuntimeError(
            "The 'wup' package is required for `rebuild watch`. "
            "Install with: pip install 'rebuild[watch]' (or pip install wup)"
        ) from exc


def _build_default_wup_config(
    repo: Path,
    health_url: str,
    base_url: str,
) -> Any:
    """Construct a minimal ``WupConfig`` for an unknown repo.

    The config picks sensible defaults:
      * Watch the whole repo, excluding ``.git``, ``.venv``, ``node_modules``,
        ``__pycache__`` and the rebuild output dir.
      * Single ``rebuild`` service that delegates to ``rebuild walk --dry-run``
        on every detected change.
    """
    from wup.models.config import (
        ProjectConfig,
        ServiceConfig,
        WatchConfig,
        WupConfig,
    )

    # Stash health/base URL on the project description for traceability;
    # the actual ``rebuild walk`` invocation happens in ``_default_on_change``,
    # not via wup's quick_tests.
    project = ProjectConfig(
        name=repo.name,
        description=(f"rebuild watch session on {repo} (health={health_url}, base={base_url})"),
    )

    watch = WatchConfig(
        paths=[str(repo)],
        exclude_patterns=[
            "**/.git/**",
            "**/.venv/**",
            "**/venv/**",
            "**/node_modules/**",
            "**/__pycache__/**",
            "**/.rebuild/**",
            "**/.pytest_cache/**",
            "**/.mypy_cache/**",
            "**/.ruff_cache/**",
        ],
        file_types=[".py", ".yml", ".yaml", ".toml", ".json"],
    )

    rebuild_service = ServiceConfig(
        name="rebuild",
        root=str(repo),
        paths=[str(repo)],
        type="custom",
    )

    return WupConfig(
        project=project,
        watch=watch,
        services=[rebuild_service],
    )


def _default_on_change(
    repo: Path,
    output: Path,
    health_url: str,
    base_url: str,
    console: Console,
) -> Callable[[List[str]], None]:
    """Default handler: invoke ``rebuild walk --dry-run`` on every batch."""
    rebuild_bin = shutil.which("rebuild") or "rebuild"

    def _handler(changed_files: List[str]) -> None:
        console.print(f"\n[cyan]✱ Detected {len(changed_files)} change(s)[/cyan]")
        for f in changed_files[:5]:
            console.print(f"  [dim]· {f}[/dim]")
        if len(changed_files) > 5:
            console.print(f"  [dim]· ... +{len(changed_files) - 5} more[/dim]")

        cmd = [
            rebuild_bin,
            "walk",
            str(repo),
            "--dry-run",
            "--days",
            "1",
            "--deploy",
            "none",
            "--output",
            str(output),
            "--health-url",
            health_url,
            "--base-url",
            base_url,
        ]
        console.print(f"[dim]$ {' '.join(cmd)}[/dim]")
        start = time.perf_counter()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            console.print("[red]✗ rebuild walk timed out after 120s[/red]")
            return
        elapsed = time.perf_counter() - start

        if result.returncode == 0:
            console.print(f"[green]✓ rebuild walk completed in {elapsed:.1f}s[/green]")
        else:
            console.print(f"[red]✗ rebuild walk failed (exit {result.returncode})[/red]")
            if result.stderr:
                console.print(f"[dim]{result.stderr.strip()[:500]}[/dim]")

    return _handler


def watch_command(
    repo: Path,
    output: Path,
    health_url: str,
    base_url: str,
    deps_file: Optional[Path],
    cpu_throttle: float,
    debounce_seconds: int,
    cooldown_seconds: int,
    console: Console,
    on_change: Optional[Callable[[List[str]], None]] = None,
    _watcher_factory: Optional[Callable[..., Any]] = None,
) -> None:
    """Run ``rebuild watch`` on *repo*.

    Args:
        repo: Repository to watch.
        output: rebuild output directory (passed to walk subprocess).
        health_url, base_url: forwarded to ``rebuild walk``.
        deps_file: Optional explicit ``deps.json`` path; defaults to
            ``<output>/wup_deps.json``.
        cpu_throttle: Skip tests when CPU > this fraction (0.0-1.0).
        debounce_seconds: Coalesce file events within this window.
        cooldown_seconds: Minimum wait between two tests of the same service.
        console: Rich console for output.
        on_change: Optional override for the default change handler.
        _watcher_factory: Test seam — replace ``wup.WupWatcher``.
    """
    _require_wup()

    repo = repo.resolve()
    output.mkdir(parents=True, exist_ok=True)
    deps_path = (deps_file or (output / "wup_deps.json")).resolve()
    config = _build_default_wup_config(repo, health_url, base_url)

    handler = on_change or _default_on_change(repo, output, health_url, base_url, console)

    if _watcher_factory is None:
        from wup import WupWatcher

        _watcher_factory = WupWatcher

    watcher = _watcher_factory(
        project_root=str(repo),
        deps_file=str(deps_path),
        cpu_throttle=cpu_throttle,
        debounce_seconds=debounce_seconds,
        test_cooldown_seconds=cooldown_seconds,
        config=config,
    )

    # Bridge wup's per-file callback to our batch-friendly handler.
    if hasattr(watcher, "on_file_change"):
        original_on_file_change = watcher.on_file_change

        def _bridge(path: str) -> None:
            handler([path])
            try:
                original_on_file_change(path)
            except Exception as exc:
                console.print(f"[yellow]wup: {exc}[/yellow]")

        watcher.on_file_change = _bridge  # type: ignore[assignment]

    console.print(f"[bold cyan]rebuild watch[/bold cyan] — {repo}")
    console.print(f"  [dim]output:[/dim]      {output}")
    console.print(f"  [dim]deps file:[/dim]   {deps_path}")
    console.print(f"  [dim]debounce:[/dim]    {debounce_seconds}s")
    console.print(f"  [dim]cooldown:[/dim]    {cooldown_seconds}s")
    console.print(f"  [dim]cpu throttle:[/dim] {cpu_throttle:.0%}")
    console.print("\n[dim]Press Ctrl+C to stop.[/dim]\n")

    try:
        watcher.start_watching()
    except KeyboardInterrupt:
        console.print("\n[dim]Watcher stopped.[/dim]")
