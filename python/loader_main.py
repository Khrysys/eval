from sqlmodel import Session, select
from models import Player, engine, init_models

def recurse():
    with Session(engine, expire_on_commit=False) as session:
        players = session.exec(select(Player)).all()
        if len(players) == 0:
            return
        for player in players:
            for archive in player.archives(end=1, timing=True):
                games = archive.games(True, True, session=session)
                session.commit()

if __name__ == '__main__':
    init_models()
    while True:
        recurse()
