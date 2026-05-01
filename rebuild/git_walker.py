"""
rebuild.git_walker — iteracja po historii git dzień po dniu.

Dla każdego dnia w zadanym przedziale znajduje najwcześniejszy (lub
najnowszy) commit i zwraca CommitInfo. Nie modyfikuje working tree —
checkout wykonuje deployer.
"""
from __future__ import annotations

import subprocess
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterator, Optional

from .models import CommitInfo, WalkConfig


def _run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def get_commit_for_day(
    repo: Path,
    day: date,
    earliest: bool = True,
) -> Optional[CommitInfo]:
    """
    Zwraca CommitInfo dla danego dnia.

    earliest=True  → najwcześniejszy commit (chronologicznie pierwszy)
    earliest=False → najpóźniejszy commit (HEAD tego dnia)
    """
    day_start = f"{day}T00:00:00"
    day_end = f"{day}T23:59:59"

    order = "--reverse" if earliest else ""
    cmd = [
        "log",
        f"--after={day_start}",
        f"--before={day_end}",
        "--format=%H|%s|%an|%aI",
        "--all",
    ]
    if order:
        cmd.append(order)

    try:
        out = _run_git(cmd, repo)
    except subprocess.CalledProcessError:
        return None

    if not out:
        return None

    # Bierzemy pierwszą linię (najwcześniejszy lub najpóźniejszy)
    line = out.splitlines()[0]
    parts = line.split("|", 3)
    if len(parts) < 4:
        return None

    sha, message, author, iso = parts
    try:
        ts = datetime.fromisoformat(iso)
    except ValueError:
        ts = datetime.now()

    return CommitInfo(
        sha=sha,
        message=message,
        author=author,
        timestamp=ts,
        date=day,
    )


def iter_days(config: WalkConfig) -> Iterator[tuple[date, Optional[CommitInfo]]]:
    """
    Generator: (day, CommitInfo|None) dla każdego dnia w przedziale.

    Kolejność: od najstarszego do najnowszego.
    """
    today = date.today()
    end = config.date_to or today
    start = config.date_from or (end - timedelta(days=config.days - 1))

    current = start
    while current <= end:
        commit = get_commit_for_day(
            config.repo_path,
            current,
            earliest=config.earliest_commit_per_day,
        )
        yield current, commit
        current += timedelta(days=1)


def checkout(repo: Path, sha: str) -> None:
    """Checkout konkretnego commitu (detached HEAD)."""
    _run_git(["checkout", sha], repo)


def restore_head(repo: Path) -> None:
    """Wróć do HEAD (np. main/master po zakończeniu walk)."""
    # Próbujemy main, potem master
    for branch in ("main", "master"):
        try:
            _run_git(["checkout", branch], repo)
            return
        except subprocess.CalledProcessError:
            continue
    # Fallback: wróć do HEAD
    try:
        _run_git(["checkout", "-"], repo)
    except subprocess.CalledProcessError:
        pass


def days_with_commits(config: WalkConfig) -> list[tuple[date, CommitInfo]]:
    """Zwraca tylko dni, które mają przynajmniej jeden commit."""
    return [
        (day, commit)
        for day, commit in iter_days(config)
        if commit is not None
    ]
