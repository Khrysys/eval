
from sqlalchemy import URL, func
from sqlmodel import (Session, SQLModel,
                      create_engine, select)

from .archive import Archive # type: ignore
from .chesscom import Chesscom # type: ignore
from .functions import (expected_rating_diff, request_with_retries, # type: ignore
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
    count = session.exec(select(func.count()).select_from(Player))
    print(f'- {count} players')
    count = session.exec(select(func.count()).select_from(Game))
    print(f'- {count} games')
    count = session.exec(select(func.count()).select_from(Match))
    print(f'- {count} matches')
    count = session.exec(select(func.count()).select_from(Opening))
    print(f'- {count} distinct openings')
    count = session.exec(select(func.count()).select_from(TimeControl))
    print(f'- {count} distinct time controls')

url = URL.create('postgresql+psycopg', 'postgres', 'postgres', 'database', 5432, 'database')
engine = create_engine(url, pool_pre_ping=True)

def init_models():
    SQLModel.metadata.create_all(engine)