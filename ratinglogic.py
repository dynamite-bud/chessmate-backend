import numpy as np
import pymc3 as pm
from stockfish import Stockfish
import numpy as np
import pymc3 as pm
from utils import *

def adaptive_rating_system(previous_rating, fen_list, player_color, num_samples=2000, K=32, stockfish_path=stockfish_path):
    """
    Updates the player's rating based on centipawn values from the current move using Bayesian inference and MCMC sampling.

    Args:
        previous_rating (float): The player's previous rating.
        fen_list (list): A list of FEN strings, representing the game states from start to end.
        player_color (str): The color of the player ('white' or 'black').
        num_samples (int, optional): The number of MCMC samples. Defaults to 2000.
        K (int, optional): A constant used to scale the rating change. Defaults to 32.
        stockfish_path (str, optional): Path to the Stockfish binary. Defaults to "stockfish".

    Returns:
        float: The updated rating.
    """

    # print("----------------------------")
    # print(fen_list)
    def rating_to_skill_level(rating):
        if rating < 0:
            return 0
        skill_level = int((rating / 3000) * 20)
        return max(0, min(skill_level, 20))

    
    # Initialize Stockfish engine
    stockfish = Stockfish(path=stockfish_path)
    # stockfish.set_skill_level(rating_to_skill_level(previous_rating))
    stockfish.set_skill_level(10)
    stockfish.set_depth(10)

    # Get centipawn differences for player's moves
    centipawn_diffs = []
    for i in range(len(fen_list) - 1):
        stockfish.set_fen_position(fen_list[i+1])
        current_turn = "white" if "w" in fen_list[i] else "black"

        if current_turn == player_color:
            player_eval = stockfish.get_evaluation()
            print(player_eval)
            player_centipawn = player_eval["value"] if player_eval["type"] == "cp" else 0

            # Get Stockfish's best move and its evaluation
            stockfish.set_fen_position(fen_list[i])
            best_move = stockfish.get_best_move()
            # create a new board with the best move applied
            board = chess.Board(fen_list[i])
            board.push_uci(best_move)
            stockfish.set_fen_position(board.fen())
            best_eval = stockfish.get_evaluation()
            print(best_eval)

            # Get centipawn value for Stockfish's best move
            stockfish_centipawn = best_eval["value"] if best_eval["type"] == "cp" else 0

            # Calculate centipawn difference
            centipawn_diff = player_centipawn - stockfish_centipawn
            centipawn_diffs.append(centipawn_diff)

    print(centipawn_diffs)
    # Define prior distribution of player's rating
    with pm.Model() as model:
        mu = pm.Normal('mu', mu=previous_rating, sigma=1000)
        sigma = pm.HalfNormal('sigma', sigma=1000) #pm.HalfCauchy('sigma', beta=25) #pm.Exponential('sigma', lam=1/50)
        rating_diffs = pm.Normal('rating_diffs', mu=0, sigma=sigma, shape=len(centipawn_diffs))
        ratings = pm.Deterministic('ratings', mu + rating_diffs)

        # Define likelihood of the observed centipawn differences
        # likelihood_values = 1 / (1 + 10 ** (-np.array(centipawn_diffs) / (K/400)))
        # likelihood = pm.Bernoulli('likelihood', p=likelihood_values, observed=np.ones(len(centipawn_diffs)))
        observed_centipawn_diffs = np.array(centipawn_diffs)
        likelihood = pm.Normal('likelihood', mu=ratings, sigma=sigma, observed=observed_centipawn_diffs)


        # Simulate games and update posterior distribution
        start = {'mu': previous_rating, 'sigma': 100, 'rating_diffs': np.zeros(len(centipawn_diffs))}
        trace = pm.sample(draws=num_samples, tune=num_samples//2, cores=2, start=start)
        # trace = pm.sample(draws=num_samples, tune=num_samples//2, cores=2)
        updated_rating = trace['ratings'][-1].mean()  # Update the player's rating

    return updated_rating


def initial_rating(player_puzzle_centipawn, stockfish_puzzle_centipawn):
    """
    Computes a user rating based on centipawn values of puzzles played by the user and best move
    for the same puzzle from Stockfish using Bayesian inference with PyMC3.

    Args:
        num_samples (int): The number of samples for the PyMC3 MCMC algorithm.
        player_puzzle_centipawn (list): A list of centipawn values of puzzles played by the user.
        stockfish_puzzle_centipawn (list): A list of centipawn values of the best moves for the same puzzles from Stockfish.

    Returns:
        float: The estimated user rating.

    Raises:
        ValueError: If the number of player centipawn values does not match the number of Stockfish centipawn values.
    """
    
    num_samples =1000
    if len(player_puzzle_centipawn) == len(stockfish_puzzle_centipawn):
        # Define prior distribution of player's rating
        initial_rating = np.mean(player_puzzle_centipawn)  # Choose a suitable initial rating
        sd = 200  # Choose a suitable standard deviation
        
        with pm.Model() as model:
            mu = pm.Normal('mu', mu=initial_rating, sigma=sd)
            sigma = pm.HalfNormal('sigma', sigma=100)
            rating_diffs = pm.Normal('rating_diffs', mu=mu, sigma=sigma, observed=np.array(player_puzzle_centipawn) - np.array(stockfish_puzzle_centipawn))
            
            # Simulate games and update posterior distribution
            trace = pm.sample(draws=num_samples, tune=num_samples//2, cores=2)
            player_rating = trace['mu'].mean()  # Update the player's rating
        print("Player centipawn values: ", player_puzzle_centipawn)
        print("Stockfish centipawn values: ", stockfish_puzzle_centipawn)
        print("Player rating: ", player_rating)
        return player_rating
    else:
        raise ValueError("The number of player centipawn values must match the number of Stockfish centipawn values.")