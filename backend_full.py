import os
import logging
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from pymongo import MongoClient, UpdateOne
from pymongo.errors import OperationFailure, ConnectionFailure
from bson.objectid import ObjectId
from dotenv import load_dotenv
import random

# Configuração do logger
logging.basicConfig(level=logging.INFO)

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
            try:
                # Removido tlsAllowInvalidCertificates=True por razões de segurança
                self.client = MongoClient(settings.MONGO_URL, tls=True)
                self.client.admin.command('ping')  # Verifica a conexão
                self.db = self.client[settings.DB_NAME]
                self.players_collection = self.db[settings.PLAYERS_COLLECTION]
                logging.info("Conexão com o MongoDB estabelecida com sucesso.")
            except ConnectionFailure as e:
                logging.error(f"Não foi possível conectar ao MongoDB: {e}")
                raise

mongo_db = MongoDB()
try:
    mongo_db.connect()
except ConnectionFailure:
    exit() # Encerra se a conexão inicial falhar

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
            logging.warning(f"Dados inválidos para o jogador: {player}")
            continue
    return results

@app.route("/api/v1/perfil/<player_id>", methods=["GET"])
def get_player_profile(player_id):
    try:
        player = mongo_db.players_collection.find_one({"_id": ObjectId(player_id)})
        if player:
            player["_id"] = str(player["_id"])
            return jsonify(player)
        abort(404, description="Jogador não encontrado")
    except (OperationFailure, ConnectionFailure) as e:
        logging.exception("Erro ao acessar o banco de dados:")
        abort(500, description="Erro interno ao acessar o banco de dados.")
    except Exception as e:
        logging.exception("Erro inesperado:")
        abort(500, description="Erro interno.")

@app.route("/api/v1/match/start", methods=["POST"])
def start_match():
    match_data = request.json
    if not match_data or "players" not in match_data:
        abort(400, description="Dados da partida inválidos")

    player_ids = [ObjectId(p["_id"]) for p in match_data["players"]]
    players_data = list(mongo_db.players_collection.find({"_id": {"$in": player_ids}}))

    if len(players_data) != len(player_ids):
        found_ids = [p["_id"] for p in players_data]
        missing_ids = [str(p) for p in player_ids if p not in found_ids]
        logging.warning(f"Jogadores não encontrados: {missing_ids}")
        abort(400, description="Um ou mais jogadores não foram encontrados.")

    results = simulate_match(players_data)

    updates = [
        UpdateOne(
            {"_id": ObjectId(player_id)},
            {"$set": {"vida": result["vida_restante"]}, "$inc": {"gems": result["gems_ganhas"]}}
        ) for player_id, result in results.items()
    ]

    if updates:
        try:
            mongo_db.players_collection.bulk_write(updates)
        except (OperationFailure, ConnectionFailure) as e:
            logging.exception("Erro ao atualizar dados no banco de dados:")
            abort(500, description="Erro ao atualizar dados no banco de dados.")

    return jsonify({"status": "match_ended", "results": results})

@app.route("/api/v1/perfil/<player_id>", methods=["PATCH"])
def update_player(player_id):
    data = request.json
    if not data:
        abort(400, description="Nenhum dado fornecido para atualização")

    update_doc = {"$inc": {}}
    valid_fields = ["vida", "gems"]
    for field in valid_fields:
        if field in data:
            if isinstance(data[field], (int, float)):
                update_doc["$inc"][field] = data[field]
            else:
                logging.warning(f"Tipo inválido para o campo {field}: {type(data[field])}")
                abort(400, description=f"O campo '{field}' deve ser numérico.")

    if not update_doc["$inc"]:
        abort(400, description="Nenhum campo válido para atualizar foi fornecido.")

    try:
        res = mongo_db.players_collection.update_one({"_id": ObjectId(player_id)}, update_doc)
        if res.modified_count:
            return jsonify({"detail": "Dados do jogador atualizados com sucesso."})
        else:
            abort(404, description="Jogador não encontrado.")
    except (OperationFailure, ConnectionFailure) as e:
        logging.exception("Erro ao atualizar dados no banco de dados:")
        abort(500, description="Erro ao atualizar dados no banco de dados.")
    except Exception as e:
        logging.exception("Erro inesperado:")
        abort(500, description="Erro interno.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

