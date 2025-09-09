from flask import Flask, jsonify, request
from database import mongo_db

app = Flask(__name__)

# Rota para obter o perfil de um jogador
@app.route('/api/v1/perfil/<player_id>', methods=['GET'])
def get_player_profile(player_id):
    """
    Retorna o perfil de um jogador com base no ID.
    """
    player = mongo_db.players_collection.find_one({"_id": player_id}, {"_id": 0})
    if player:
        return jsonify(player)
    else:
        # Retorna 404 se o jogador não for encontrado
        return jsonify({"error": "Player not found"}), 404

# Rota para iniciar uma partida
@app.route('/api/v1/match/start', methods=['POST'])
def start_match():
    """
    Simula o início de uma partida.
    """
    data = request.json
    return jsonify({"message": "Match started", "data": data})

# Rota para criar um novo jogador
@app.route('/api/v1/perfil', methods=['POST'])
def create_player():
    """
    Cria um novo perfil de jogador com validação de dados.
    """
    data = request.json

    # Validação: verifica se todos os campos obrigatórios existem no JSON
    if not all(k in data for k in ["_id", "nome", "vida", "gems"]):
        return jsonify({"error": "Campos obrigatórios faltando"}), 400
    
    # Validação: verifica se 'vida' e 'gems' são números inteiros
    if not isinstance(data.get("vida"), int) or not isinstance(data.get("gems"), int):
        return jsonify({"error": "Os campos 'vida' e 'gems' devem ser números inteiros"}), 400

    # Insere o novo jogador no banco de dados
    try:
        mongo_db.players_collection.insert_one(data)
        return jsonify({"message": "Jogador criado com sucesso!"}), 201
    except Exception as e:
        # Retorna um erro caso a inserção falhe (ex: ID duplicado)
        return jsonify({"error": f"Erro ao criar o jogador: {str(e)}"}), 500

# Rota para atualizar um jogador existente
@app.route('/api/v1/perfil/<player_id>', methods=['PUT'])
def update_player(player_id):
    """
    Atualiza um jogador com base no ID.
    """
    data = request.json
    # Atualiza apenas os campos enviados na requisição
    result = mongo_db.players_collection.update_one(
        {"_id": player_id},
        {"$set": data}
    )
    if result.matched_count:
        return jsonify({"message": "Jogador atualizado!"}), 200
    else:
        # Retorna 404 se o jogador não for encontrado
        return jsonify({"error": "Jogador não encontrado."}), 404

if __name__ == '__main__':
    mongo_db.connect()
    app.run(host='0.0.0.0', port=8000)

