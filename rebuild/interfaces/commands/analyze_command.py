from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.tree import Tree


def duplicates_command(
    path: Path,
    min_lines: int,
    semantic: bool,
    semantic_model: str,
    semantic_threshold: float,
    semantic_max_fragments: int,
    console: Console,
) -> None:
    from ...analysis.duplication_engine import DuplicationEngine

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
        console.print(
            f"[bold]Grupa {i} (Similarity: {group.similarity:.2f}, Reason: {group.reason})[/bold]"
        )
        for frag in group.fragments:
            console.print(
                f"  - {frag.file}:{frag.start_line} ([cyan]{frag.name or 'block'}[/cyan])"
            )
        console.print("")


def vector_build_command(
    path: Path,
    index: Path,
    min_lines: int,
    model: str,
    console: Console,
) -> None:
    from ...analysis.vector_search import VectorSearchIndex

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


def vector_query_command(
    query: str,
    index: Path,
    top_k: int,
    min_score: float,
    model: str,
    console: Console,
) -> None:
    from ...analysis.vector_search import VectorSearchIndex

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


def multi_repo_command(
    repos: List[Path],
    min_lines: int,
    export: Optional[Path],
    console: Console,
) -> None:
    from ...analysis.service_graph import MultiRepoAnalyzer

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


def services_command(path: Path, export: bool, console: Console) -> None:
    from ...analysis.service_graph import ServiceGraphBuilder
    from ...analysis.service_similarity import ServiceSimilarityAnalyzer
    from ...analysis.graph_exporter import GraphExporter

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
        console.print(
            f"\n[bold yellow]Wykryto {len(similarities)} nakładających się usług:[/bold yellow]"
        )
        for sim in similarities:
            console.print(
                f"  [bold]{sim.service_a}[/bold] ↔ [bold]{sim.service_b}[/bold] (Overlap: [red]{sim.overlap:.2f}[/red])"
            )


def truth_command(file: Path, function: str, repo: Path, console: Console) -> None:
    from ...analysis.git_truth_analyzer import GitTruthAnalyzer
    from rich.table import Table

    analyzer = GitTruthAnalyzer(repo.resolve())
    qualities = analyzer.analyze_function_history(file, function)

    if not qualities:
        console.print(
            f"[yellow]Nie znaleziono historii dla funkcji {function} w pliku {file}[/yellow]"
        )
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
            f"{q.test_pass_rate * 100:.0f}%",
            f"{q.score:.1f}",
        )
    console.print(table)
