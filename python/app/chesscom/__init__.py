from fastapi import APIRouter, Depends
from sqlmodel import Session
from models import *

chesscomapi = APIRouter(prefix='/chesscom')

@chesscomapi.get('/player/{username}', response_model=Player)
async def get_chesscom_player(username: str, *, session: Session = Depends(get_session)):
    '''
    Loads a player from the chess.com database. If the player's username already exists from either chess.com or lichess, that player will be returned instead.
    '''
    return Chesscom.get_player(username, session=session)