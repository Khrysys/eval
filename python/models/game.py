from datetime import datetime
from typing import TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel, ForeignKeyConstraint

if TYPE_CHECKING:
    from .player import Player
    from .opening import Opening
    from .time_control import TimeControl
    from .match import Match

class Game(SQLModel, table=True):
    url: str = Field(primary_key=True)  
    player_a_win: bool
    draw: bool
    date: datetime

    time_control_code: str | None = Field(default=None, foreign_key='timecontrol.code')
    opening_eco: str | None = Field(default=None, foreign_key='opening.eco')
    match_id: int | None = Field(default=None, foreign_key='match.id')

    opening: 'Opening' = Relationship(sa_relationship_kwargs={
        'foreign_keys': 'game.c.opening_eco'
    })
    time_control: 'TimeControl' = Relationship(sa_relationship_kwargs={
        'foreign_keys': 'game.c.time_control_code'
    })
    match: 'Match' = Relationship(back_populates='games', sa_relationship_kwargs={
        'foreign_keys': 'game.c.match_id'
    })