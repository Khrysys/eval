from itertools import repeat
from math import floor, sqrt
from time import sleep, time
from scipy.stats import rankdata

from sqlalchemy import func
import numpy as np
from matplotlib import pyplot as plt
from sqlmodel import Session, select
from models import Player, Match, sigmoid,expected_rating_diff, Game, engine


def process_player(i: int, matches: dict[int, Match], valid_matches: set[int], unscaled_ratings: dict[str, tuple[float, float]], username: str):
    if not unscaled_ratings.get(username):
        unscaled_ratings[username] = (0, 0)
    prev_lower, prev_upper = unscaled_ratings[username]
    prev_midpoint = (prev_lower + prev_upper) / 2
    prev_half_width = (prev_upper - prev_lower) / 2
    
    for match_id in valid_matches:
        match = matches[match_id]
        is_player_a = username == match.player_a_username
        opponent = match.player_b if is_player_a else match.player_a
        opponent_rating = unscaled_ratings.get(opponent.username)
        if not opponent_rating:
            continue
        opponent_upper, opponent_lower = opponent_rating
        opponent_midpoint = (opponent_lower + opponent_upper) / 2
        opponent_half_width = (opponent_upper - opponent_lower) / 2
        
        lower, upper = match.interval_bounds()
        if not is_player_a:
            lower *= -1
            upper *= -1
            
        
        lower = sigmoid(lower, 1.2)
        upper = sigmoid(upper, 1.2)

        lower = expected_rating_diff(lower)
        upper = expected_rating_diff(upper)

        midpoint = (lower + upper) / 2
        half_width = (upper - lower) / 2
        
        next_midpoint = (((prev_midpoint - opponent_midpoint) - midpoint) / i) + prev_midpoint
        next_half_width = sqrt(pow(half_width, 2) + pow(prev_half_width, 2) + pow(opponent_half_width, 2))
        
        return (username, (next_midpoint - next_half_width, next_midpoint + next_half_width))

def loop_through(i: int, matches: dict[int, Match], valid_matches: dict[str, set[int]], unscaled_ratings: dict[str, tuple[float, float]]):
    results = map(process_player, repeat(i), repeat(matches), [valid_matches[username] for username in valid_matches], repeat(unscaled_ratings), [username for username in valid_matches])
    for result in results:
        if not result:
            continue
        username, rating = result
        unscaled_ratings[username]=rating
    return unscaled_ratings

def calculate(*, session: Session):
    # We are using a set to prevent double counting
    valid_matches: dict[str, set[int]] = {}
    all_valid_matches: set[int] = set()
    unscaled_ratings: dict[str, tuple[float, float]] = {}
    # Start with a player

    start = time()
    # Look at al confidence intervals
    matches = {m.id: m for m in session.exec(select(Match).join(Game, Match.id == Game.match_id).group_by(Match.id).having(func.count(Game.url) >= 2)).fetchall()} # type: ignore
    
    for id, match in matches.items():
        match.calculate_rating_difference(session=session)
        valid_matches.setdefault(match.player_a.username, set()).add(id) # type: ignore
        valid_matches.setdefault(match.player_b.username, set()).add(id) # type: ignore
        all_valid_matches.add(id) # type: ignore
            
    print(f"Filter took {time() - start} seconds")
    start = time()
    unscaled_ratings = loop_through(1, matches, valid_matches, unscaled_ratings) # type: ignore
    print(f'Loop took {time() - start} seconds')
    start = time()
    unscaled_ratings = loop_through(2, matches, valid_matches, unscaled_ratings) # type: ignore
    print(f'Loop took {time() - start} seconds')

    # Get all confidence intervals for this player

    final_ratings: dict[str, float] = {}

    for username in unscaled_ratings:
        lower, upper = unscaled_ratings[username]
        final_ratings[username] = (lower + upper) / 2

    if len(final_ratings) == 0:
        print('No players to run data on yet')
        return
    
    usernames: list[str] = []
    ratings: list[float] = []
    for username, rating in final_ratings.items():
        usernames.append(username)
        ratings.append(rating)

    ratings = np.array(ratings) # type: ignore
    
    minimum = np.min(ratings)
    ratings = (ratings-minimum)/(np.max(ratings)+np.max(ratings))

    start = time()
    # Normalize all ratings
    
    minimum = min(final_ratings.values())

    for username in final_ratings:
        final_ratings[username] -= minimum

    maximum = max(final_ratings.values())

    for username in final_ratings:
        final_ratings[username] *= 3000 / maximum

    # Update all ratings
    values = list(final_ratings.values())

    #print(x)
    print(f'{len(values)} players calculated')
    print(f'{len(valid_matches)} matches used')

    players = session.exec(select(Player)).all()

    for player in players:
        if final_ratings.get(player.username):
            player.rating = floor(final_ratings[player.username])
        else:
            player.rating = -1
        session.add(player)
    print(f'Normalization took {time() - start} seconds')
    x = rankdata(values, method='ordinal')/len(values)
    plt.scatter(x, values) # type: ignore
    plt.savefig(f'/var/snapshots/{len(x)}') # type: ignore
    plt.close()
    session.commit()

if __name__ == '__main__':
    while True:
        with Session(engine) as session:
            start = time()
            print('beginning rating calculation')
            calculate(session=session)
            print(f'Rating calculation took {time() - start} seconds.')
            t = 1200 - (time() - start)
            if t < 0:
                sleep(t)