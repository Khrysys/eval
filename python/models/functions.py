from functools import lru_cache
from math import exp, log10, sqrt
from time import sleep, time
import requests
from scipy.stats import norm # type: ignore

def sigmoid(x: float, a:float=1):
    return a * ((1 / (1 + exp((-x) + 0.5)))) - ((a - 1) / 2)

def prop_se(p: float, n: float):
    return sqrt(p * (1 - p) / n)

def z_score_2tail(x: float = 0.95):
    return norm.ppf(x / 2 + 0.5) # type: ignore

def expected_rating_diff(win_rate: float):
    return -326 * log10((1-win_rate) / win_rate)

def expected_win_rate(ra: float, rb: float):
    return 1 / (1 + 10 ** ((rb - ra) / 326)) # 326 is derived from wanting a 100 point rating difference to be a 67% win rate for the higher rated player

@lru_cache(maxsize=2 ** 10)
def make_request_with_retries(url: str, retries: int = 3, delay: int = 60):
    for i in range(retries):
        try:
            print(f'Getting {url} (Attempt {i + 1} / {retries})')
            response = requests.get(url, headers={
                'User-Agent': "{'username': 'khrysys'}"
            })
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                sleep(delay)
            else:
                response.raise_for_status()
        except (requests.exceptions.RequestException, requests.exceptions.Timeout, requests.exceptions.HTTPError) as e:
            print(f"Request to {url} failed with exception: {e}")
            sleep(delay)
    return None

def request_with_timing(url: str, retries: int = 3, delay: int = 60):
    start = time()
    r = make_request_with_retries(url, retries, delay)
    print(f'Request to {url} took {round(100 * (time() - start), 2)} ms')
    return r