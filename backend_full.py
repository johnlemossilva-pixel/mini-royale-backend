from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import random
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = FastAPI()

origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conexão MongoDB
MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://johnlemossilva_db_user:BChX9sxgXSXErMTS@cluster0.knt4teh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = "mini_royale_db"
PLAYERS_COLLECTION = "players"

class MongoDB:
    def __init__(self):
        self.client = MongoClient(MONGO_URL, tls=True, tlsAllowInvalidCertificates=True)
        self.db = self.client[DB_NAME]
        self.players_collection = self.db[PLAYERS_COLLECTION]
        print("Conexão com o MongoDB estabelecida.")

    def update_player_gems(self, player_id: str, gems_earned: int):
        result = self.players_collection.update_one(
            {"_id": player_id},
            {"$inc": {"gems": gems_earned}},
            upsert=True
        )
        return result.modified_count

    def get_player_data(self, player_id: str):
        player = self.players_collection.find_one({"_id": player_id})
        if player:
            player["_id"] = str(player["_id"])
        return player
    
    # Novo método para testar a consulta diretamente
    def test_query(self, player_id: str):
        return self.players_collection.find_one({"_id": player_id})

db_service = MongoDB()

router = APIRouter()

class PlayerModel(BaseModel):
    id: str
    nome: str
    vida: int = 100

class MatchStart(BaseModel):
    players: List[PlayerModel]
    player_id: str

def simulate_match(players: List[dict]):
    players_rewards = {}
    for player in players:
        players_rewards[player["id"]] = random.randint(1, 10)
    return {"players_rewards": players_rewards}

@router.get("/perfil/{player_id}")
async def get_player_profile(player_id: str):
    try:
        player = db_service.get_player_data(player_id)
        if player:
            return player
        raise HTTPException(status_code=404, detail="Jogador não encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/test-query/{player_id}")
async def test_query_player(player_id: str):
    try:
        player = db_service.test_query(player_id)
        if player:
            player["_id"] = str(player["_id"])
            return player
        else:
            return {"detail": "Jogador não encontrado no teste direto"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no teste direto: {str(e)}")

@router.post("/iniciar-partida")
async def start_match(match: MatchStart):
    players_data = [player.model_dump() for player in match.players]
    
    match_result = simulate_match(players_data)
    player_gems = match_result["players_rewards"].get(match.player_id, 0)
    update_result = db_service.update_player_gems(
        player_id=match.player_id,
        gems_earned=player_gems
    )
    match_result["db_updated"] = update_result

    return match_result

app.include_router(router)
