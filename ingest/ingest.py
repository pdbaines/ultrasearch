from abc import ABC, abstractmethod
import logging as log
from typing import List, Dict

from supabase import Client

from events import Event

log.basicConfig(level=log.INFO)


class InternalError(Exception):
    pass


class Ingest(ABC):

    @abstractmethod
    def fetch(self) -> List[Dict]:
        pass

    @abstractmethod
    def parse(self, batch: List[Dict]) -> List[Event]:
        pass

    @abstractmethod
    def upload(self, client: Client) -> None:
        pass
