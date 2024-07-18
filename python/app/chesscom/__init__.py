from fastapi import APIRouter, Depends
from pydantic import ValidationError
from sqlmodel import Session
from models import *

chesscomapi = APIRouter(prefix='/chesscom')

@chesscomapi.get('/player/{username}', response_model=Player)
async def get_chesscom_player(username: str, *, session: Session = Depends(get_session)):
    '''
    Loads a player from the chess.com database. If the player's username already exists from either chess.com or lichess, that player will be returned instead.
    '''
    return Chesscom.get_player(username, session=session)

@chesscomapi.get('/player/{username}/archives')
async def get_chesscom_player_archives(username: str, *, session: Session = Depends(get_session)):
    player = Chesscom.get_player(username, session=session)
    if not player:
        raise ValidationError(f'Player {username} was not found')   
    
    return player.archives(end=-1)

@chesscomapi.get('/player/{username}/archives/{index}')
async def get_chesscom_player_single_archive(username: str, index: int, *, session: Session = Depends(get_session)):
    player = Chesscom.get_player(username, session=session)
    if not player:
        raise ValidationError(f'Player {username} was not found')
    
    archives = player.archives(end=-1)
    if len(archives) < index:
        raise ValidationError(f'Index not found (Max: {len(archives)})')

    return archives[-(index+1)]

@chesscomapi.get('/player/{username}/archives/{index}/games')
async def get_chesscom_player_games_from_archive(username: str, index: int, *, session: Session = Depends(get_session)):
    player = Chesscom.get_player(username, session=session)
    if not player:
        raise ValidationError(f'Player {username} was not found')
    
    archives = player.archives(end=-1)
    if len(archives) < index:
        raise ValidationError(f'Index not found (Max: {len(archives)})')

    return archives[-(index+1)].games(session=session)