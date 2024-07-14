from typing import Annotated
from typer import Option, Typer
from models import *
from rich.progress import track

app = Typer()

@app.command()
def add(username: str, is_lichess: Annotated[bool, Option('--lichess')] = False, timing_info: Annotated[bool, Option('--timing')] = False):
    '''
    Adds a user to the database from an online chess site API (chess.com or lichess)
    '''
    with Session(engine) as session:
        if is_lichess:
            player = Lichess.get_player(username, timing_info, session=session)
        else:
            player = Chesscom.get_player(username, timing_info, session=session)

        if not player:
            print(f'There was an error loading {username}!')
            return

        print(f'Found {username} with rating {player.rating}')

@app.command()
def archives(username: str, start_month: int = 0, total_months: int=5, is_lichess: Annotated[bool, Option('--lichess')] = False, return_object: bool = False):
    '''
    Adds a players archived games of the last specified months. Chess.com users get a convenient API endpoint directly for this, Lichess isn't as easy.
    '''
    with Session(engine) as session:
        if is_lichess:
            raise NotImplementedError
        else:
            player = Chesscom.get_player(username, session=session)
        
        if not player:
            print(f'There was an error loading {username}!')
            return
        
        archives = player.archives(start_month, start_month+total_months)
        for archive in archives:
            archive.games(session=session)

@app.command()
def compute_intervals(confidence: float = 0.95):
    '''
    Computes confidence intervals for all matches currently in the database.
    '''
    with Session(engine) as session:
        matches = session.exec(select(Match)).all()
        for match in track(matches, description=f'Processing {len(matches)} matches...'):
            match.calculate_rating_difference(confidence, session=session)
        print(f'Processed {len(matches)} matches')
