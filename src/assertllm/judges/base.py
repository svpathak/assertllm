from abc import ABC, abstractmethod

class BaseJudge(ABC):
    @abstractmethod
    def evaluate(self, response: str, assertions: list[str]) -> list[bool]:
        pass