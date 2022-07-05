from abc import ABC, abstractmethod


class UltraRequest(ABC):

    def __init__(self, params):
        self.params = params

    @abstractmethod
    def fetch(self):
        pass
