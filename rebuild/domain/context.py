from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Optional
from .endpoint import Endpoint, EndpointResult
from .commit import CommitInfo

@dataclass
class EndpointContext:
    endpoint: Endpoint
    commit: CommitInfo
    day: date
    result: Optional[EndpointResult] = None
