from pydantic import ValidationError
from sqlmodel import  SQLModel, Session

from .player import Player

class Archive(SQLModel):
    player: Player
    url: str

    def games(self, *, session: Session):
        from .system import SystemNames
        from .chesscom import Chesscom
        if self.player.system == SystemNames.chesscom:
            return Chesscom.get_games(self, session=session)
        else:
            raise ValidationError('Cannot get games from archive on a player from lichess!')