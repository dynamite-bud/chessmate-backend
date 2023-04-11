from flask import Flask
from flask import jsonify, request
import chess
from stockfish import Stockfish

stockfish = Stockfish("stockfish-windows-2022-x86-64-avx2.exe")
# stockfish.set_depth(20)#How deep the AI looks
# stockfish.set_skill_level(20)#Highest rank stockfish
# stockfish.get_parameters()
# stockfish.get_evaluation() -> {'type': 'cp', 'value': 0.0}
# stockfish.set_fen_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")
# stockfish.get_top_moves(3)



app = Flask(__name__)

opening_moves = [
    ["e4", "e5","Nf3","Nc6","Bc4"], #Simple
    ["e4", "e6", "d4","d5"], #Simple
    ["e4", "e5", "Nf3", "Nc6", "Bb5"] #Simple
]

opening_title = [
    "The Italian Game",
    "The French Defense",
    "The Ruy-Lopez"
]
opening_description = [
    "The point is to control the center quickly with your pawn and knight and then put your bishop on its most dangerous square. You are also preparing to castle to safety.",
    "The French Defense is one of the first strategic openings every chess player should learn. After e5 (now or later), both sides will have pawn chains. One risk of the French Defense is that the c8-bishop can be very hard to develop.",
    "The Ruy Lopez is one of the oldest and most classic of all openings. It is named after a Spanish bishop who wrote one of the first books on chess. The Ruy Lopez attacks the knight which defends the e5-pawn. White hopes to use this attack to build more pressure on Black's central pawn."
]



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

    rating = request_data['rating']



    data = {
        "moves": "test"
    }
    return jsonify(data)