from abc import abstractmethod
from enum import StrEnum

class SystemNames(StrEnum):
    lichess = 'lichess'
    chesscom = 'chesscom'

class System:
    @staticmethod
    @abstractmethod
    def get_player(username: str):
        raise NotImplementedError
    