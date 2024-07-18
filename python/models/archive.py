from pydantic import ValidationError
from sqlmodel import  SQLModel, Session

from .player import Player
from .game import Game

class Archive(SQLModel):
    player: Player
    url: str

    def games(self, timing: bool = False, new_only: bool = False, *, session: Session) -> list[Game]:
        from .system import SystemNames
        from .chesscom import Chesscom
        if self.player.system == SystemNames.chesscom:
            return Chesscom.get_games(self, timing, new_only, session=session)
        else:
            raise ValidationError('Cannot get games from archive on a player from lichess!')