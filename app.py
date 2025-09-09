from flask import Flask, jsonify, request
from database import mongo_db

app = Flask(__name__)

@app.route('/api/v1/perfil/<player_id>', methods=['GET'])
def get_player_profile(player_id):
    player = mongo_db.players_collection.find_one({"_id": player_id}, {"_id": 0})
    if player:
        return jsonify(player)
    else:
        return jsonify({"error": "Player not found"}), 404

@app.route('/api/v1/match/start', methods=['POST'])
def start_match():
    data = request.json
    return jsonify({"message": "Match started", "data": data})

if __name__ == '__main__':
    mongo_db.connect()
    app.run(host='0.0.0.0', port=8000)
