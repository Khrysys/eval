from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from functools import lru_cache
from io import StringIO
from math import exp, log10, sqrt
from multiprocessing import Pool
from time import sleep, time

import requests
from aiohttp import (ClientError, ClientResponseError, ClientSession,
                     ServerTimeoutError)
from chess.pgn import read_game as load_pgn
from scipy.stats import norm
from sqlalchemy import URL
from sqlmodel import (Field, Relationship, Session, SQLModel, UniqueConstraint,
                      create_engine, select)
from tqdm import tqdm

from .archive import Archive
from .chesscom import Chesscom
from .functions import (make_request_with_retries, prop_se,
                        request_with_timing, z_score_2tail, sigmoid, expected_rating_diff)
from .game import Game
from .lichess import Lichess
from .match import Match
from .opening import Opening
from .player import Player
from .system import System
from .time_control import TimeControl

async def add_all_data_from_username(username: str):
    with Session(engine) as session:
        player = Chesscom.get_player(username, session=session)
        if not player:
            return
        t1 = time()
        archives = player.archives(start=0, end=1)
        print(f'Getting {len(archives)} archives took {round(1000 * (time() - t1), 2)} ms')
        for archive in archives:
            games = archive.games(session=session)
            session.flush()

        matches = session.exec(select(Match)).all()

        for match in matches:
            match.calculate_rating_difference(session=session)
        session.commit()

async def test():
    # The top 3 blitz players
    await add_all_data_from_username('hikaru')
    await add_all_data_from_username('nihalsarin')
    await add_all_data_from_username('magnuscarlsen')
    # Top 3 bullet players
    await add_all_data_from_username('arkadiykhromaev')
    await add_all_data_from_username('firouzja2003')
    await add_all_data_from_username('gurelediz')
    # Top 3 rapid players
    await add_all_data_from_username('gutovandrey')
    await add_all_data_from_username('seanwinshand')
    await add_all_data_from_username('lyonbeast')

    #await add_all_data_from_username('khrysys')

    statistics()

async def recurse():
    with Session(engine) as session:
        players = session.exec(select(Player)).all()
        for player in players:
            await add_all_data_from_username(player.username)

def statistics():
    with Session(engine) as session:
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

url = URL.create('postgresql+psycopg', 'postgres', 'postgres', '127.0.0.1', 5432, 'db-chess-ratings')
engine = create_engine('postgresql+psycopg://u3s9daxzy3nrxy7y23gg:4fWB6h0l6nvHAfz3Lt2wT041Dadfma@bbixyz9jayqyh5eok6qr-postgresql.services.clever-cloud.com:50013/bbixyz9jayqyh5eok6qr')
engine = create_engine(url)
SQLModel.metadata.create_all(engine)