from flask import Flask, session
from flask import jsonify, request
from stockfish import Stockfish
from openings import *
from utils import *
from ratinglogic import *
from flask import Blueprint
from routes.auth import auth_app
from pymongo import MongoClient
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
app.register_blueprint(auth_app)

# MongoDB setup
client = MongoClient('mongodb+srv://admin:BwHJZgZP5tyzrQuU@user-db.kia6aok.mongodb.net/?retryWrites=true&w=majority')
db = client['users']
users = db['users']

stockfish = Stockfish(stockfish_path)

# stockfish.set_depth(20)#How deep the AI looks
# stockfish.set_skill_level(20)#Highest rank stockfish
# stockfish.get_parameters()
# stockfish.get_evaluation() -> {'type': 'cp', 'value': 0.0}
# stockfish.set_fen_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")
# stockfish.get_top_moves(3)

app.config['SECRET_KEY'] = "q2edf4r5t6y7u8i9o0p8fdgh"
app.config['MONGO_URI'] = "mongodb+srv://admin:BwHJZgZP5tyzrQuU@user-db.kia6aok.mongodb.net/?retryWrites=true&w=majority"



@app.route('/')
def hello() :
    data = {
        "moves": "test"
    }
    return jsonify(data)

@app.route('/best-move', methods=['POST'])
def get_best_move():
    request_data = request.get_json()
    print(request_data)
    # eg. request_data = {"board": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "count": 5}

    board = request_data['board']

    stockfish.set_depth(10)  # How deep the AI looks
    stockfish.set_skill_level(10)  # Highest rank stockfish
    stockfish.set_fen_position(board)
    # try and if fails try again
    try:
        best_move = stockfish.get_top_moves(request_data['count'])

        moves = []
        for data in best_move:
            moves.append(data["Move"])
        print(moves)

        response = {
            "best_move": moves
        }
        return jsonify(response)
    except:
        random_move = random.choice(list(chess.Board(board).legal_moves))
        response = {
            "best_move": random_move
        }
        return jsonify(response)

@app.route('/get-opening', methods=['POST'])
def get_oppening():
    request_data = request.get_json()

    username = request_data['username']
    user = users.find_one({'username': username})
    rating = user['rating']

    cnv_rating = convert_rating(rating)
    
    # convert cnv_rating to int
    cnv_rating = int(cnv_rating)

    # get opening
    # moves = opening_moves[:cnv_rating]
    # title = opening_title[:cnv_rating]
    # description = opening_description[:cnv_rating]

    openings = []
    for i in range(cnv_rating):
        opening = {
            "title": opening_title[i],
            "moves": opening_moves[i],
            "description": opening_description[i]
        }
        openings.append(opening)

    response = {
        "openings": openings
    }
    return jsonify(response)

@app.route('/get-puzzle', methods=['POST'])
def get_puzzle() :
    request_data = request.get_json()

    group = request_data['group']
    username = request_data['username']    

    # if 'username' not in session:
    #     return jsonify({'error': 'Unauthorized access'}), 401
    
    # session_username = session['username']

    # if session_username != username:
    #     return jsonify({'error': 'Unauthorized access'}), 401 

    levels = get_levels_by_group(group)

    puzzles = []
    for level in levels:
        puzzles.append(generate_puzzle(level,1))

    data = {
        "puzzles": puzzles
    }

    # Append the new puzzle to the user's puzzle history
    users.update_one(
        {"username": username},
        {"$set": {"puzzle": puzzles}}
    )


    return jsonify(data)

@app.route('/get-centipawn', methods=['POST'])
def get_centipawn():
    request_data = request.get_json()
    board = request_data['board']
    stockfish.set_fen_position(board)
    return stockfish.get_evaluation()["value"]

@app.route('/update-rating', methods=['POST'])
def update_rating():

    data = request.get_json()
    
    username = data['username']

    # if 'username' not in session:
    #     return jsonify({'error': 'Unauthorized access'}), 401
    
    # session_username = session['username']

    # if session_username != username:
    #     return jsonify({'error': 'Unauthorized access'}), 401

    
    user = users.find_one({'username': username})
    
    fen_list = data['fens']
    previous_rating = user['rating']
    player_color = data['player_color']
    player_color = 'white' if player_color == 'w' else 'black'

    rating = adaptive_rating_system(previous_rating, fen_list, player_color)

    rating = round(rating, 2)
    # Update user's rating
    users.update_one({'username': username}, {'$set': {'rating': rating}})
    # Append the new rating to the user's rating history
    users.update_one(
        {"username": username},
        {"$push": {"rating_history": rating}}
    )

    return jsonify({'message': 'Rating updated successfully', 'rating': rating}), 200

@app.route('/get-rating/<username>', methods=['GET'])
def get_rating(username):
    # Check if user exists in the database
    user = users.find_one({'username': username})
    # if not user:
    #     return jsonify({'error': 'User not found'}), 404
    
    rating = user['rating']
    history = user['rating_history']
    return jsonify({'rating': rating, 'history': history}), 200

@app.route('/get-initial-rating', methods=['POST'])
def get_initial_rating():

    data = request.get_json()
    
    username = data['username']
    

    # if 'username' not in session:
    #     return jsonify({'error': 'Unauthorized access'}), 401
    
    # session_username = session['username']

    # if session_username != username:
    #     return jsonify({'error': 'Unauthorized access'}), 401    

    player_fens = data['player_fens']
    # Get centipawn from each fen
    player_centipawns = []
    for fen in player_fens:
        stockfish.set_fen_position(fen)
        player_centipawns.append(stockfish.get_evaluation()["value"])

    user = users.find_one({'username': username})
    puzzles = user['puzzle']

    stockfish_centipawns = []

    for puzzle in puzzles:
        # set the fen to a board
        board = chess.Board(puzzle['fen'])
        # make a move on the board
        board.push_san(puzzle['best_move'])
        # update the board to stockfish
        stockfish.set_fen_position(board.fen())
        # get the centipawn
        centipawn = stockfish.get_evaluation()["value"]

        stockfish_centipawns.append(centipawn)

    rating = initial_rating(player_centipawns, stockfish_centipawns)
    
    rating = round(rating, 2)

    # Update user's rating
    users.update_one({'username': username}, {'$set': {'rating': rating}})


    return jsonify({'message': 'Rating updated successfully', 'rating': rating}), 200