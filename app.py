from flask import Flask
from flask import jsonify, request
import chess
from stockfish import Stockfish

stockfish = Stockfish("stockfish-windows-2022-x86-64-avx2.exe")
app = Flask(__name__)

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
