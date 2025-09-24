from pydantic import BaseModel, Field
from typing import List, Literal

Perfil = Literal["padrao", "pcd"]

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
