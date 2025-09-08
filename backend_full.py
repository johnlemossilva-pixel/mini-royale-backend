from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import players_router

app = FastAPI()

origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(players_router.router, prefix="/api/v1")
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://username:pass@cluster.mongodb.net/?retryWrites=true&w=majority")
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
            print("Conexão com o MongoDB estabelecida.")
    
    def close(self):
        if self.client:
            self.client.close()
            self.client = None
            print("Conexão com o MongoDB fechada.")

mongo_db = MongoDB()

def get_db():
    try:
        if not mongo_db.client:
            mongo_db.connect()
        yield mongo_db
    finally:
        # deixar aberto enquanto rodar o app
        pass
from pydantic import BaseModel, Field
from typing import List, Optional

class PlayerModel(BaseModel):
    id: str = Field(..., alias="_id")
    nome: str
    vida: int = 100
    gems: int = 0

class MatchStart(BaseModel):
    players: List[PlayerModel]
    player_id: str

class PlayerUpdate(BaseModel):
    gems_earned: Optional[int] = None
    vida_earned: Optional[int] = None
from fastapi import APIRouter, HTTPException, Depends, Body
from pymongo.errors import OperationFailure
from database import get_db, MongoDB
from models import PlayerModel, MatchStart
import random

router = APIRouter()

def simulate_match(players: list):
    results = {}
    for player in players:
        dano = random.randint(5, 20)
        gems_ganhas = random.randint(1, 10)
        nova_vida = max(player["vida"] - dano, 0)
        results[str(player["_id"])] = {
            "dano_sofrido": dano,
            "vida_restante": nova_vida,
            "gems_ganhas": gems_ganhas
        }
    return results

@router.get("/perfil/{player_id}", response_model=PlayerModel)
async def get_player_profile(player_id: str, db: MongoDB = Depends(get_db)):
    try:
        player = db.players_collection.find_one({"_id": player_id})
        if player:
            return player
        raise HTTPException(status_code=404, detail="Jogador não encontrado")
    except OperationFailure as e:
        raise HTTPException(status_code=500, detail=f"Erro no banco de dados: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.post("/match/start")
async def start_match(match_ MatchStart, db: MongoDB = Depends(get_db)):
    player_ids = [player.id for player in match_data.players]
    players_data = list(db.players_collection.find({"_id": {"$in": player_ids}}))
    if len(players_data) != len(player_ids):
        raise HTTPException(status_code=400, detail="Um ou mais jogadores não foram encontrados.")
    
    results = simulate_match(players_data)
    for player_id, result in results.items():
        db.players_collection.update_one(
            {"_id": player_id},
            {"$set": {"vida": result["vida_restante"]}, "$inc": {"gems": result["gems_ganhas"]}}
        )
    return {"status": "match_ended", "results": results}

@router.patch("/perfil/{player_id}/vida")
async def update_vida(player_id: str, amount: int = Body(..., embed=True), db: MongoDB = Depends(get_db)):
    res = db.players_collection.update_one({"_id": player_id}, {"$inc": {"vida": amount}})
    if res.modified_count:
        return {"detail": f"Vida atualizada em {amount} para jogador {player_id}"}
    raise HTTPException(status_code=404, detail="Jogador não encontrado")

@router.patch("/perfil/{player_id}/gems")
async def update_gems(player_id: str, amount: int = Body(..., embed=True), db: MongoDB = Depends(get_db)):
    res = db.players_collection.update_one({"_id": player_id}, {"$inc": {"gems": amount}})
    if res.modified_count:
        return {"detail": f"Gems atualizadas em {amount} para jogador {player_id}"}
    raise HTTPException(status_code=404, detail="Jogador não encontrado")
