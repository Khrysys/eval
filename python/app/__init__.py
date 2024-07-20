from fastapi import Depends, FastAPI
from sqlalchemy import func
from sqlmodel import Session, select

from models import get_session, Player, Game, Match, Opening, TimeControl


app = FastAPI()
@app.get('/count/player', response_model=int)
def get_player_count(*, session: Session = Depends(get_session)):
    return session.exec(select(func.count()).select_from(Player)).first()

@app.get('/count/game', response_model=int)
def get_game_count(*, session: Session = Depends(get_session)):
    return session.exec(select(func.count()).select_from(Game)).first()

@app.get('/count/match', response_model=int)
def get_match_count(*, session: Session = Depends(get_session)):
    return session.exec(select(func.count()).select_from(Match)).first()

@app.get('/opening', response_model=list[Opening])
def get_all_openings(*, session: Session = Depends(get_session)):
    return session.exec(select(Opening)).all()

@app.get('/time_control', response_model=list[TimeControl])
def get_all_time_controls(*, session: Session = Depends(get_session)):
    return session.exec(select(TimeControl)).all()

from .chesscom import chesscomapi as chesscom

app.include_router(chesscom)
#app.include_router(lichessapi)