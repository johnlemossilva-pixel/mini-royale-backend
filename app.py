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

@app.route('/api/v1/perfil', methods=['POST'])
def create_player():
    data = request.json
    # Valide os campos obrigatórios (exemplo simplificado)
    if not data or "_id" not in data or "nome" not in data or "vida" not in data or "gems" not in 
        return jsonify({"error": "Campos obrigatórios faltando"}), 400
    mongo_db.players_collection.insert_one(data)
    return jsonify({"message": "Jogador criado com sucesso!"}), 201

@app.route('/api/v1/perfil/<player_id>', methods=['PUT'])
def update_player(player_id):
    data = request.json
    # Atualiza apenas os campos enviados na requisição
    result = mongo_db.players_collection.update_one(
        {"_id": player_id},
        {"$set": data}
    )
    if result.matched_count:
        return jsonify({"message": "Jogador atualizado!"}), 200
    else:
        return jsonify({"error": "Jogador não encontrado."}), 404

if __name__ == '__main__':
    mongo_db.connect()
    app.run(host='0.0.0.0', port=8000)

