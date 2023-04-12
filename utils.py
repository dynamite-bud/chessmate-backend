from stockfish import Stockfish
import random
import chess.engine


stockfish = Stockfish("stockfish-windows-2022-x86-64-avx2.exe")


def get_centipawn(board):
    stockfish.set_fen_position(board)
    return stockfish.get_evaluation()["value"]

def generate_puzzle(level, num_puzzles=1):
    # Initialize Stockfish engine
    engine = chess.engine.SimpleEngine.popen_uci("stockfish-windows-2022-x86-64-avx2.exe")
    board = chess.Board()


    # Set skill level
    engine.configure({"Skill Level": level})

    # Analyze the current board position
    analysis = engine.analyse(board, chess.engine.Limit(time=2.0))
    score = analysis["score"]

    # Get a list of legal moves
    legal_moves = list(board.legal_moves)

    if legal_moves:
        # Select a random legal move
        move = random.choice(legal_moves)

        # Apply the random move to the board
        board.push(move)

        # Run Stockfish engine to find the best move for the current position
        result = engine.play(board, chess.engine.Limit(time=2.0))
        best_move = result.move

        # Create the puzzle
        puzzle = {
            "fen": board.fen(),
            "score": score.white().score(),
            "best_move": best_move.uci()
        }
    else:
        # Handle case where there are no legal moves
        puzzle = {
            "fen": board.fen(),
            "score": score.white().score(),
            "best_move": None
        }
    
    # Clear the board for the next puzzle
    board.reset()

    # Close the engine
    engine.quit()

    return puzzle

def get_levels_by_group(group_number):
    if group_number == 7:
        return [19, 20]
    
    start_number = (group_number - 1) * 3 + 1
    return list(range(start_number, start_number + 3))