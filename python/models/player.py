from sqlmodel import Field, SQLModel, Session, select # type: ignore

from .system import SystemNames

class Player(SQLModel, table=True):
    username: str = Field(primary_key=True)
    rating: int
    system: SystemNames

    def games(self, *, session: Session):
        from .match import Match
        games_a = [match.games for match in list(session.exec(select(Match).where(Match.player_a==self)).all())]
        games_b = [match.games for match in list(session.exec(select(Match).where(Match.player_b==self)).all())]
        return list(set(games_a + games_b)) # Just in case there's something weird where a game gets double counted
        
    def archives(self, start: int = 0, end: int = 5):
        from .lichess import Lichess
        from .chesscom import Chesscom
        if self.system == SystemNames.chesscom:
            return Chesscom.get_archives(self, start, end)
        else:
            return Lichess.get_archives(self, start, end)