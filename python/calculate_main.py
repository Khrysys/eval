from itertools import repeat
from math import floor, sqrt
from os import mkdir, path
from time import sleep, time
from scipy.stats import rankdata

from sqlalchemy import func
import numpy as np
from matplotlib import pyplot as plt
from sqlmodel import Session, select
from models import Player, Match, sigmoid,expected_rating_diff, Game, engine
from scipy.stats import norm

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
    unscaled_ratings: dict[str, tuple[float, float]] = {}
    final_ratings: dict[str, float] = {}
    # Start with a player

    start = time()
    # Look at al confidence intervals
    matches = {m.id: m for m in session.exec(select(Match).join(Game, Match.id == Game.match_id).group_by(Match.id).having(func.count(Game.url) >= 2)).fetchall()} # type: ignore
    print(f"Filter took {time() - start} seconds")
    start = time()
    
    for id, match in matches.items():
        valid_matches.setdefault(match.player_a.username, set()).add(id) # type: ignore
        valid_matches.setdefault(match.player_b.username, set()).add(id) # type: ignore

    print(f'Sorting took {time() - start} seconds')
            
    start = time()
    unscaled_ratings = loop_through(1, matches, valid_matches, unscaled_ratings) # type: ignore
    print(f'Loop took {time() - start} seconds')
    start = time()
    unscaled_ratings = loop_through(2, matches, valid_matches, unscaled_ratings) # type: ignore
    print(f'Loop took {time() - start} seconds')

    # Get all confidence intervals for this player

    start = time()

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
    # Normalize all ratings
    ratings = (ratings-minimum)*(3000/(np.max(ratings)-minimum))


    # Update all ratings

    #print(x)
    print(f'{len(ratings)} players calculated')
    print(f'{len(matches)} matches used')

    players = session.exec(select(Player)).all()

    for i in range(0, len(ratings)):
        final_ratings[usernames[i]] = ratings[i]

    for player in players:
        if final_ratings.get(player.username):
            player.rating = floor(final_ratings[player.username])
        else:
            player.rating = -1
        session.add(player)
    print(f'Normalization took {time() - start} seconds')
    start = time()
    x = rankdata(ratings, method='ordinal')/len(ratings)
    plt.scatter(x, ratings) # type: ignore
    plt.savefig(f'/var/snapshots/{len(ratings)}') # type: ignore
    plt.close()
    mu, std = norm.fit(ratings)
    plt.hist(ratings, bins=25, density=True)
    xmin, xmax = plt.xlim()
    x = np.linspace(xmin, xmax, 200)
    p = norm.pdf(x, mu, std)
    plt.plot(x, p, 'k', linewidth=2)
    title = "Fit results: mu = %.2f,  std = %.2f" % (mu, std)
    plt.title(title)
    plt.savefig(f'/var/snapshots/pdf/{len(ratings)}') # type: ignore
    plt.close()
    print(f'Outputting snapshot took {time() - start} seconds')
    session.commit()

if __name__ == '__main__':
    if not path.exists('/var/snapshots/pdf'):
        mkdir('/var/snapshots/pdf')
    while True:
        start = time()
        with Session(engine) as session:
            print('Beginning Rating Calculation')
            calculate(session=session)
            print(f'Rating calculation took {time() - start} seconds.')
        t = 300 - (time() - start)
        if t > 0:
            print(f'Waiting for {t} seconds')
            sleep(t)