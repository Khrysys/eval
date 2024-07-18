from datetime import datetime
from io import StringIO
from sqlmodel import Session, select


from .functions import *

from .archive import Archive
from .player import Player
from .game import Game
from .match import Match
from .time_control import TimeControl
from .opening import Opening
from .system import System, SystemNames
from chess.pgn import read_game as load_pgn

class Chesscom(System):
    @staticmethod
    def get_player(username: str, timing: bool = False, *, session: Session):
        result = session.exec(select(Player).where(Player.username==username).where(Player.system==SystemNames.chesscom)).one_or_none()
        if result:
            return result
        
        url = f"https://api.chess.com/pub/player/{username}/stats"
        if timing:
            data = request_with_timing(url)
        else:
            data = make_request_with_retries(url)
        if not data:
            return None
        
        try:
            if 'chess_blitz' in data:
                rating = data['chess_blitz']['best']['rating']
            elif 'chess_rapid' in data:
                rating = data['chess_rapid']['best']['rating']
            elif 'chess_bullet' in data:
                rating = data['chess_bullet']['best']['rating']
            else:
                rating = 1500
        except:
            rating = 1500

        player = Player(username=username, rating=rating, system=SystemNames.chesscom)
        session.add(player)
        return player
    
    @staticmethod
    def get_archives(player: Player, start: int, end: int, timing: bool = False):
        
        url = f'https://api.chess.com/pub/player/{player.username}/games/archives'
        if timing:
            data = request_with_timing(url)
        else:
            data = make_request_with_retries(url)

        output: list[Archive] = []

        if not data:
            return output
        
        try:
            archives = data['archives']
        except:
            return output
        if end == -1:
            return [Archive(player=player, url=url) for url in archives]

        for i in range(start, end):
            try:
                url = archives[-(i + 1)]
                archive = Archive(player=player, url=url) # type: ignore
                output.append(archive)
            except:
                continue
        return output
    
    @staticmethod
    def get_games(archive: Archive, timing: bool = True, new_only: bool = False, *, session: Session):
        if timing:
            data = request_with_timing(archive.url)
        else:
            data = make_request_with_retries(archive.url)
        output: list[Game] = []
        if not data:
            return output
        
        games = data['games']
        start = time()

        for game in games:
            if not game.get('rules', '') == 'chess':
                continue
            
            url = game.get('url')
            if not url:
                continue
            
            g = session.exec(select(Game).where(Game.url==url)).one_or_none()
            if g:
                if not new_only:
                    output.append(g)
                continue
            
            time_control_code = game.get('time_control')
            if not time_control_code:
                print(f'No time control on {url}')
                time_control_code = ''
            time_control = TimeControl.get(time_control_code, session=session)

            pgn = game.get('pgn')
            if not pgn:
                print(f'No PGN on {url}')
                continue
            
            g = load_pgn(StringIO(pgn))
            if not g:
                print(f'PGN was invalid on {url}')
                continue
            
            eco = g.headers.get('ECO', '')
            eco_url = g.headers.get('ECOUrl', '')
            opening = Opening.get(eco, eco_url, session=session)

            white = game['white']
            black = game['black']
            end_time = game['end_time']

            user_is_white: bool = archive.player.username == white['username'].lower().strip()
            opponent_username = black['username'].lower().strip() if user_is_white else white['username'].lower().strip() 
            opponent = Chesscom.get_player(opponent_username, session=session)
            if not opponent:
                continue

            is_draw = any(white['result'].lower().strip() == x for x in ['agreed', 'repetition', 'stalemate', 'insufficient', '50move', 'timevsinsufficient'])


            if not is_draw:
                white_win = white['result'].lower().strip() == 'win'

                player_win = white_win == user_is_white
            else:
                player_win = False
            
            match = Match.get(archive.player, opponent, session=session)
            g = Game(
                url=url,
                player_a_win=player_win,
                draw=is_draw,
                date=datetime.fromtimestamp(int(end_time)),
                opening=opening,
                time_control=time_control,
                match=match
            )
            session.add(g)
            output.append(g)

        print(f'Processing {len(games)} games took {round(time() - start, 2)} s')
        return output
    
    
