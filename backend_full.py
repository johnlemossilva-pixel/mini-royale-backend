from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import players_router

app = FastAPI()

# Configuração do CORS
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui os roteadores
app.include_router(players_router.router, prefix="/api/v1")
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGO_URL: str = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
    DB_NAME: str = os.getenv("DB_NAME", "mini_royale_db")
    PLAYERS_COLLECTION: str = "players"

settings = Settings()
from pymongo import MongoClient
from config import settings

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None
        self.players_collection = None
    
    def connect(self):
        if self.client is None:
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
        if mongo_db.client is None:
            mongo_db.connect()
        yield mongo_db
    finally:
        # A conexão é fechada quando a aplicação é encerrada
        pass

from pydantic import BaseModel, Field
from typing import List, Optional

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError("string required")
        return cls(v)

class PlayerModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId)
    nome: str
    vida: int = 100
    gems: int = 0

class MatchStart(BaseModel):
    players: List[PlayerModel]
    player_id: str

class PlayerUpdate(BaseModel):
    gems_earned: Optional[int] = None
    vida_earned: Optional[int] = None
from fastapi import APIRouter, HTTPException, Depends
from pymongo.errors import OperationFailure
from database import get_db, MongoDB
from schemas import PlayerModel, MatchStart, PlayerUpdate
import random

router = APIRouter()

def simulate_match(players: list):
    """Simula uma partida e calcula os resultados."""
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
async def start_match(match_data: MatchStart, db: MongoDB = Depends(get_db)):
    # Lógica para simular a partida e atualizar os jogadores
    # Isso é apenas um exemplo simplificado
    
    # 1. Obter os dados completos dos jogadores do DB
    player_ids = [player.id for player in match_data.players]
    
    # Validações e lógica de negócio aqui...
    
    # 2. Simular a partida
    players_data = list(db.players_collection.find({"_id": {"$in": player_ids}}))
    if len(players_data) != len(player_ids):
        raise HTTPException(status_code=400, detail="Um ou mais jogadores não foram encontrados.")
    
    results = simulate_match(players_data)
    
    # 3. Atualizar dados no banco de dados
    for player_id, result in results.items():
        db.players_collection.update_one(
            {"_id": player_id},
            {"$set": {"vida": result["vida_restante"]}, "$inc": {"gems": result["gems_ganhas"]}}
        )
    
    return {"status": "match_ended", "results": results}
