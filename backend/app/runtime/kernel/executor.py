from abc import ABC, abstractmethod

class Executor(ABC):
    @abstractmethod
    def execute(self, command: dict):
        """Executa um comando/ação no domínio."""
        pass
