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
    vida: Optional[int] = None
    gems: Optional[int] = None
