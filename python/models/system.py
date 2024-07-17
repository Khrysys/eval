from abc import abstractmethod
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlmodel import Session

if TYPE_CHECKING:
    from .player import Player

class SystemNames(StrEnum):
    lichess = 'lichess'
    chesscom = 'chesscom'

class System:
    @staticmethod
    @abstractmethod
    def get_player(username: str, *, session: Session) -> Player | None:
        raise NotImplementedError
    