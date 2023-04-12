import numpy as np
import pymc3 as pm
from stockfish import Stockfish
import numpy as np
import pymc3 as pm

def adaptive_rating_system(previous_rating, fen_list, player_color, num_samples=2000, K=32, stockfish_path="stockfish"):
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

    # Initialize Stockfish engine
    stockfish = Stockfish(path=stockfish_path)

    # Get centipawn differences for player's moves
    centipawn_diffs = []
    for i in range(len(fen_list) - 1):
        stockfish.set_fen_position(fen_list[i])
        current_turn = 'white' if ' w ' in fen_list[i] else 'black'

        if current_turn == player_color:
            player_eval = stockfish.get_evaluation()
            player_centipawn = player_eval["value"] if player_eval["type"] == "cp" else 0

            # Get Stockfish's best move and its evaluation
            best_move = stockfish.get_best_move()
            stockfish.set_fen_position(fen_list[i + 1])
            best_eval = stockfish.get_evaluation()

            # Get centipawn value for Stockfish's best move
            stockfish_centipawn = best_eval["value"] if best_eval["type"] == "cp" else 0

            # Calculate centipawn difference
            centipawn_diff = player_centipawn - stockfish_centipawn
            centipawn_diffs.append(centipawn_diff)

    # Define prior distribution of player's rating
    with pm.Model() as model:
        mu = pm.Normal('mu', mu=previous_rating, sigma=200)
        sigma = pm.HalfNormal('sigma', sigma=100)
        rating_diffs = pm.Normal('rating_diffs', mu=0, sigma=sigma, shape=len(centipawn_diffs))
        ratings = pm.Deterministic('ratings', mu + rating_diffs)

        # Define likelihood of the observed centipawn differences
        likelihood_values = 1 / (1 + 10 ** (-np.array(centipawn_diffs) / (K/400)))
        likelihood = pm.Bernoulli('likelihood', p=likelihood_values, observed=np.ones(len(centipawn_diffs)))

        # Simulate games and update posterior distribution
        trace = pm.sample(draws=num_samples, tune=num_samples//2, cores=2)
        updated_rating = trace['ratings'][-1].mean()  # Update the player's rating

    return updated_rating


def initial_rating(num_samples, player_puzzle_centipawn, stockfish_puzzle_centipawn):
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
    if len(player_puzzle_centipawn) == len(stockfish_puzzle_centipawn):
        # Define prior distribution of player's rating
        initial_rating = np.mean(player_puzzle_centipawn)  # Choose a suitable initial rating
        sd = 200  # Choose a suitable standard deviation
        
        with pm.Model() as model:
            mu = pm.Normal('mu', mu=initial_rating, sigma=sd)
            sigma = pm.HalfNormal('sigma', sigma=100)
            rating_diffs = pm.Normal('rating_diffs', mu=mu, sigma=sigma, observed=player_puzzle_centipawn - stockfish_puzzle_centipawn)

            # Simulate games and update posterior distribution
            trace = pm.sample(draws=num_samples, tune=num_samples//2, cores=2)
            player_rating = trace['mu'].mean()  # Update the player's rating
        
        return player_rating
    else:
        raise ValueError("The number of player centipawn values must match the number of Stockfish centipawn values.")