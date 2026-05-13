from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class CommitInfo:
    sha: str
    message: str
    author: str
    timestamp: datetime
    date: date
