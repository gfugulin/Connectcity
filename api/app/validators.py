"""
Módulo de validações para a API Conneccity
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
import re

class RouteRequestValidator(BaseModel):
    """Validador para requisições de rota"""
    from_id: str = Field(alias="from", min_length=1, max_length=16)
    to_id: str = Field(alias="to", min_length=1, max_length=16)
    perfil: str = Field(..., pattern="^(padrao|pcd)$")
    chuva: bool = Field(default=False)
    k: int = Field(default=1, ge=1, le=10)
    
    @validator('from_id', 'to_id')
    def validate_node_ids(cls, v):
        """Valida se o ID do nó é válido"""
        if not re.match(r'^[A-Za-z0-9_-]+$', v):
            raise ValueError('ID do nó deve conter apenas letras, números, _ e -')
        return v.upper()
    
    @validator('perfil')
    def validate_profile(cls, v):
        """Valida se o perfil é válido"""
        valid_profiles = ['padrao', 'pcd']
        if v not in valid_profiles:
            raise ValueError(f'Perfil deve ser um dos seguintes: {", ".join(valid_profiles)}')
        return v

class EdgeToFixValidator(BaseModel):
    """Validador para requisições de edge-to-fix"""
    top: int = Field(default=3, ge=1, le=20)
    perfil: str = Field(default="padrao", pattern="^(padrao|pcd)$")
    chuva: bool = Field(default=False)
    
    @validator('perfil')
    def validate_profile(cls, v):
        """Valida se o perfil é válido"""
        valid_profiles = ['padrao', 'pcd']
        if v not in valid_profiles:
            raise ValueError(f'Perfil deve ser um dos seguintes: {", ".join(valid_profiles)}')
        return v

class NodeValidator(BaseModel):
    """Validador para nós do grafo"""
    id: str = Field(..., min_length=1, max_length=16)
    name: str = Field(..., min_length=1, max_length=128)
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    tipo: str = Field(..., pattern="^(metro|onibus|acesso|polo)$")
    
    @validator('id')
    def validate_node_id(cls, v):
        """Valida ID do nó"""
        if not re.match(r'^[A-Za-z0-9_-]+$', v):
            raise ValueError('ID do nó deve conter apenas letras, números, _ e -')
        return v.upper()

class EdgeValidator(BaseModel):
    """Validador para arestas do grafo"""
    from_id: str = Field(alias="from", min_length=1, max_length=16)
    to_id: str = Field(alias="to", min_length=1, max_length=16)
    tempo_min: float = Field(..., gt=0, le=1440)  # Máximo 24 horas
    transferencia: int = Field(..., ge=0, le=1)
    escada: int = Field(..., ge=0, le=1)
    calcada_ruim: int = Field(..., ge=0, le=1)
    risco_alag: int = Field(..., ge=0, le=1)
    modo: str = Field(..., pattern="^(pe|onibus|metro|trem)$")
    
    @validator('from_id', 'to_id')
    def validate_node_ids(cls, v):
        """Valida IDs dos nós"""
        if not re.match(r'^[A-Za-z0-9_-]+$', v):
            raise ValueError('ID do nó deve conter apenas letras, números, _ e -')
        return v.upper()

def validate_graph_data(nodes: List[Dict], edges: List[Dict]) -> Dict[str, List[str]]:
    """
    Valida dados do grafo e retorna erros encontrados
    
    Args:
        nodes: Lista de nós
        edges: Lista de arestas
        
    Returns:
        Dict com lista de erros por categoria
    """
    errors = {
        'nodes': [],
        'edges': [],
        'connectivity': []
    }
    
    # Validar nós
    node_ids = set()
    for i, node in enumerate(nodes):
        try:
            validated_node = NodeValidator(**node)
            if validated_node.id in node_ids:
                errors['nodes'].append(f"Linha {i+1}: ID duplicado '{validated_node.id}'")
            node_ids.add(validated_node.id)
        except Exception as e:
            errors['nodes'].append(f"Linha {i+1}: {str(e)}")
    
    # Validar arestas
    for i, edge in enumerate(edges):
        try:
            validated_edge = EdgeValidator(**edge)
            
            # Verificar se os nós existem
            if validated_edge.from_id not in node_ids:
                errors['edges'].append(f"Linha {i+1}: Nó origem '{validated_edge.from_id}' não encontrado")
            if validated_edge.to_id not in node_ids:
                errors['edges'].append(f"Linha {i+1}: Nó destino '{validated_edge.to_id}' não encontrado")
                
        except Exception as e:
            errors['edges'].append(f"Linha {i+1}: {str(e)}")
    
    # Verificar conectividade básica
    if not node_ids:
        errors['connectivity'].append("Nenhum nó válido encontrado")
    elif len(node_ids) < 2:
        errors['connectivity'].append("Grafo deve ter pelo menos 2 nós")
    
    return errors

def validate_route_request(from_id: str, to_id: str, perfil: str, chuva: bool, k: int) -> List[str]:
    """
    Valida requisição de rota
    
    Returns:
        Lista de erros encontrados
    """
    errors = []
    
    try:
        request_data = {
            "from": from_id,
            "to": to_id,
            "perfil": perfil,
            "chuva": chuva,
            "k": k
        }
        RouteRequestValidator(**request_data)
    except Exception as e:
        errors.append(str(e))
    
    return errors

def validate_edge_to_fix_request(top: int, perfil: str, chuva: bool) -> List[str]:
    """
    Valida requisição de edge-to-fix
    
    Returns:
        Lista de erros encontrados
    """
    errors = []
    
    try:
        request_data = {
            "top": top,
            "perfil": perfil,
            "chuva": chuva
        }
        EdgeToFixValidator(**request_data)
    except Exception as e:
        errors.append(str(e))
    
    return errors
