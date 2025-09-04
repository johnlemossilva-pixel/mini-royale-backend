# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serviços e Simulador
import random
from pymongo import MongoClient
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

# Conexão MongoDB (simplificado)
MONGO_URL = "mongodb://localhost:27017/"
DB_NAME = "mini_royale_db"
PLAYERS_COLLECTION = "players"

class MongoDB:
    def __init__(self):
        self.client = MongoClient(MONGO_URL)
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

db_service = MongoDB()

# Simulador de partida
def get_random_player(players):
    return random.choice(players)

def calcular_recompensa(is_winner, rounds_survived):
    base_gems = 10
    if is_winner:
        return base_gems + (rounds_survived * 5)
    else:
        return base_gems + (rounds_survived * 2)

def simulate_match(initial_players):
    active_players = initial_players[:]
    match_log = []
    round_number = 0
    
    players_data = {player['id']: {'rounds_survived': 0} for player in initial_players}

    match_log.append(f"A partida começou com {len(active_players)} aventureiros!")

    while len(active_players) > 1:
        round_number += 1
        match_log.append(f"--- Rodada {round_number} ---")
        
        if round_number % 3 == 0 and len(active_players) > 2:
            eliminated_player = active_players.pop(0)
            players_data[eliminated_player['id']]['rounds_survived'] = round_number
            match_log.append(f"A zona encolheu e {eliminated_player['nome']} foi eliminado!")

        if len(active_players) > 1:
            attacker = get_random_player(active_players)
            defenders = [p for p in active_players if p['nome'] != attacker['nome']]
            defender = get_random_player(defenders)

            match_log.append(f"{attacker['nome']} ataca {defender['nome']}!")
            defender['vida'] -= 10
            
            if defender['vida'] <= 0:
                players_data[defender['id']]['rounds_survived'] = round_number
                active_players = [p for p in active_players if p['nome'] != defender['nome']]
                match_log.append(f"{defender['nome']} foi derrotado por {attacker['nome']}!")

    winner = active_players[0] if active_players else None
    
    if winner:
        players_data[winner['id']]['rounds_survived'] = round_number
        players_data[winner['id']]['is_winner'] = True
        match_log.append(f"O vencedor é {winner['nome']}!")
    else:
        match_log.append("A partida terminou em um empate!")

    final_result = {
        "winner": winner,
        "log": match_log,
        "rounds": round_number,
        "players_rewards": {}
    }

    for player_id, data in players_data.items():
        is_winner = data.get('is_winner', False)
        rewards = calcular_recompensa(is_winner, data['rounds_survived'])
        final_result['players_rewards'][player_id] = rewards
        
    return final_result

# API Router e endpoints
router = APIRouter()

class PlayerModel(BaseModel):
    id: str
    nome: str
    vida: int = 100

class MatchStart(BaseModel):
    players: List[PlayerModel]
    player_id: str

@router.get("/perfil/{player_id}")
async def get_player_profile(player_id: str):
    player = db_service.get_player_data(player_id)
    if player:
        return player
    raise HTTPException(status_code=404, detail="Jogador não encontrado")

async def get_player_profile(player_id: str):
    player = db_service.get_player_data(player_id)
    if player:
        return player
    raise HTTPException(status_code=404, detail="Player not found")

@router.post("/iniciar-partida")
async def start_match(match: MatchStart):

    players_data = [player.dict() for player in match_data.players]
    match_result = simulate_match(players_data)

    player_gems = match_result['players_rewards'].get(match_data.player_id, 0)
    
    update_result = db_service.update_player_gems(
        player_id=match_data.player_id,
        gems_earned=player_gems
    )
    
    match_result['db_updated'] = update_result
    
    return match_result

# Registrar router na aplicação principal
app.include_router(router)
