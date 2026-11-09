# ingestion/base.py
"""
Abstract base class for email ingestion providers.
"""

from abc import ABC, abstractmethod
from typing import List
from core.models import RawEmail


class EmailIngestionProvider(ABC):
    @abstractmethod
    def fetch_emails(self, max_count: int = 50) -> List[RawEmail]:
        """Fetches raw emails from the source provider."""
        pass
