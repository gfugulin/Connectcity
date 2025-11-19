from pydantic import BaseModel, Field
from typing import List, Literal, Optional

Perfil = Literal["padrao", "idoso", "pcd"]

class RouteRequest(BaseModel):
    from_id: str = Field(alias="from")
    to_id: str = Field(alias="to")
    perfil: Perfil
    chuva: bool = False
    k: int = 1

class Alt(BaseModel):
    id: int
    tempo_total_min: float
    transferencias: int
    path: List[str]
    barreiras_evitas: List[str] = []

class AlternativesResponse(BaseModel):
    alternatives: List[Alt]

class RouteDetailsRequest(BaseModel):
    from_id: Optional[str] = Field(None, alias="from")
    to_id: Optional[str] = Field(None, alias="to")
    path: Optional[List[str]] = None
    perfil: Perfil
    chuva: bool = False
    
    class Config:
        # Permite usar 'from' e 'to' como campos
        populate_by_name = True
