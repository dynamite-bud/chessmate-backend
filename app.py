from flask import Flask
from flask import jsonify, request
import chess.engine
from stockfish import Stockfish
import random
from openings import opening_moves, opening_title, opening_description

stockfish = Stockfish("stockfish-windows-2022-x86-64-avx2.exe")
# stockfish.set_depth(20)#How deep the AI looks
# stockfish.set_skill_level(20)#Highest rank stockfish
# stockfish.get_parameters()
# stockfish.get_evaluation() -> {'type': 'cp', 'value': 0.0}
# stockfish.set_fen_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")
# stockfish.get_top_moves(3)

app = Flask(__name__)

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

@app.route('/')
def hello() :
    data = {
        "moves": "test"
    }
    return jsonify(data)

@app.route('/best-move', methods=['POST'])
def get_best_move():
    request_data = request.get_json()
    # eg. request_data = {"board": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "count": 5}

    board = request_data['board']

    stockfish.set_depth(20)  # How deep the AI looks
    stockfish.set_skill_level(20)  # Highest rank stockfish
    stockfish.set_fen_position(board)
    best_move = stockfish.get_top_moves(request_data['count'])

    moves = []
    for data in best_move:
        moves.append(data["Move"])
    print(moves)

    response = {
        "best_move": moves
    }
    return jsonify(response)

@app.route('/get-opening', methods=['POST'])
def get_oppening():
    request_data = request.get_json()

    rating = request_data['rating']

    cnv_rating = (rating) * (3) / (2500)
    
    # convert cnv_rating to int
    cnv_rating = int(cnv_rating)

    # get opening
    moves = opening_moves[:cnv_rating]
    title = opening_title[:cnv_rating]
    description = opening_description[:cnv_rating]

    response = {
        "moves": moves,
        "title": title,
        "description": description
    }
    return jsonify(response)

@app.route('/get-puzzle', methods=['POST'])
def get_puzzle() :
    request_data = request.get_json()

    group = request_data['group']

    levels = get_levels_by_group(group)

    puzzles = []
    for level in levels:
        puzzles.append(generate_puzzle(level,1))

    data = {
        "puzzles": puzzles
    }
    return jsonify(data)

@app.route('/get-centipawn', methods=['POST'])
def get_centipawn():
    request_data = request.get_json()
    board = request_data['board']
    stockfish.set_fen_position(board)
    return stockfish.get_evaluation()["value"]