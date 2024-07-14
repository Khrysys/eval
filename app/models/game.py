from datetime import datetime
from typing import TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from . import Player, Opening, TimeControl, Match

class Game(SQLModel, table=True):
    url: str = Field(primary_key=True)
    player_a_win: bool
    draw: bool
    date: datetime

    time_control_code: str | None = Field(default=None, foreign_key='timecontrol.code')
    player_a_username: str | None = Field(default=None, foreign_key='player.username')
    player_b_username: str | None = Field(default=None, foreign_key='player.username')
    opening_eco: str | None = Field(default=None, foreign_key='opening.eco')
    match_id: int | None = Field(default=None, foreign_key='match.id')

    player_a: 'Player' = Relationship(sa_relationship_kwargs={
        'foreign_keys':'game.c.player_a_username', 
    })
    player_b: 'Player' = Relationship(sa_relationship_kwargs={
        'foreign_keys':'game.c.player_b_username', 
    })
    opening: 'Opening' = Relationship(sa_relationship_kwargs={
        'foreign_keys': 'game.c.opening_eco'
    })
    time_control: 'TimeControl' = Relationship(sa_relationship_kwargs={
        'foreign_keys': 'game.c.time_control_code'
    })
    match: 'Match' = Relationship(sa_relationship_kwargs={
        'foreign_keys': 'game.c.match_id'
    })
