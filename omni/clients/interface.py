from abc import ABC, abstractmethod


class ClientInterface(ABC):

    @abstractmethod
    def observe(self) -> dict:
        pass

    @abstractmethod
    def stop(self):
        pass
