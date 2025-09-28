"""
API para gerenciamento de dados de São Paulo
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Dict, List, Any, Optional
import logging
import asyncio
from pathlib import Path

from integration.sp_data_collector import SPDataCollector
from .exceptions import ConneccityException, CoreLibraryException

logger = logging.getLogger(__name__)

# Router para dados de São Paulo
sp_data_router = APIRouter(prefix="/sp-data", tags=["São Paulo Data"])

# Instância global do coletor
sp_collector = SPDataCollector()

@sp_data_router.get("/status")
async def get_data_status():
    """Retorna status dos dados de São Paulo"""
    try:
        summary = await sp_collector.get_data_summary()
        return {
            "status": "ok",
            "data_summary": summary,
            "timestamp": summary.get('last_updates', {})
        }
    except Exception as e:
        logger.error(f"Erro ao obter status: {str(e)}")
        raise CoreLibraryException(f"Erro ao obter status: {str(e)}")

@sp_data_router.post("/collect")
async def collect_sp_data(background_tasks: BackgroundTasks):
    """Inicia coleta de dados de São Paulo"""
    try:
        # Executar coleta em background
        background_tasks.add_task(_collect_data_background)
        
        return {
            "message": "Coleta de dados iniciada em background",
            "status": "started"
        }
    except Exception as e:
        logger.error(f"Erro ao iniciar coleta: {str(e)}")
        raise CoreLibraryException(f"Erro ao iniciar coleta: {str(e)}")

@sp_data_router.get("/collect/sync")
async def collect_sp_data_sync():
    """Coleta dados de São Paulo de forma síncrona"""
    try:
        logger.info("Iniciando coleta síncrona de dados...")
        
        results = await sp_collector.collect_all_data()
        
        return {
            "status": "completed",
            "results": results,
            "statistics": results.get('statistics', {}),
            "duration_seconds": results.get('duration_seconds', 0)
        }
    except Exception as e:
        logger.error(f"Erro na coleta síncrona: {str(e)}")
        raise CoreLibraryException(f"Erro na coleta: {str(e)}")

@sp_data_router.get("/gtfs/sources")
async def get_gtfs_sources():
    """Retorna fontes GTFS configuradas"""
    try:
        return {
            "sources": sp_collector.config.gtfs_sources,
            "update_intervals": sp_collector.config.update_intervals,
            "cache_ttl": sp_collector.config.cache_ttl
        }
    except Exception as e:
        logger.error(f"Erro ao obter fontes GTFS: {str(e)}")
        raise CoreLibraryException(f"Erro ao obter fontes: {str(e)}")

@sp_data_router.get("/osm/areas")
async def get_osm_areas():
    """Retorna áreas OSM configuradas"""
    try:
        return {
            "areas": sp_collector.config.osm_areas,
            "update_intervals": sp_collector.config.update_intervals,
            "cache_ttl": sp_collector.config.cache_ttl
        }
    except Exception as e:
        logger.error(f"Erro ao obter áreas OSM: {str(e)}")
        raise CoreLibraryException(f"Erro ao obter áreas: {str(e)}")

@sp_data_router.post("/config/update")
async def update_config(new_config: Dict[str, Any]):
    """Atualiza configuração de dados"""
    try:
        await sp_collector.update_config(new_config)
        
        return {
            "message": "Configuração atualizada com sucesso",
            "new_config": new_config
        }
    except Exception as e:
        logger.error(f"Erro ao atualizar configuração: {str(e)}")
        raise CoreLibraryException(f"Erro ao atualizar configuração: {str(e)}")

@sp_data_router.post("/cache/clear")
async def clear_cache():
    """Limpa cache de dados"""
    try:
        await sp_collector.clear_cache()
        
        return {
            "message": "Cache limpo com sucesso",
            "timestamp": "now"
        }
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {str(e)}")
        raise CoreLibraryException(f"Erro ao limpar cache: {str(e)}")

@sp_data_router.get("/cache/status")
async def get_cache_status():
    """Retorna status do cache"""
    try:
        summary = await sp_collector.get_data_summary()
        
        return {
            "cache_status": summary.get('cache_status', {}),
            "last_updates": summary.get('last_updates', {}),
            "data_counts": summary.get('data_counts', {})
        }
    except Exception as e:
        logger.error(f"Erro ao obter status do cache: {str(e)}")
        raise CoreLibraryException(f"Erro ao obter status: {str(e)}")

@sp_data_router.get("/test/connection")
async def test_connection():
    """Testa conexão com fontes de dados"""
    try:
        results = {}
        
        # Testar conexão GTFS
        for source_name, url in sp_collector.config.gtfs_sources.items():
            try:
                # Teste simples de conectividade
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.head(url, timeout=10) as response:
                        results[source_name] = {
                            "status": "ok" if response.status == 200 else "error",
                            "status_code": response.status,
                            "url": url
                        }
            except Exception as e:
                results[source_name] = {
                    "status": "error",
                    "error": str(e),
                    "url": url
                }
        
        # Testar conexão OSM
        try:
            import aiohttp
            overpass_url = "http://overpass-api.de/api/interpreter"
            async with aiohttp.ClientSession() as session:
                async with session.head(overpass_url, timeout=10) as response:
                    results["osm_overpass"] = {
                        "status": "ok" if response.status == 200 else "error",
                        "status_code": response.status,
                        "url": overpass_url
                    }
        except Exception as e:
            results["osm_overpass"] = {
                "status": "error",
                "error": str(e),
                "url": overpass_url
            }
        
        return {
            "connection_tests": results,
            "timestamp": "now"
        }
    except Exception as e:
        logger.error(f"Erro no teste de conexão: {str(e)}")
        raise CoreLibraryException(f"Erro no teste: {str(e)}")

@sp_data_router.get("/validate")
async def validate_data():
    """Valida dados coletados"""
    try:
        # Verificar se há dados no cache
        summary = await sp_collector.get_data_summary()
        cache_status = summary.get('cache_status', {})
        
        validation_results = {
            "cache_validation": {},
            "data_quality": {},
            "recommendations": []
        }
        
        # Validar cache
        for cache_key, is_valid in cache_status.items():
            validation_results["cache_validation"][cache_key] = {
                "is_valid": is_valid,
                "last_update": summary.get('last_updates', {}).get(cache_key, "unknown")
            }
        
        # Verificar qualidade dos dados
        data_counts = summary.get('data_counts', {})
        for key, count in data_counts.items():
            if count > 0:
                validation_results["data_quality"][key] = "good"
            else:
                validation_results["data_quality"][key] = "empty"
                validation_results["recommendations"].append(f"Coletar dados para {key}")
        
        # Recomendações gerais
        if not any(cache_status.values()):
            validation_results["recommendations"].append("Executar coleta de dados")
        
        if len([k for k, v in cache_status.items() if v]) < 3:
            validation_results["recommendations"].append("Verificar configuração de cache")
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Erro na validação: {str(e)}")
        raise CoreLibraryException(f"Erro na validação: {str(e)}")

async def _collect_data_background():
    """Função para coleta em background"""
    try:
        logger.info("Iniciando coleta em background...")
        results = await sp_collector.collect_all_data()
        logger.info(f"Coleta em background concluída: {results.get('statistics', {})}")
    except Exception as e:
        logger.error(f"Erro na coleta em background: {str(e)}")

