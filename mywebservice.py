from flask import Flask
from flask import jsonify
from flask import request
from mybackend import Database

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def view():
    db = Database()
    points = db.get_start_points()
    return jsonify(points)