
from typing import TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel, Session, UniqueConstraint, select

from .player import Player
from .game import Game
from .functions import z_score_2tail, prop_se

class Match(SQLModel, table=True):
    __tableargs__ = (UniqueConstraint('interval_id'), )
    id: int | None = Field(default=None, primary_key=True)

    games: list['Game'] = Relationship(back_populates='match')

    interval_mean: float
    interval_half_turn: float

    def interval_bounds(self):
        return (self.interval_mean - abs(self.interval_half_turn), self.interval_mean + abs(self.interval_half_turn))

    def calculate_rating_difference(self, confidence: float = 0.95, *, session: Session):
        try:
            player_a = self.games[0].player_a
        except:
            return None

        points_a = self.points(player_a)
        
        z = z_score_2tail(confidence)

        mean = (points_a + 1) / (len(self.games) + 2)
        half_turn = abs(z * prop_se((points_a + 1) / (len(self.games) + 2), len(self.games)))

        self.interval_mean = mean
        self.interval_half_turn = half_turn # type: ignore
        session.add(self)
        
    def win_rate(self, player: Player):
        return self.points(player) / len(self.games)

    def points(self, player: Player):
        points = 0
        for game in self.games:
            if game.player_a == player:
                player_a = True
            elif game.player_b == player:
                player_a = False
            else: 
                raise Exception(f"Player {player.username} is not in Match(id={self.id})")

            if player_a:
                points += (1 if game.player_a_win else (0.5 if game.draw else 0))
            else:
                points += (0 if game.player_a_win else (0.5 if game.draw else 1))

        return points

    @staticmethod
    def get(p1: Player, p2: Player, *, session: Session):
        game = session.exec(select(Game).where(Game.player_a==p1).where(Game.player_b==p2)).first()
        if game:
            return game.match
        game = session.exec(select(Game).where(Game.player_b==p1).where(Game.player_a==p2)).one_or_none()
        if game:
            return game.match

        result = Match(games=[], interval_mean=0, interval_half_turn=0)
        session.add(result)
        return result
