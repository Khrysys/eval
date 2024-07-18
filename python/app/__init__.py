from fastapi import Depends, FastAPI
from sqlmodel import Session, select

from models import get_session, Player, Game, Match, Opening, TimeControl


app = FastAPI(prefix='/api')
@app.get('/count/player')
def get_player_count(*, session: Session = Depends(get_session)):
    return len(session.exec(select(Player)).all())

@app.get('/count/game')
def get_game_count(*, session: Session = Depends(get_session)):
    return len(session.exec(select(Game)).all())

@app.get('/count/match')
def get_match_count(*, session: Session = Depends(get_session)):
    return len(session.exec(select(Match)).all())

@app.get('/opening')
def get_all_openings(*, session: Session = Depends(get_session)):
    return session.exec(select(Opening)).all()

@app.get('/time_control')
def get_all_time_controls(*, session: Session = Depends(get_session)):
    return session.exec(select(TimeControl)).all()

from .chesscom import chesscomapi as chesscom

app.include_router(chesscom)
#app.include_router(lichessapi)