from json import dump, load
from math import log10, sqrt
from numpy import linspace
from scipy.stats import norm

def prop_se(p, n):
    return sqrt(p * (1 - p) / n)

def expected_win_rate(ra, rb):
    return 1 / (1 + 10 ** ((rb - ra) / 326)) # 326 is derived from wanting a 100 point rating difference to be a 67% win rate for the higher rated player

def expected_rating_diff(win_rate):
    return 326 * log10((1 / win_rate)-1)

def z_score_2tail(x = 0.95):
    return norm.ppf(x / 2 + 0.5)

def compute_confidence_interval(rating_a, rating_b, wins_a, draws, wins_b, confidence=0.95):
    '''
    This should return a tuple of the expectations for player a in this match of (lower, upper) at the given confidence level
    '''
    score_a = wins_a + (draws / 2)
    games = wins_a + draws + wins_b

    z = z_score_2tail(confidence)

    expected_win_rate_a = expected_win_rate(rating_a, rating_b)

    standard_error = prop_se((score_a + 1) / (games + 2), games)

    #z_value = (expected_win_rate_a - (score_a / games) / standard_error)

    mean = (score_a + 1) / (games + 2)
    lower = mean - abs(z * standard_error)
    upper = mean + abs(z * standard_error)

    # We need to convert this to rating change somwhow
    return (expected_rating_diff(upper if upper < 1 else 0.999), expected_rating_diff(lower if lower > 0 else 0.001))
    
def get_player_range(player: str, rating: int, players: dict[str, int], games: list[dict[str, str | int]], min_games: int = 3):
    intervals = {}

    for game in games:
        try:
            who_played = game['players']
            results = game['wdl']


            if sum(results) < min_games:
                continue

            if player == who_played[0]:
                opponent = who_played[1]
                interval = compute_confidence_interval(rating, players[who_played[1]], results[0], results[1], results[2])
            elif player == who_played[1]:
                opponent = who_played[0]
                interval = compute_confidence_interval(rating, players[who_played[0]], results[2], results[1], results[0])
            else:
                continue

            lower, upper = interval
            if lower < 0:
                upper += abs(lower)
                lower = 0


            #interval = (lower, upper)
            print(interval)
            intervals[opponent] = interval
            
            
        except KeyError:
            pass 

    return intervals

    lower = 0
    median = 0
    upper = 0
    for i in intervals:
        l, u = i
        lower += l
        median += (l + u) / 2
        upper += u
    try:
        lower /= len(intervals)
        median /= len(intervals)
        upper /= len(intervals)
        half = abs(upper - lower) / 2
        lower = median - half
        upper = median + half

        print(f"Rating range for {player}: {round(median)} ± {round(half)} -> ({round(lower)}, {round(upper)})")
    except: pass

    return (lower, median, upper)
        

def update_all_players(players: dict[str, int], games: list[list[str | int]]):
    updated = {}
    for player in players.keys():
        updated[player] = get_player_range(player, players[player], players, games)

    dump(updated, open('test.json', 'w'), indent = 4)

if __name__ == '__main__':
    data = load(open('data.json'))

    players = data['players']
    games: list = data['games']

    #get_player_range('hikaru', players['hikaru'], players, games)
    update_all_players(players, games)

    import matplotlib.pyplot as plt
    # x = linspace(-3, 3, 200)
    # plt.plot(x, norm.ppf(x))
    # plt.show()