'''

app = typer.Typer()

LICENSE_STR = """
   Copyright (c) 2015 Miguel A. Ballicora
   Ordo is program for calculating ratings of engine or chess players

   Ordo is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   Ordo is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with Ordo.  If not, see <http://www.gnu.org/licenses/>.
"""

COPYRIGHT_STR = "Copyright (c) 2015 Miguel A. Ballicora\nThere is NO WARRANTY of any kind\n"

INTRO_STR = "Program to calculate individual ratings\n"

EXAMPLE_OPTIONS = "-a 2500 -p input.pgn -o output.txt"

EXAMPLE_STR = """
  - Processes input.pgn (PGN file) to calculate ratings to output.txt.
  - The general pool will have an average of 2500
"""

def parameter_error():
    print("Parameter error")
    raise typer.Exit()

def example():
    print(EXAMPLE_OPTIONS)
    print(EXAMPLE_STR)

def usage():
    print(LICENSE_STR)
    print(COPYRIGHT_STR)
    print(INTRO_STR)
    example()

from enum import Enum
from typing import List, Tuple

# Equivalent to 'enum' in C
class AnchorSZ(Enum):
    MAX_ANCHORSIZE = 1024

@app.command()
def main(
    average: int = typer.Option(2500, "-a", "--average", help="Set rating for the pool average"),
    anchor: str = typer.Option(None, "-A", "--anchor", help="Anchor: rating given by '-a' is fixed for <player>"),
    pool_relative: bool = typer.Option(False, "-V", "--pool-relative", help="Errors relative to pool average, not to the anchor"),
    multi_anchors: str = typer.Option(None, "-m", "--multi-anchors", help="Multiple anchors: file contains rows of 'AnchorName', AnchorRating"),
    loose_anchors: str = typer.Option(None, "-y", "--loose-anchors", help="Loose anchors: file contains rows of 'Player', Rating, Uncertainty"),
    relations: str = typer.Option(None, "-r", "--relations", help="Relations: rows of 'PlayerA', 'PlayerB', delta_rating, uncertainty"),
    remove_older: bool = typer.Option(False, "-R", "--remove-older", help="No output of older 'related' versions (given by -r)"),
    white: float = typer.Option(0.0, "-w", "--white", help="White advantage value (default=0.0)"),
    white_error: float = typer.Option(0.0, "-u", "--white-error", help="White advantage uncertainty value (default=0.0)"),
    white_auto: bool = typer.Option(False, "-W", "--white-auto", help="White advantage will be automatically adjusted"),
    draw: float = typer.Option(50.0, "-d", "--draw", help="Draw rate value % (default=50.0)"),
    draw_error: float = typer.Option(0.0, "-k", "--draw-error", help="Draw rate uncertainty value % (default=0.0 %)"),
    draw_auto: bool = typer.Option(False, "-D", "--draw-auto", help="Draw rate value will be automatically adjusted"),
    scale: float = typer.Option(202.0, "-z", "--scale", help="Set rating for winning expectancy of 76% (default=202)"),
    table: bool = typer.Option(False, "-T", "--table", help="Display winning expectancy table"),
    pgn: str = typer.Option(None, "-p", "--pgn", help="Input file, PGN format"),
    pgn_list: str = typer.Option(None, "-P", "--pgn-list", help="Multiple input: file with a list of PGN files"),
    output: str = typer.Option(None, "-o", "--output", help="Output file, text format"),
    csv: str = typer.Option(None, "-c", "--csv", help="Output file, comma separated value format"),
    elostat: bool = typer.Option(False, "-E", "--elostat", help="Output files in elostat format (rating.dat, programs.dat & general.dat)"),
    head2head: str = typer.Option(None, "-j", "--head2head", help="Output file with head to head information"),
    groups: str = typer.Option(None, "-g", "--groups", help="Outputs group connection info (no rating output)"),
    force: bool = typer.Option(False, "-G", "--force", help="Force program to run ignoring isolated-groups warning"),
    simulations: int = typer.Option(None, "-s", "--simulations", help="Perform NUM simulations to calculate errors"),
    error_matrix: str = typer.Option(None, "-e", "--error-matrix", help="Save an error matrix (use of -s required)"),
    cfs_matrix: str = typer.Option(None, "-C", "--cfs-matrix", help="Save a matrix (comma separated value .csv) with confidence for superiority (-s was used)"),
    cfs_show: bool = typer.Option(False, "-J", "--cfs-show", help="Output an extra column with confidence for superiority (relative to the player in the next row)"),
    confidence: float = typer.Option(95.0, "-F", "--confidence", help="Confidence to estimate error margins (default=95.0)"),
    ignore_draws: bool = typer.Option(False, "-X", "--ignore-draws", help="Do not take into account draws in the calculation"),
    threshold: int = typer.Option(None, "-t", "--threshold", help="Threshold of games for a participant to be included"),
    decimals: str = typer.Option(None, "-N", "--decimals", help="a=rating decimals, b=score decimals (optional)"),
    ml: bool = typer.Option(False, "-M", "--ml", help="Force maximum-likelihood estimation to obtain ratings"),
    cpus: int = typer.Option(None, "-n", "--cpus", help="Number of processors used in simulations"),
    columns: str = typer.Option(None, "-U", "--columns", help="Info in output (default columns are '0,1,2,3,4,5')"),
    synonyms: str = typer.Option(None, "-Y", "--synonyms", help="Name synonyms (comma separated value format). Each line: main,syn1,syn2 or 'main','syn1','syn2'"),
    aliases: str = typer.Option(None, "--aliases", help="Same as --synonyms FILE"),
    include: str = typer.Option(None, "-i", "--include", help="Include only games of participants present in FILE"),
    exclude: str = typer.Option(None, "-x", "--exclude", help="Names in FILE will not have their games included"),
    no_warnings: bool = typer.Option(False, "--no-warnings", help="Suppress warnings of names from -x or -i that do not match names in input file"),
    column_format: str = typer.Option(None, "-b", "--column-format", help="Format column output, each line from FILE being <column>,<width>,'Header'"),
):
    """
    Ordo is a program for calculating ratings of engine or chess players.
    """
    print(f"Processing {pgn} with average rating {average} to {output}")

'''
if __name__ == "__main__":
    app()