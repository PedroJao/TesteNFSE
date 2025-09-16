from abc import ABC, abstractmethod

class NFSeExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: str) -> dict:
        """Extrai dados do arquivo PDF e retorna dict estruturado."""
        raise NotImplementedError
