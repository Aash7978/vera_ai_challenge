from datetime import datetime, timezone
from typing import Any, Dict, Optional


class SuppressionStore:

    def __init__(self):
        self._records = {}

    def has_been_sent(
        self,
        suppression_key: Optional[str],
    ) -> bool:

        if not suppression_key:
            return False

        return suppression_key in self._records

    def record(
        self,
        suppression_key: Optional[str],
    ) -> None:

        if not suppression_key:
            return

        self._records[suppression_key] = {
            "recorded_at": datetime.now(
                timezone.utc
            ).isoformat()
        }

    def get(
        self,
        suppression_key: str,
    ) -> Optional[Dict[str, Any]]:

        return self._records.get(
            suppression_key
        )