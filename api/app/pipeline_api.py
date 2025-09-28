#!/usr/bin/env python3
"""
API endpoints para gerenciamento do pipeline de processamento
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from integration.pipeline_manager import PipelineManager, PipelineConfig, PipelineStatus
from integration.realtime_processor import RealTimeProcessor
from integration.smart_cache import SmartCache
from integration.data_streaming import DataStreamer
from integration.performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)

# Router para pipeline
pipeline_router = APIRouter(prefix="/pipeline", tags=["Pipeline Management"])

# Instância global do pipeline manager
pipeline_manager: Optional[PipelineManager] = None

def get_pipeline_manager() -> PipelineManager:
    """Dependency para obter o pipeline manager"""
    global pipeline_manager
    if pipeline_manager is None:
        # Configuração padrão
        config = PipelineConfig(
            gtfs_interval=300,
            osm_interval=3600,
            integration_interval=1800,
            cache_strategy="adaptive",
            l1_max_size=1000,
            l1_max_memory_mb=100,
            l2_max_size=10000,
            streaming_enabled=True,
            stream_endpoints={
                "gtfs_realtime": "http://localhost:8080/gtfs/realtime",
                "osm_changes": "http://localhost:8080/osm/changes"
            },
            monitoring_interval=30,
            cpu_threshold=80.0,
            memory_threshold=85.0,
            disk_threshold=90.0
        )
        pipeline_manager = PipelineManager(config)
    return pipeline_manager

@pipeline_router.post("/initialize")
async def initialize_pipeline(
    background_tasks: BackgroundTasks,
    manager: PipelineManager = Depends(get_pipeline_manager)
) -> Dict[str, Any]:
    """
    Inicializa o pipeline de processamento
    """
    try:
        logger.info("🔧 Inicializando pipeline...")
        
        # Inicializar em background
        background_tasks.add_task(manager.initialize)
        
        return {
            "message": "Pipeline sendo inicializado em background",
            "status": "initializing",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao inicializar pipeline: {str(e)}")

@pipeline_router.post("/start")
async def start_pipeline(
    background_tasks: BackgroundTasks,
    manager: PipelineManager = Depends(get_pipeline_manager)
) -> Dict[str, Any]:
    """
    Inicia o pipeline de processamento
    """
    try:
        logger.info("🚀 Iniciando pipeline...")
        
        # Iniciar em background
        background_tasks.add_task(manager.start_pipeline)
        
        return {
            "message": "Pipeline sendo iniciado em background",
            "status": "starting",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar pipeline: {str(e)}")

@pipeline_router.post("/stop")
async def stop_pipeline(
    background_tasks: BackgroundTasks,
    manager: PipelineManager = Depends(get_pipeline_manager)
) -> Dict[str, Any]:
    """
    Para o pipeline de processamento
    """
    try:
        logger.info("🛑 Parando pipeline...")
        
        # Parar em background
        background_tasks.add_task(manager.stop_pipeline)
        
        return {
            "message": "Pipeline sendo parado em background",
            "status": "stopping",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao parar pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao parar pipeline: {str(e)}")

@pipeline_router.post("/pause")
async def pause_pipeline(
    background_tasks: BackgroundTasks,
    manager: PipelineManager = Depends(get_pipeline_manager)
) -> Dict[str, Any]:
    """
    Pausa o pipeline de processamento
    """
    try:
        logger.info("⏸️ Pausando pipeline...")
        
        # Pausar em background
        background_tasks.add_task(manager.pause_pipeline)
        
        return {
            "message": "Pipeline sendo pausado em background",
            "status": "pausing",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao pausar pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao pausar pipeline: {str(e)}")

@pipeline_router.post("/resume")
async def resume_pipeline(
    background_tasks: BackgroundTasks,
    manager: PipelineManager = Depends(get_pipeline_manager)
) -> Dict[str, Any]:
    """
    Resume o pipeline de processamento
    """
    try:
        logger.info("▶️ Resumindo pipeline...")
        
        # Resumir em background
        background_tasks.add_task(manager.resume_pipeline)
        
        return {
            "message": "Pipeline sendo resumido em background",
            "status": "resuming",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao resumir pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao resumir pipeline: {str(e)}")

@pipeline_router.post("/restart")
async def restart_pipeline(
    background_tasks: BackgroundTasks,
    manager: PipelineManager = Depends(get_pipeline_manager)
) -> Dict[str, Any]:
    """
    Reinicia o pipeline de processamento
    """
    try:
        logger.info("🔄 Reiniciando pipeline...")
        
        # Reiniciar em background
        background_tasks.add_task(manager.restart_pipeline)
        
        return {
            "message": "Pipeline sendo reiniciado em background",
            "status": "restarting",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao reiniciar pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao reiniciar pipeline: {str(e)}")

@pipeline_router.get("/status")
async def get_pipeline_status(
    manager: PipelineManager = Depends(get_pipeline_manager)
) -> Dict[str, Any]:
    """
    Retorna o status atual do pipeline
    """
    try:
        status = manager.get_status()
        return {
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter status do pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter status: {str(e)}")

@pipeline_router.get("/metrics")
async def get_pipeline_metrics(
    manager: PipelineManager = Depends(get_pipeline_manager)
) -> Dict[str, Any]:
    """
    Retorna métricas do pipeline
    """
    try:
        metrics = manager.get_metrics()
        return {
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter métricas do pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter métricas: {str(e)}")

@pipeline_router.get("/health")
async def get_pipeline_health(
    manager: PipelineManager = Depends(get_pipeline_manager)
) -> Dict[str, Any]:
    """
    Retorna status de saúde do pipeline
    """
    try:
        health = manager.get_health_status()
        return {
            "health": health,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter saúde do pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter saúde: {str(e)}")

# Endpoints para componentes específicos

@pipeline_router.get("/realtime/status")
async def get_realtime_status(
    manager: PipelineManager = Depends(get_pipeline_manager)
) -> Dict[str, Any]:
    """
    Retorna status do processador em tempo real
    """
    try:
        if not manager.realtime_processor:
            raise HTTPException(status_code=404, detail="RealTimeProcessor não inicializado")
        
        metrics = manager.realtime_processor.get_metrics()
        return {
            "realtime_processor": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter status do RealTimeProcessor: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter status: {str(e)}")

@pipeline_router.get("/cache/status")
async def get_cache_status(
    manager: PipelineManager = Depends(get_pipeline_manager)
) -> Dict[str, Any]:
    """
    Retorna status do cache inteligente
    """
    try:
        if not manager.smart_cache:
            raise HTTPException(status_code=404, detail="SmartCache não inicializado")
        
        status = manager.smart_cache.get_status()
        metrics = manager.smart_cache.get_metrics()
        
        return {
            "cache_status": status,
            "cache_metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter status do cache: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter status: {str(e)}")

@pipeline_router.post("/cache/clear")
async def clear_cache(
    background_tasks: BackgroundTasks,
    manager: PipelineManager = Depends(get_pipeline_manager)
) -> Dict[str, Any]:
    """
    Limpa o cache inteligente
    """
    try:
        if not manager.smart_cache:
            raise HTTPException(status_code=404, detail="SmartCache não inicializado")
        
        # Limpar em background
        background_tasks.add_task(manager.smart_cache.clear)
        
        return {
            "message": "Cache sendo limpo em background",
            "status": "clearing",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao limpar cache: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao limpar cache: {str(e)}")

@pipeline_router.get("/streaming/status")
async def get_streaming_status(
    manager: PipelineManager = Depends(get_pipeline_manager)
) -> Dict[str, Any]:
    """
    Retorna status do sistema de streaming
    """
    try:
        if not manager.data_streamer:
            raise HTTPException(status_code=404, detail="DataStreamer não inicializado")
        
        status = manager.data_streamer.get_status()
        metrics = manager.data_streamer.get_metrics()
        
        return {
            "streaming_status": status,
            "streaming_metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter status do streaming: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter status: {str(e)}")

@pipeline_router.get("/performance/status")
async def get_performance_status(
    manager: PipelineManager = Depends(get_pipeline_manager)
) -> Dict[str, Any]:
    """
    Retorna status do monitor de performance
    """
    try:
        if not manager.performance_monitor:
            raise HTTPException(status_code=404, detail="PerformanceMonitor não inicializado")
        
        status = manager.performance_monitor.get_status()
        metrics = manager.performance_monitor.get_current_metrics()
        alerts = manager.performance_monitor.get_active_alerts()
        
        return {
            "performance_status": status,
            "performance_metrics": metrics,
            "active_alerts": alerts,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter status de performance: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter status: {str(e)}")

@pipeline_router.get("/performance/history")
async def get_performance_history(
    hours: int = 1,
    manager: PipelineManager = Depends(get_pipeline_manager)
) -> Dict[str, Any]:
    """
    Retorna histórico de performance
    """
    try:
        if not manager.performance_monitor:
            raise HTTPException(status_code=404, detail="PerformanceMonitor não inicializado")
        
        history = manager.performance_monitor.get_metrics_history(hours)
        
        return {
            "performance_history": history,
            "hours_covered": hours,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter histórico de performance: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter histórico: {str(e)}")

@pipeline_router.post("/export/state")
async def export_pipeline_state(
    file_path: str = "pipeline_state.json",
    manager: PipelineManager = Depends(get_pipeline_manager)
) -> Dict[str, Any]:
    """
    Exporta estado do pipeline para arquivo
    """
    try:
        # Exportar em background
        import asyncio
        asyncio.create_task(manager.export_pipeline_state(file_path))
        
        return {
            "message": f"Estado do pipeline sendo exportado para {file_path}",
            "status": "exporting",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao exportar estado do pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao exportar estado: {str(e)}")

@pipeline_router.get("/config")
async def get_pipeline_config(
    manager: PipelineManager = Depends(get_pipeline_manager)
) -> Dict[str, Any]:
    """
    Retorna configuração atual do pipeline
    """
    try:
        config = {
            "gtfs_interval": manager.config.gtfs_interval,
            "osm_interval": manager.config.osm_interval,
            "integration_interval": manager.config.integration_interval,
            "cache_strategy": manager.config.cache_strategy,
            "l1_max_size": manager.config.l1_max_size,
            "l1_max_memory_mb": manager.config.l1_max_memory_mb,
            "l2_max_size": manager.config.l2_max_size,
            "streaming_enabled": manager.config.streaming_enabled,
            "stream_endpoints": manager.config.stream_endpoints,
            "monitoring_interval": manager.config.monitoring_interval,
            "cpu_threshold": manager.config.cpu_threshold,
            "memory_threshold": manager.config.memory_threshold,
            "disk_threshold": manager.config.disk_threshold
        }
        
        return {
            "config": config,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter configuração do pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter configuração: {str(e)}")


