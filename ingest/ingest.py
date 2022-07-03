from abc import ABC, abstractmethod
import logging as log
from typing import List, Dict

from supabase import Client

from events import Event
from ingest.ultrarequest import UltraRequest

log.basicConfig(level=log.INFO)


class InternalError(Exception):
    pass


class Ingest(ABC):

    @abstractmethod
    def fetch(self) -> List[UltraRequest]:
        pass

    @abstractmethod
    def parse(self, batch: List[Dict]) -> List[Event]:
        pass

    @abstractmethod
    def upload(self, parsed_batch: List[Event], client: Client) -> None:
        pass
