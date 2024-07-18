
from sqlalchemy import URL
from sqlmodel import (Session, SQLModel,
                      create_engine, select)

from .archive import Archive # type: ignore
from .chesscom import Chesscom # type: ignore
from .functions import (expected_rating_diff, make_request_with_retries, # type: ignore
                        prop_se, request_with_timing, sigmoid, z_score_2tail) # type: ignore
from .game import Game # type: ignore
from .lichess import Lichess # type: ignore
from .match import Match # type: ignore
from .opening import Opening # type: ignore
from .player import Player # type: ignore
from .system import System # type: ignore
from .time_control import TimeControl # type: ignore

def get_session():
    with Session(engine) as session:
        yield session
        session.commit()

def statistics(*, session: Session):
    print("Database Statistics")
    count = len(session.exec(select(Player)).all())
    print(f'- {count} players')
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