from abc import abstractmethod
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlmodel import Session


class SystemNames(StrEnum):
    lichess = 'lichess'
    chesscom = 'chesscom'

class System:
    @staticmethod
    @abstractmethod
    def get_player(username: str, *, session: Session):
        raise NotImplementedError
    