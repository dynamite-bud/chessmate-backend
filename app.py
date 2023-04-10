from flask import Flask
from flask import jsonify

app = Flask(__name__)

@app.route('/')
def hello() :
    data = {
        "moves": "test"
    }
    return jsonify(data)