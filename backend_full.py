import os
from pymongo import MongoClient, UpdateOne
from pymongo.errors import OperationFailure, ConnectionFailure
from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import random

# Carrega variáveis ambiente
load_dotenv()

# Configuração banco
class Settings:
    MONGO_URL = os.getenv("MONGO_URL")
    DB_NAME = os.getenv("DB_NAME", "mini_royale_db")
    PLAYERS_COLLECTION = "players"

settings = Settings()

# MongoDB Client
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

def get_db():
    try:
        if not mongo_db.client:
            mongo_db.connect()
        yield mongo_db
    finally:
        pass

# Pydantic models
class PlayerModel(BaseModel):
    id: str = Field(..., alias="_id")
    nome: str
    vida: int = 100
    gems: int = 0

class MatchStart(BaseModel):
    players: List[PlayerModel]
    player_id: str

class PlayerUpdate(BaseModel):
    vida: Optional[int] = None
    gems: Optional[int] = None

# FastAPI app e roteador
app = FastAPI()

origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()

def simulate_match(players: list):
    results = {}
    for player in players:
        try:
            player_id = str(player["_id"])
            current_vida = int(player["vida"])

            dano = random.randint(5, 20)
            gems_ganhas = random.randint(1, 10)

            nova_vida = max(current_vida - dano, 0)

            results[player_id] = {
                "dano_sofrido": dano,
                "vida_restante": nova_vida,
                "gems_ganhas": gems_ganhas
            }
        except (KeyError, TypeError, ValueError):
            continue
    return results

@router.get("/perfil/{player_id}", response_model=PlayerModel)
async def get_player_profile(player_id: str, db: MongoDB = Depends(get_db)):
    try:
        player = db.players_collection.find_one({"_id": player_id})
        if player:
            return player
        raise HTTPException(status_code=404, detail="Jogador não encontrado")
    except (OperationFailure, ConnectionFailure):
        raise HTTPException(status_code=500, detail="Erro interno ao acessar o banco de dados.")

@router.post("/match/start")
async def start_match(match_ MatchStart, db: MongoDB = Depends(get_db)):
    player_ids = [player.id for player in match_data.players]
    players_data = list(db.players_collection.find({"_id": {"$in": player_ids}}))
    if len(players_data) != len(player_ids):
        raise HTTPException(status_code=400, detail="Um ou mais jogadores não foram encontrados.")
    results = simulate_match(players_data)
    updates = [
        UpdateOne(
            {"_id": player_id},
            {"$set": {"vida": result["vida_restante"]}, "$inc": {"gems": result["gems_ganhas"]}}
        ) for player_id, result in results.items()
    ]
    if updates:
        try:
            db.players_collection.bulk_write(updates)
        except (OperationFailure, ConnectionFailure):
            raise HTTPException(status_code=500, detail="Erro ao atualizar dados no banco de dados.")
    return {"status": "match_ended", "results": results}

@router.patch("/perfil/{player_id}")
async def update_player(player_id: str,  PlayerUpdate, db: MongoDB = Depends(get_db)):
    update_doc = {"$inc": {}}
    if data.vida is not None:
        update_doc["$inc"]["vida"] = data.vida
    if data.gems is not None:
        update_doc["$inc"]["gems"] = data.gems
    if not update_doc["$inc"]:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar foi fornecido.")
    try:
        res = db.players_collection.update_one({"_id": player_id}, update_doc)
        if res.modified_count:
            return {"detail": "Dados do jogador atualizados com sucesso."}
    except (OperationFailure, ConnectionFailure):
        raise HTTPException(status_code=500, detail="Erro ao atualizar dados no banco de dados.")
    raise HTTPException(status_code=404, detail="Jogador não encontrado.")

# Incluindo roteador no app
app.include_router(router, prefix="/api/v1")
