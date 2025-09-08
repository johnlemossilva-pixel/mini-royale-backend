from fastapi import APIRouter, HTTPException, Depends
from pymongo import UpdateOne
from pymongo.errors import OperationFailure
from database import get_db, MongoDB
from models import PlayerModel, MatchStart, PlayerUpdate
import random

router = APIRouter()

def simulate_match(players: list):
    results = {}
    for player in players:
        try:
            player_id = str(player["_id"])
            current_vida = int(player["vida"])  # Converte para int
            
            dano = random.randint(5, 20)
            gems_ganhas = random.randint(1, 10)
            
            nova_vida = max(current_vida - dano, 0)
            
            results[player_id] = {
                "dano_sofrido": dano,
                "vida_restante": nova_vida,
                "gems_ganhas": gems_ganhas
            }
        except (KeyError, TypeError, ValueError):
            # Ignora jogador mal formatado ou dados inválidos
            continue
    return results

@router.get("/perfil/{player_id}", response_model=PlayerModel)
async def get_player_profile(player_id: str, db: MongoDB = Depends(get_db)):
    try:
        player = db.players_collection.find_one({"_id": player_id})
        if player:
            return player
        raise HTTPException(status_code=404, detail="Jogador não encontrado")
    except OperationFailure:
        raise HTTPException(status_code=500, detail="Erro ao acessar o banco de dados. Tente novamente.")

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
        except OperationFailure:
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
    
    res = db.players_collection.update_one({"_id": player_id}, update_doc)
    if res.modified_count:
        return {"detail": "Dados do jogador atualizados com sucesso."}
    
    raise HTTPException(status_code=404, detail="Jogador não encontrado.")

