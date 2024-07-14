from typing import TYPE_CHECKING
from sqlmodel import Field, SQLModel, Session, select

from .functions import request_with_timing
from .game import Game
from .system import SystemNames

class Player(SQLModel, table=True):
    username: str = Field(primary_key=True)
    rating: int
    system: SystemNames

    def games(self, *, session: Session):
        games_a = list(session.exec(select(Game).where(Game.player_a==self)).all())
        games_b = list(session.exec(select(Game).where(Game.player_b==self)).all())
        return list(set(games_a + games_b)) # Just in case there's something weird where a game gets double counted
        
    def archives(self, start: int = 0, end: int = 5):
        from . import Archive
        data = request_with_timing(f'https://api.chess.com/pub/player/{self.username}/games/archives')

        output: list[Archive] = []

        if not data:
            return output
        
        try:
            archives = data['archives']
        except:
            return output
        if end == -1:
            return [Archive(player=self, url=url) for url in archives]

        for i in range(start, end):
            try:
                url = archives[-(i + 1)]
                archive = Archive(player=self, url=url) # type: ignore
                output.append(archive)
            except:
                continue
        return output