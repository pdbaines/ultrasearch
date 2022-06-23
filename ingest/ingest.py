from abc import ABC, abstractmethod
import logging as log

from supabase import Client


log.basicConfig(level=log.INFO)


class InternalError(Exception):
    pass


class Ingest(ABC):

    @abstractmethod
    def fetch(self) -> None:
        pass

    @abstractmethod
    def parse(self) -> None:
        pass

    @abstractmethod
    def upload(self, client: Client) -> None:
        pass
