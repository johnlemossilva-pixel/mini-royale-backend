from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/api/v1/perfil/<player_id>', methods=['GET'])
def get_player_profile(player_id):
    return jsonify({"player_id": player_id, "life": 100, "gems": 50})

@app.route('/api/v1/match/start', methods=['POST'])
def start_match():
    data = request.json
    return jsonify({"message": "Match started", "data": data})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
