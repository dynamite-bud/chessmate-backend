from flask import Flask
from flask import jsonify, request
from pymongo import MongoClient
from stockfish import Stockfish
from openings import *
from utils import *

stockfish = Stockfish("stockfish-windows-2022-x86-64-avx2.exe")
# stockfish.set_depth(20)#How deep the AI looks
# stockfish.set_skill_level(20)#Highest rank stockfish
# stockfish.get_parameters()
# stockfish.get_evaluation() -> {'type': 'cp', 'value': 0.0}
# stockfish.set_fen_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")
# stockfish.get_top_moves(3)

app = Flask(__name__)
app.config['SECRET_KEY'] = "q2edf4r5t6y7u8i9o0p8fdgh"
app.config['MONGO_URI'] = "mongodb+srv://admin:BwHJZgZP5tyzrQuU@user-db.kia6aok.mongodb.net/?retryWrites=true&w=majority"

# MongoDB setup
client = MongoClient('mongodb+srv://admin:BwHJZgZP5tyzrQuU@user-db.kia6aok.mongodb.net/?retryWrites=true&w=majority')
db = client['users']
users = db['users']

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

# Endpoint for user login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    # Check if username and password are correct
    user = users.find_one({'username': username, 'password': password})
    if not user:
        return jsonify({'error': 'Invalid username or password'}), 401

    return jsonify({'message': 'Login successful'}), 200

# Endpoint for user registration
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']

    # Check if username already exists
    if users.find_one({'username': username}):
        return jsonify({'error': 'Username already taken'}), 400

    # Insert new user to database
    users.insert_one({'username': username, 'password': password})
    return jsonify({'message': 'User registered successfully'}), 201