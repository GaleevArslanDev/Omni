from abc import ABC, abstractmethod


class ClientInterface(ABC):

    @abstractmethod
    def observe(self) -> dict:
        pass

    @abstractmethod
    def execute(self, action: str, **kwargs) -> bool:
        pass

    @abstractmethod
    def get_available_actions(self) -> list[str]:
        pass

    @abstractmethod
    def reset(self) -> bool:
        pass
