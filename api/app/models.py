from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime

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
    modes: List[str] = []  # Modos de transporte usados na rota (ex: ['onibus', 'pe', 'metro'])


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


# Tipos de barreira que o usuário pode reportar
BarrierType = Literal[
    "escada",
    "calcada_ruim",
    "alagamento",
    "obstaculo",
    "iluminacao_ruim",
    "seguranca",
    "sinalizacao_ruim",
    "outro"
]


class BarrierReport(BaseModel):
    """
    Relato de barreira feito pelo usuário durante ou após uma rota.
    Este modelo é pensado para idosos/PCD, focando em simplicidade.
    """
    # Identificação da rota / contexto
    route_id: Optional[int] = Field(
        default=None,
        description="ID interno da alternativa de rota (se disponível)"
    )
    from_node: Optional[str] = Field(
        default=None,
        description="ID do nó de origem da rota (opcional)"
    )
    to_node: Optional[str] = Field(
        default=None,
        description="ID do nó de destino da rota (opcional)"
    )
    step_index: Optional[int] = Field(
        default=None,
        ge=0,
        description="Índice do passo em que a barreira foi encontrada"
    )
    node_id: Optional[str] = Field(
        default=None,
        description="ID do nó mais próximo da barreira (se conhecido)"
    )

    # Perfil do usuário e tipo de barreira
    profile: Perfil = Field(
        description="Perfil do usuário que está reportando (padrao, idoso, pcd)"
    )
    type: BarrierType = Field(
        description="Tipo principal de barreira percebida"
    )

    # Intensidade e descrição livre
    severity: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Severidade percebida (1=muito leve, 5=muito grave)"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Descrição opcional em linguagem natural da barreira"
    )

    # Localização aproximada (caso disponível)
    lat: Optional[float] = Field(
        default=None,
        description="Latitude aproximada da barreira"
    )
    lon: Optional[float] = Field(
        default=None,
        description="Longitude aproximada da barreira"
    )

    # Metadados
    app_version: Optional[str] = Field(
        default=None,
        description="Versão do aplicativo (para debug futuro)"
    )
    platform: Optional[str] = Field(
        default=None,
        description="Plataforma do usuário (web, android, ios, etc.)"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Momento em que o backend recebeu o relato (UTC)"
    )


class BarrierReportResponse(BaseModel):
    """
    Resposta simplificada ao usuário após reportar uma barreira.
    """
    id: str
    message: str
    stored: bool = True
    created_at: datetime


class Notification(BaseModel):
    """Modelo de notificação"""
    id: str
    type: Literal["info", "warning", "alert", "tip", "maintenance"]
    title: str
    message: str
    priority: int = Field(default=1, ge=1, le=5, description="Prioridade: 1=baixa, 5=crítica")
    created_at: datetime
    expires_at: Optional[datetime] = None
    action_url: Optional[str] = None
    action_label: Optional[str] = None


class NotificationsResponse(BaseModel):
    """Resposta com lista de notificações"""
    notifications: List[Notification]
    unread_count: int
