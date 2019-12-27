from flask import Flask
from flask import jsonify
from flask import request
from mybackend import Database

app = Flask(__name__)


@app.route('/', methods=['GET'])
def view():
    try:

        startlocation = request.args.get('startlocation')
        timeduration = int(request.args.get('timeduration'))

        db = Database()
        points = db.findTrip(startlocation, timeduration - 1, timeduration + 1, 0, None)

        k = int(request.args.get('k'))
        k = min(k, len(points))
        if k < 0:
            raise Exception('k <= 0 error')
        print(points)
        points = points[:k]
        ans = list()

        for point in points:
            ans.append(point['destination'])

        return jsonify(ans)
    except:
        return jsonify('bad input')


if __name__ == '__main__':
    app.run()
