"""
API endpoints para integração com Olho Vivo (SPTrans)
Fornece dados em tempo real de transporte público
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import logging
import os

from integration.olho_vivo_client import OlhoVivoClient

logger = logging.getLogger(__name__)

# Router para Olho Vivo
olho_vivo_router = APIRouter(prefix="/olho-vivo", tags=["Olho Vivo - Tempo Real"])

# Token da API Olho Vivo (deve estar em variável de ambiente ou config)
OLHO_VIVO_TOKEN = os.getenv(
    "OLHO_VIVO_TOKEN",
    "1abf7ba19b22829e9d95648f8affe9afaf8c64b9cbb8c8042e6b50cb5d63be81"
)

# Cliente global (singleton)
_olho_vivo_client: Optional[OlhoVivoClient] = None

def get_olho_vivo_client() -> OlhoVivoClient:
    """Obtém instância do cliente Olho Vivo"""
    global _olho_vivo_client
    if _olho_vivo_client is None:
        _olho_vivo_client = OlhoVivoClient(OLHO_VIVO_TOKEN)
        # Autenticar na inicialização
        if not _olho_vivo_client.authenticate():
            logger.warning("⚠️ Falha na autenticação inicial do Olho Vivo")
    return _olho_vivo_client

@olho_vivo_router.get("/linhas/buscar")
async def buscar_linhas(termos: str = Query(..., description="Termo de busca (número ou nome da linha)")):
    """Busca linhas de ônibus"""
    try:
        client = get_olho_vivo_client()
        linhas = client.buscar_linhas(termos)
        return {
            "linhas": linhas,
            "total": len(linhas)
        }
    except Exception as e:
        logger.error(f"Erro ao buscar linhas: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar linhas: {str(e)}")

@olho_vivo_router.get("/paradas/buscar")
async def buscar_paradas(termos: str = Query(..., description="Termo de busca (nome ou código da parada)")):
    """Busca paradas de ônibus"""
    try:
        client = get_olho_vivo_client()
        paradas = client.buscar_paradas(termos)
        return {
            "paradas": paradas,
            "total": len(paradas)
        }
    except Exception as e:
        logger.error(f"Erro ao buscar paradas: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar paradas: {str(e)}")

@olho_vivo_router.get("/paradas/por-linha/{codigo_linha}")
async def buscar_paradas_por_linha(codigo_linha: int):
    """Busca paradas atendidas por uma linha"""
    try:
        client = get_olho_vivo_client()
        paradas = client.buscar_paradas_por_linha(codigo_linha)
        return {
            "paradas": paradas,
            "codigo_linha": codigo_linha,
            "total": len(paradas)
        }
    except Exception as e:
        logger.error(f"Erro ao buscar paradas por linha: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar paradas: {str(e)}")

@olho_vivo_router.get("/posicao")
async def obter_posicao_veiculos(codigo_linha: Optional[int] = Query(None, description="Código da linha (opcional)")):
    """Obtém posição dos veículos em tempo real"""
    try:
        client = get_olho_vivo_client()
        posicoes = client.obter_posicao_veiculos(codigo_linha)
        return posicoes
    except Exception as e:
        logger.error(f"Erro ao obter posição dos veículos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter posição: {str(e)}")

@olho_vivo_router.get("/previsao")
async def obter_previsao_chegada(
    codigo_parada: int = Query(..., description="Código da parada"),
    codigo_linha: Optional[int] = Query(None, description="Código da linha (opcional)")
):
    """Obtém previsão de chegada dos veículos"""
    try:
        client = get_olho_vivo_client()
        previsao = client.obter_previsao_chegada(codigo_parada, codigo_linha)
        return previsao
    except Exception as e:
        logger.error(f"Erro ao obter previsão: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter previsão: {str(e)}")

@olho_vivo_router.get("/previsao/parada/{codigo_parada}")
async def obter_previsao_por_parada(codigo_parada: int):
    """Obtém previsão de chegada para todas as linhas de uma parada"""
    try:
        client = get_olho_vivo_client()
        previsao = client.obter_previsao_chegada(codigo_parada, None)
        return previsao
    except Exception as e:
        logger.error(f"Erro ao obter previsão por parada: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter previsão: {str(e)}")

@olho_vivo_router.get("/corredores")
async def obter_corredores():
    """Obtém lista de corredores"""
    try:
        client = get_olho_vivo_client()
        corredores = client.obter_corredores()
        return {
            "corredores": corredores,
            "total": len(corredores)
        }
    except Exception as e:
        logger.error(f"Erro ao obter corredores: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter corredores: {str(e)}")

@olho_vivo_router.get("/empresas")
async def obter_empresas():
    """Obtém lista de empresas operadoras"""
    try:
        client = get_olho_vivo_client()
        empresas = client.obter_empresas()
        return {
            "empresas": empresas,
            "total": len(empresas)
        }
    except Exception as e:
        logger.error(f"Erro ao obter empresas: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter empresas: {str(e)}")

