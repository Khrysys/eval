
from sqlalchemy import URL, Engine
from sqlmodel import (Session, SQLModel,
                      create_engine, select)

from .archive import Archive
from .chesscom import Chesscom
from .functions import (expected_rating_diff, make_request_with_retries,
                        prop_se, request_with_timing, sigmoid, z_score_2tail)
from .game import Game
from .lichess import Lichess
from .match import Match
from .opening import Opening
from .player import Player
from .system import System
from .time_control import TimeControl

def get_session():
    with Session(engine) as session:
        yield session
        session.commit()

def statistics(*, session: Session):
    print("Database Statistics")
    count = len(session.exec(select(Player)).all())
    print(f'- {count} players')
    count = len(session.exec(select(Archive)).all())
    print(f'- {count} archives')
    count = len(session.exec(select(Game)).all())
    print(f'- {count} games')
    count = len(session.exec(select(Match)).all())
    print(f'- {count} matches')
    count = len(session.exec(select(Opening)).all())
    print(f'- {count} distinct openings')
    count = len(session.exec(select(TimeControl)).all())
    print(f'- {count} distinct time controls')

url = URL.create('postgresql+psycopg', 'postgres', 'postgres', 'database', 5432, 'database')
engine = create_engine(url, pool_pre_ping=True)

def init_models():
    SQLModel.metadata.create_all(engine)