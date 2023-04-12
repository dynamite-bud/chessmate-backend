from flask import Flask, session
from flask import jsonify, request
from pymongo import MongoClient
from flask import Blueprint
from werkzeug.security import generate_password_hash, check_password_hash


auth_app = Blueprint('auth', __name__)

# MongoDB setup
client = MongoClient('mongodb+srv://admin:BwHJZgZP5tyzrQuU@user-db.kia6aok.mongodb.net/?retryWrites=true&w=majority')
db = client['users']
users = db['users']

@auth_app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    # Check if user exists in the database
    user = users.find_one({'username': username})
    if not user:
        return jsonify({'error': 'Invalid username or password'}), 401

    # Check if password is correct
    if not check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid username or password'}), 401

    # Login user and create session
    session['username'] = username
    return jsonify({'message': 'Logged in successfully'}), 200

@auth_app.route('/logout')
def logout():
    session.pop('username', None)
    return jsonify({'message': 'Logged out successfully'}), 200

# Endpoint for user registration
@auth_app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']

    # Check if username already exists
    if users.find_one({'username': username}):
        return jsonify({'error': 'Username already taken'}), 400

    hashed_password = generate_password_hash(password)

    # Insert new user to database
    users.insert_one({'username': username, 'password': hashed_password})
    return jsonify({'message': 'User registered successfully'}), 201
