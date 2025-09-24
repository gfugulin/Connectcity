"""
Módulo de exceções customizadas para a API Conneccity
"""
from fastapi import HTTPException
from typing import Optional, Dict, Any

class ConneccityException(Exception):
    """Exceção base para o Conneccity"""
    def __init__(self, message: str, error_code: str = "CONNECCITY_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class GraphLoadException(ConneccityException):
    """Exceção para erros de carregamento do grafo"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "GRAPH_LOAD_ERROR", details)

class NodeNotFoundException(ConneccityException):
    """Exceção para nó não encontrado"""
    def __init__(self, node_id: str):
        super().__init__(f"Nó '{node_id}' não encontrado", "NODE_NOT_FOUND", {"node_id": node_id})

class RouteNotFoundException(ConneccityException):
    """Exceção para rota não encontrada"""
    def __init__(self, from_id: str, to_id: str):
        super().__init__(
            f"Nenhuma rota encontrada de '{from_id}' para '{to_id}'", 
            "ROUTE_NOT_FOUND", 
            {"from": from_id, "to": to_id}
        )

class InvalidProfileException(ConneccityException):
    """Exceção para perfil inválido"""
    def __init__(self, profile: str):
        super().__init__(
            f"Perfil '{profile}' inválido", 
            "INVALID_PROFILE", 
            {"profile": profile, "valid_profiles": ["padrao", "pcd"]}
        )

class ValidationException(ConneccityException):
    """Exceção para erros de validação"""
    def __init__(self, message: str, validation_errors: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", validation_errors or {})

class CoreLibraryException(ConneccityException):
    """Exceção para erros da biblioteca C"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CORE_LIBRARY_ERROR", details)

def handle_conneccity_exception(exc: ConneccityException) -> HTTPException:
    """
    Converte exceção Conneccity para HTTPException
    
    Args:
        exc: Exceção Conneccity
        
    Returns:
        HTTPException apropriada
    """
    status_code_map = {
        "GRAPH_LOAD_ERROR": 500,
        "NODE_NOT_FOUND": 404,
        "ROUTE_NOT_FOUND": 422,
        "INVALID_PROFILE": 400,
        "VALIDATION_ERROR": 400,
        "CORE_LIBRARY_ERROR": 500,
        "CONNECCITY_ERROR": 500
    }
    
    status_code = status_code_map.get(exc.error_code, 500)
    
    return HTTPException(
        status_code=status_code,
        detail={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )

def create_error_response(error_code: str, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Cria resposta de erro padronizada
    
    Args:
        error_code: Código do erro
        message: Mensagem do erro
        details: Detalhes adicionais
        
    Returns:
        Dict com resposta de erro
    """
    return {
        "error": True,
        "error_code": error_code,
        "message": message,
        "details": details or {},
        "timestamp": None  # Será preenchido pelo middleware
    }
