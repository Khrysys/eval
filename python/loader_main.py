from math import floor, sqrt
from models import *
import matplotlib.pyplot as plt
from scipy.stats import rankdata # type: ignore

def loop_through(i: int, matches: list[Match], valid_matches: dict[str, set[int]], unscaled_ratings: dict[str, tuple[float, float]]):
    for username, data in valid_matches.items():
        if username not in unscaled_ratings:
            unscaled_ratings[username] = (0, 0)
        prev_lower, prev_upper = unscaled_ratings[username]
        prev_midpoint = (prev_lower + prev_upper) / 2
        prev_half_width = (prev_upper - prev_lower) / 2
            
        for match_id in data:
            match = [match for match in matches if match.id == match_id][0] # This is safe, we know that match_id only exists once and only once inside of this set
            is_player_a = username == match.player_a.username
            opponent = match.player_b if is_player_a else match.player_a
            if opponent.username not in unscaled_ratings:
                continue

            opponent_upper, opponent_lower = unscaled_ratings[opponent.username]
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
            
            unscaled_ratings[username] = (next_midpoint - next_half_width, next_midpoint + next_half_width)
            
    return unscaled_ratings
                

def calculate(*, session: Session):
    effective_intervals = 0
    # We are using a set to prevent double counting
    valid_matches: dict[str, set[int]] = {}
    unscaled_ratings: dict[str, tuple[float, float]] = {}
    # Start with a player

    # Look at al confidence intervals
    matches = session.exec(select(Match)).all()

    for match in matches:
        if len(match.games) < 2:
            continue

        match.calculate_rating_difference(session=session)
        
        player_a = match.player_a.username
        player_b = match.player_b.username
        if player_a not in valid_matches:
            valid_matches[player_a] = set()
        if player_b not in valid_matches:
            valid_matches[player_b] = set()

        if match.id:
            effective_intervals += 1
            valid_matches[player_a].add(match.id)
            valid_matches[player_b].add(match.id)

    unscaled_ratings = loop_through(1, list(matches), valid_matches, unscaled_ratings)
    for i in range(1, 5):
        unscaled_ratings = loop_through(i, list(matches), valid_matches, unscaled_ratings)

    # Get all confidence intervals for this player

    final_ratings: dict[str, float] = {}

    for username in unscaled_ratings:
        lower, upper = unscaled_ratings[username]
        final_ratings[username] = (lower + upper) / 2

    if len(final_ratings) == 0:
        print('No players to run data on yet')
        return

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
    print(f'{effective_intervals} intervals used')

    players = session.exec(select(Player)).all()

    for player in players:
        if player.username in final_ratings:
            player.rating = floor(final_ratings[player.username])
        else:
            player.rating = -1
        session.add(player)
    x = rankdata(values, method='ordinal')/len(values)
    plt.scatter(x, values) # type: ignore
    plt.savefig(f'var/loader/{len(x)}') # type: ignore
    plt.close()
    session.commit()


def recurse():
    with Session(engine, expire_on_commit=False) as session:
        players = session.exec(select(Player)).all()
        if len(players) == 0:
            return
        for player in players:
            for archive in player.archives(end=1, timing=True):
                games = archive.games(True, True, session=session)
                session.commit()
                if len(games) > 100:
                    calculate(session=session)

if __name__ == '__main__':
    init_models()
    with Session(engine) as session:
        Chesscom.get_player('hikaru', timing=True, session=session)
        session.commit()
    while True:
        recurse()
