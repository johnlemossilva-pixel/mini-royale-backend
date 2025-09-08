from fastapi import APIRouter, HTTPException, Depends, Body
from database import get_db, MongoDB
from models import PlayerModel, MatchStart
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
    player = db.players_collection.find_one({"_id": player_id})
    if player:
        return player
    raise HTTPException(status_code=404, detail="Jogador não encontrado")

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
