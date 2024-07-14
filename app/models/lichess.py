from sqlmodel import Session, select

from .functions import make_request_with_retries, request_with_timing
from .player import Player
from .system import System

class Lichess(System):
    @staticmethod
    def get_player(username: str, timing: bool = False, *, session: Session):
        result = session.exec(select(Player).where(Player.username==username)).one_or_none()
        if result:
            return result
        url = f'https://lichess.org/api/user/{username}'
        if timing:
            data = request_with_timing(url)
        else:
            data = make_request_with_retries(url)
