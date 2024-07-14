from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from io import StringIO
from time import time
from typing import TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel, Session, UniqueConstraint, select

from chess.pgn import read_game as load_pgn

from .game import Game
from .time_control import TimeControl
from .opening import Opening
from .player import Player
from .chesscom import Chesscom
from .match import Match
from .functions import request_with_timing
from .system import System

class Archive(SQLModel):
    player: Player
    url: str

    def process_game(self, game, system: System = Chesscom, *, session: Session): # type: ignore
        if not game.get('rules', '') == 'chess':
            return
        
        url = game.get('url')
        if not url:
            return
        
        g = session.exec(select(Game).where(Game.url==url)).one_or_none()
        if g:
            return g
        
        time_control_code = game.get('time_control')
        if not time_control_code:
            print(f'No time control on {url}')
            time_control_code = ''
        time_control = TimeControl.get(time_control_code, session=session)

        pgn = game.get('pgn')
        if not pgn:
            print(f'No PGN on {url}')
            return
        
        g = load_pgn(StringIO(pgn))
        if not g:
            print(f'PGN was invalid on {url}')
            return
        
        len([m for m in g.mainline_moves()])
        eco = g.headers.get('ECO', '')
        eco_url = g.headers.get('ECOUrl', '')
        opening = Opening.get(eco, eco_url, session=session)

        white = game['white']
        black = game['black']
        end_time = game['end_time']        
        user_is_white: bool = self.player.username == white['username'].lower().strip()
        opponent_username = black['username'].lower().strip() if user_is_white else white['username'].lower().strip() 
        opponent = Chesscom.get_player(opponent_username, session=session)
        if not opponent:
            return
        is_draw = any(white['result'].lower().strip() == x for x in ['agreed', 'repetition', 'stalemate', 'insufficient', '50move', 'timevsinsufficient'])


        if not is_draw:
            white_win = white['result'].lower().strip() == 'win'

            player_win = white_win == user_is_white
        else:
            player_win = False
        
        match = Match.get(self.player, opponent, session=session)
        g = Game(
            url=url,
            player_a_win=player_win,
            draw=is_draw,
            date=datetime.fromtimestamp(int(end_time)),
            player_a=self.player,
            player_b=opponent,
            opening=opening,
            time_control=time_control,
            match=match
        )
        session.add(g)
        return g
    
    def games(self, *, session: Session):
        data = request_with_timing(self.url)
        if not data:
            return
        
        games = data['games']
        start = time()

        output = []
        for game in games:
            output.append((self.process_game(game, session=session)))

        print(f'Processing {len(games)} games took {round(time() - start, 2)} s')
        return [game for game in output if game]