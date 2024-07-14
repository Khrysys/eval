from sqlmodel import Session, select


from .functions import *

from .player import Player
from .system import System, SystemNames

class Chesscom(System):
    @staticmethod
    def get_player(username: str, timing: bool = False, *, session: Session):
        result = session.exec(select(Player).where(Player.username==username)).one_or_none()
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