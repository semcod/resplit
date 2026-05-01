from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from .endpoint import Endpoint
from .commit import CommitInfo

@dataclass
class EndpointContext:
    endpoint: Endpoint
    commit: CommitInfo
    day: date
