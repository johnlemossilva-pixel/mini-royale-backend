from fastapi import APIRouter, HTTPException, Depends
from pymongo import UpdateOne
from pymongo.errors import OperationFailure, ConnectionFailure
from database import get_db, MongoDB
from models import PlayerModel, MatchStart, PlayerUpdate
import random

router = APIRouter()

def simulate_match(players: list):
    """Simula uma partida e calcula os resultados para cada jogador."""
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
            # Ignora o jogador se os dados estiverem mal formatados ou ausentes
            continue
    return results

@router.get("/perfil/{player_id}", response_model=PlayerModel)
async def get_player_profile(player_id: str, db: MongoDB = Depends(get_db)):
    """Busca o perfil de um jogador pelo ID."""
    try:
        player = db.players_collection.find_one({"_id": player_id})
        if player:
            return player
        raise HTTPException(status_code=404, detail="Jogador não encontrado")
    except (OperationFailure, ConnectionFailure):
        raise HTTPException(status_code=500, detail="Erro interno ao acessar o banco de dados.")

@router.post("/match/start")
async def start_match(match_data: MatchStart, db: MongoDB = Depends(get_db)):
    """Inicia uma partida, simula os resultados e atualiza os jogadores."""
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
async def update_player(player_id: str, data: PlayerUpdate, db: MongoDB = Depends(get_db)):
    """Atualiza a vida ou as gems de um jogador."""
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
