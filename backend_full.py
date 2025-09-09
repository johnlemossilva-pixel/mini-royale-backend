import os
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from pymongo import MongoClient, UpdateOne
from pymongo.errors import OperationFailure, ConnectionFailure
from dotenv import load_dotenv
import random

load_dotenv()

class Settings:
    MONGO_URL = os.getenv("MONGO_URL")
    DB_NAME = os.getenv("DB_NAME", "mini_royale_db")
    PLAYERS_COLLECTION = "players"

settings = Settings()

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None
        self.players_collection = None

    def connect(self):
        if not self.client:
            self.client = MongoClient(settings.MONGO_URL, tls=True, tlsAllowInvalidCertificates=True)
            self.db = self.client[settings.DB_NAME]
            self.players_collection = self.db[settings.PLAYERS_COLLECTION]

mongo_db = MongoDB()
mongo_db.connect()

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

def simulate_match(players):
    results = {}
    for player in players:
        try:
            player_id = str(player["_id"])
            current_vida = int(player.get("vida", 100))
            dano = random.randint(5, 20)
            gems_ganhas = random.randint(1, 10)
            nova_vida = max(current_vida - dano, 0)
            results[player_id] = {
                "dano_sofrido": dano,
                "vida_restante": nova_vida,
                "gems_ganhas": gems_ganhas,
            }
        except (KeyError, TypeError, ValueError):
            continue
    return results

@app.route("/api/v1/perfil/<player_id>", methods=["GET"])
def get_player_profile(player_id):
    try:
        player = mongo_db.players_collection.find_one({"_id": player_id})
        if player:
            player["_id"] = str(player["_id"])
            return jsonify(player)
        abort(404, description="Jogador não encontrado")
    except (OperationFailure, ConnectionFailure):
        abort(500, description="Erro interno ao acessar o banco de dados.")

@app.route("/api/v1/match/start", methods=["POST"])
def start_match():
    match_data = request.json
    if not match_data or "players" not in match_
        abort(400, description="Dados da partida inválidos")

    player_ids = [p["_id"] for p in match_data["players"]]
    players_data = list(mongo_db.players_collection.find({"_id": {"$in": player_ids}}))

    if len(players_data) != len(player_ids):
        abort(400, description="Um ou mais jogadores não foram encontrados.")

    results = simulate_match(players_data)

    updates = [
        UpdateOne(
            {"_id": player_id},
            {"$set": {"vida": result["vida_restante"]}, "$inc": {"gems": result["gems_ganhas"]}}
        ) for player_id, result in results.items()
    ]

    if updates:
        try:
            mongo_db.players_collection.bulk_write(updates)
        except (OperationFailure, ConnectionFailure):
            abort(500, description="Erro ao atualizar dados no banco de dados.")

    return jsonify({"status": "match_ended", "results": results})

@app.route("/api/v1/perfil/<player_id>", methods=["PATCH"])
def update_player(player_id):
    data = request.json
    if not 
        abort(400, description="Nenhum dado fornecido para atualização")

    update_doc = {"$inc": {}}
    if "vida" in 
        update_doc["$inc"]["vida"] = data["vida"]
    if "gems" in 
        update_doc["$inc"]["gems"] = data["gems"]

    if not update_doc["$inc"]:
        abort(400, description="Nenhum campo para atualizar foi fornecido.")

    try:
        res = mongo_db.players_collection.update_one({"_id": player_id}, update_doc)
        if res.modified_count:
            return jsonify({"detail": "Dados do jogador atualizados com sucesso."})
        else:
            abort(404, description="Jogador não encontrado.")
    except (OperationFailure, ConnectionFailure):
        abort(500, description="Erro ao atualizar dados no banco de dados.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

