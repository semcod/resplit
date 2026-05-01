from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime
import json

@dataclass
class PipelineEvent:
    event_type: str
    timestamp: str
    data: dict

    @classmethod
    def create(cls, event_type: str, **kwargs) -> PipelineEvent:
        return cls(
            event_type=event_type,
            timestamp=datetime.now().isoformat(),
            data=kwargs
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self))

# Event types:
# - COMMIT_CHECKOUT
# - DEPLOY_STARTED
# - DEPLOY_FINISHED
# - SCAN_FINISHED
# - TEST_FINISHED
# - SCREENSHOT_TAKEN
# - DAY_FINISHED
