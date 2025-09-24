#!/usr/bin/env python3
"""
Gerenciador do pipeline completo de processamento para Conneccity
"""
import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from .realtime_processor import RealTimeProcessor, DataSource, UpdateType
from .smart_cache import SmartCache, CacheLevel, CacheStrategy
from .data_streaming import DataStreamer, StreamType, StreamConfig
from .performance_monitor import PerformanceMonitor, AlertLevel

logger = logging.getLogger(__name__)

class PipelineStatus(Enum):
    """Status do pipeline"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"

@dataclass
class PipelineConfig:
    """Configuração do pipeline"""
    # RealTimeProcessor
    gtfs_interval: int = 300  # 5 minutos
    osm_interval: int = 3600  # 1 hora
    integration_interval: int = 1800  # 30 minutos
    
    # SmartCache
    cache_strategy: str = "adaptive"
    l1_max_size: int = 1000
    l1_max_memory_mb: int = 100
    l2_max_size: int = 10000
    
    # DataStreaming
    streaming_enabled: bool = True
    stream_endpoints: Dict[str, str] = None
    
    # PerformanceMonitor
    monitoring_interval: int = 30
    cpu_threshold: float = 80.0
    memory_threshold: float = 85.0
    disk_threshold: float = 90.0

class PipelineManager:
    """
    Gerenciador do pipeline completo de processamento
    """
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.status = PipelineStatus.STOPPED
        
        # Componentes do pipeline
        self.realtime_processor: Optional[RealTimeProcessor] = None
        self.smart_cache: Optional[SmartCache] = None
        self.data_streamer: Optional[DataStreamer] = None
        self.performance_monitor: Optional[PerformanceMonitor] = None
        
        # Métricas
        self.metrics = {
            'start_time': None,
            'uptime_seconds': 0,
            'total_processed': 0,
            'errors_count': 0,
            'last_activity': None
        }
        
        # Callbacks
        self.status_callbacks: List[Callable] = []
        self.error_callbacks: List[Callable] = []
        
        logger.info("✅ Pipeline Manager inicializado")
    
    async def initialize(self):
        """Inicializa todos os componentes do pipeline"""
        try:
            logger.info("🔧 Inicializando componentes do pipeline...")
            
            # Configurar RealTimeProcessor
            rt_config = {
                'gtfs_interval': self.config.gtfs_interval,
                'osm_interval': self.config.osm_interval,
                'integration_interval': self.config.integration_interval,
                'min_data_freshness': 3600,
                'max_processing_time': 300,
                'min_cache_hit_rate': 0.8
            }
            self.realtime_processor = RealTimeProcessor(rt_config)
            
            # Configurar SmartCache
            cache_config = {
                'cache_strategy': self.config.cache_strategy,
                'l1_max_size': self.config.l1_max_size,
                'l1_max_memory_mb': self.config.l1_max_memory_mb,
                'l2_max_size': self.config.l2_max_size,
                'l2_cache_path': 'cache/l2',
                'l3_enabled': False,
                'default_ttl': 3600,
                'cleanup_interval': 300,
                'cleanup_threshold': 0.8
            }
            self.smart_cache = SmartCache(cache_config)
            
            # Configurar DataStreamer
            if self.config.streaming_enabled:
                streamer_config = {
                    'max_buffer_size': 10000,
                    'cleanup_interval': 300,
                    'retry_delay': 60
                }
                self.data_streamer = DataStreamer(streamer_config)
                
                # Adicionar streams configurados
                if self.config.stream_endpoints:
                    for stream_name, endpoint in self.config.stream_endpoints.items():
                        stream_type = StreamType(stream_name)
                        stream_config = StreamConfig(
                            stream_type=stream_type,
                            endpoint=endpoint,
                            interval=30,
                            timeout=30,
                            retry_attempts=3
                        )
                        self.data_streamer.add_stream(stream_type, stream_config)
            
            # Configurar PerformanceMonitor
            monitor_config = {
                'monitoring_interval': self.config.monitoring_interval,
                'retention_hours': 24,
                'alert_cooldown': 300,
                'cpu_threshold': self.config.cpu_threshold,
                'memory_threshold': self.config.memory_threshold,
                'disk_threshold': self.config.disk_threshold
            }
            self.performance_monitor = PerformanceMonitor(monitor_config)
            
            # Configurar callbacks
            self._setup_callbacks()
            
            logger.info("✅ Componentes do pipeline inicializados")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar pipeline: {e}")
            raise
    
    def _setup_callbacks(self):
        """Configura callbacks entre componentes"""
        if self.performance_monitor:
            # Callback para alertas de performance
            self.performance_monitor.add_alert_callback(self._handle_performance_alert)
        
        if self.realtime_processor:
            # Callback para atualizações de dados
            self.realtime_processor.subscribe('pipeline_manager', self._handle_data_update)
    
    async def start_pipeline(self):
        """Inicia o pipeline completo"""
        if self.status != PipelineStatus.STOPPED:
            logger.warning(f"⚠️ Pipeline já está {self.status.value}")
            return
        
        try:
            logger.info("🚀 Iniciando pipeline completo...")
            self.status = PipelineStatus.STARTING
            self.metrics['start_time'] = datetime.now()
            
            # Iniciar componentes em paralelo
            tasks = []
            
            if self.realtime_processor:
                tasks.append(self.realtime_processor.start_processing())
            
            if self.data_streamer:
                tasks.append(self.data_streamer.start_streaming())
            
            if self.performance_monitor:
                tasks.append(self.performance_monitor.start_monitoring())
            
            # Aguardar inicialização
            await asyncio.gather(*tasks)
            
            # Iniciar tarefa de métricas
            asyncio.create_task(self._metrics_task())
            
            self.status = PipelineStatus.RUNNING
            logger.info("✅ Pipeline completo iniciado")
            
            # Notificar callbacks
            await self._notify_status_callbacks()
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar pipeline: {e}")
            self.status = PipelineStatus.ERROR
            await self._notify_error_callbacks(e)
            raise
    
    async def stop_pipeline(self):
        """Para o pipeline completo"""
        if self.status not in [PipelineStatus.RUNNING, PipelineStatus.PAUSED]:
            logger.warning(f"⚠️ Pipeline não está rodando (status: {self.status.value})")
            return
        
        try:
            logger.info("🛑 Parando pipeline completo...")
            self.status = PipelineStatus.STOPPING
            
            # Parar componentes em paralelo
            tasks = []
            
            if self.realtime_processor:
                tasks.append(self.realtime_processor.stop_processing())
            
            if self.data_streamer:
                tasks.append(self.data_streamer.stop_streaming())
            
            if self.performance_monitor:
                tasks.append(self.performance_monitor.stop_monitoring())
            
            # Aguardar parada
            await asyncio.gather(*tasks, return_exceptions=True)
            
            self.status = PipelineStatus.STOPPED
            logger.info("✅ Pipeline completo parado")
            
            # Notificar callbacks
            await self._notify_status_callbacks()
            
        except Exception as e:
            logger.error(f"❌ Erro ao parar pipeline: {e}")
            self.status = PipelineStatus.ERROR
            await self._notify_error_callbacks(e)
            raise
    
    async def pause_pipeline(self):
        """Pausa o pipeline"""
        if self.status != PipelineStatus.RUNNING:
            logger.warning(f"⚠️ Pipeline não está rodando (status: {self.status.value})")
            return
        
        try:
            logger.info("⏸️ Pausando pipeline...")
            self.status = PipelineStatus.PAUSED
            
            # Pausar componentes
            if self.realtime_processor:
                # Pausar processamento
                pass
            
            if self.data_streamer:
                # Pausar streaming
                pass
            
            logger.info("✅ Pipeline pausado")
            await self._notify_status_callbacks()
            
        except Exception as e:
            logger.error(f"❌ Erro ao pausar pipeline: {e}")
            await self._notify_error_callbacks(e)
    
    async def resume_pipeline(self):
        """Resume o pipeline"""
        if self.status != PipelineStatus.PAUSED:
            logger.warning(f"⚠️ Pipeline não está pausado (status: {self.status.value})")
            return
        
        try:
            logger.info("▶️ Resumindo pipeline...")
            self.status = PipelineStatus.RUNNING
            
            # Resumir componentes
            if self.realtime_processor:
                # Resumir processamento
                pass
            
            if self.data_streamer:
                # Resumir streaming
                pass
            
            logger.info("✅ Pipeline resumido")
            await self._notify_status_callbacks()
            
        except Exception as e:
            logger.error(f"❌ Erro ao resumir pipeline: {e}")
            await self._notify_error_callbacks(e)
    
    async def _handle_data_update(self, update, success: bool):
        """Manipula atualizações de dados"""
        try:
            if success:
                self.metrics['total_processed'] += 1
                self.metrics['last_activity'] = datetime.now()
                
                # Atualizar cache se disponível
                if self.smart_cache:
                    cache_key = f"data_update_{update.timestamp.isoformat()}"
                    await self.smart_cache.set(cache_key, update.data)
                
                # Enviar para streaming se disponível
                if self.data_streamer:
                    # Implementar envio para streams
                    pass
            else:
                self.metrics['errors_count'] += 1
                logger.warning(f"⚠️ Falha no processamento de dados: {update}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao manipular atualização de dados: {e}")
    
    async def _handle_performance_alert(self, alert):
        """Manipula alertas de performance"""
        try:
            logger.warning(f"🚨 Alerta de performance: {alert.message}")
            
            # Ações baseadas no nível do alerta
            if alert.level == AlertLevel.CRITICAL:
                # Ações críticas
                await self._handle_critical_alert(alert)
            elif alert.level == AlertLevel.ERROR:
                # Ações de erro
                await self._handle_error_alert(alert)
            elif alert.level == AlertLevel.WARNING:
                # Ações de warning
                await self._handle_warning_alert(alert)
            
        except Exception as e:
            logger.error(f"❌ Erro ao manipular alerta de performance: {e}")
    
    async def _handle_critical_alert(self, alert):
        """Manipula alertas críticos"""
        logger.critical(f"🚨 ALERTA CRÍTICO: {alert.message}")
        
        # Pausar pipeline se necessário
        if self.status == PipelineStatus.RUNNING:
            await self.pause_pipeline()
        
        # Limpar cache para liberar memória
        if self.smart_cache:
            await self.smart_cache.clear()
    
    async def _handle_error_alert(self, alert):
        """Manipula alertas de erro"""
        logger.error(f"🚨 ALERTA DE ERRO: {alert.message}")
        
        # Reduzir carga de processamento
        if self.realtime_processor:
            # Aumentar intervalos de processamento
            pass
    
    async def _handle_warning_alert(self, alert):
        """Manipula alertas de warning"""
        logger.warning(f"🚨 ALERTA DE WARNING: {alert.message}")
        
        # Monitorar mais de perto
        if self.performance_monitor:
            # Reduzir intervalo de monitoramento
            pass
    
    async def _metrics_task(self):
        """Tarefa de atualização de métricas"""
        while self.status in [PipelineStatus.RUNNING, PipelineStatus.PAUSED]:
            try:
                # Atualizar uptime
                if self.metrics['start_time']:
                    self.metrics['uptime_seconds'] = (
                        datetime.now() - self.metrics['start_time']
                    ).total_seconds()
                
                # Log de métricas
                logger.debug(f"📊 Métricas do pipeline: {self.metrics}")
                
                # Aguardar próximo ciclo
                await asyncio.sleep(60)  # 1 minuto
                
            except Exception as e:
                logger.error(f"❌ Erro na tarefa de métricas: {e}")
                await asyncio.sleep(60)
    
    def add_status_callback(self, callback: Callable):
        """Adiciona callback para mudanças de status"""
        self.status_callbacks.append(callback)
        logger.info("📝 Callback de status adicionado")
    
    def add_error_callback(self, callback: Callable):
        """Adiciona callback para erros"""
        self.error_callbacks.append(callback)
        logger.info("📝 Callback de erro adicionado")
    
    async def _notify_status_callbacks(self):
        """Notifica callbacks de status"""
        for callback in self.status_callbacks:
            try:
                await callback(self.status, self.metrics)
            except Exception as e:
                logger.error(f"❌ Erro ao notificar callback de status: {e}")
    
    async def _notify_error_callbacks(self, error: Exception):
        """Notifica callbacks de erro"""
        for callback in self.error_callbacks:
            try:
                await callback(error, self.metrics)
            except Exception as e:
                logger.error(f"❌ Erro ao notificar callback de erro: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status do pipeline"""
        return {
            'status': self.status.value,
            'metrics': self.metrics,
            'components': {
                'realtime_processor': self.realtime_processor is not None,
                'smart_cache': self.smart_cache is not None,
                'data_streamer': self.data_streamer is not None,
                'performance_monitor': self.performance_monitor is not None
            },
            'config': {
                'gtfs_interval': self.config.gtfs_interval,
                'osm_interval': self.config.osm_interval,
                'integration_interval': self.config.integration_interval,
                'streaming_enabled': self.config.streaming_enabled,
                'cache_strategy': self.config.cache_strategy
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas do pipeline"""
        metrics = self.metrics.copy()
        
        # Adicionar métricas dos componentes
        if self.realtime_processor:
            metrics['realtime_processor'] = self.realtime_processor.get_metrics()
        
        if self.smart_cache:
            metrics['smart_cache'] = self.smart_cache.get_metrics()
        
        if self.data_streamer:
            metrics['data_streamer'] = self.data_streamer.get_metrics()
        
        if self.performance_monitor:
            try:
                metrics['performance_monitor'] = self.performance_monitor.get_performance_summary()
            except Exception as e:
                logger.warning(f"⚠️ Erro ao obter métricas de performance: {e}")
                metrics['performance_monitor'] = {}
        
        return metrics
    
    def get_health_status(self) -> Dict[str, Any]:
        """Retorna status de saúde do pipeline"""
        health = {
            'overall_status': 'healthy',
            'components': {},
            'alerts': [],
            'recommendations': []
        }
        
        # Verificar status dos componentes
        if self.status == PipelineStatus.ERROR:
            health['overall_status'] = 'unhealthy'
            health['alerts'].append('Pipeline em estado de erro')
        
        if self.status == PipelineStatus.STOPPED:
            health['overall_status'] = 'stopped'
        
        # Verificar métricas
        if self.metrics['errors_count'] > 10:
            health['overall_status'] = 'degraded'
            health['alerts'].append('Muitos erros detectados')
            health['recommendations'].append('Verificar logs e reiniciar componentes')
        
        if self.metrics['last_activity']:
            last_activity_age = (datetime.now() - self.metrics['last_activity']).total_seconds()
            if last_activity_age > 3600:  # 1 hora
                health['overall_status'] = 'degraded'
                health['alerts'].append('Sem atividade recente')
                health['recommendations'].append('Verificar conectividade e fontes de dados')
        
        # Verificar componentes
        if self.realtime_processor:
            rt_metrics = self.realtime_processor.get_metrics()
            health['components']['realtime_processor'] = {
                'status': 'healthy' if rt_metrics['is_running'] else 'stopped',
                'quality_score': rt_metrics.get('quality_score', 0)
            }
        
        if self.smart_cache:
            cache_metrics = self.smart_cache.get_metrics()
            health['components']['smart_cache'] = {
                'status': 'healthy',
                'hit_rate': cache_metrics.get('hit_rate', 0),
                'memory_usage_mb': cache_metrics.get('memory_usage_mb', 0)
            }
        
        if self.performance_monitor:
            perf_metrics = self.performance_monitor.get_performance_summary()
            health['components']['performance_monitor'] = {
                'status': 'healthy',
                'cpu_usage': perf_metrics.get('cpu_stats', {}).get('current', 0),
                'memory_usage': perf_metrics.get('memory_stats', {}).get('current', 0)
            }
        
        return health
    
    async def restart_pipeline(self):
        """Reinicia o pipeline"""
        logger.info("🔄 Reiniciando pipeline...")
        
        if self.status in [PipelineStatus.RUNNING, PipelineStatus.PAUSED]:
            await self.stop_pipeline()
        
        await asyncio.sleep(5)  # Aguardar 5 segundos
        
        await self.start_pipeline()
        
        logger.info("✅ Pipeline reiniciado")
    
    async def export_pipeline_state(self, file_path: str):
        """Exporta estado do pipeline"""
        try:
            state = {
                'timestamp': datetime.now().isoformat(),
                'status': self.get_status(),
                'metrics': self.get_metrics(),
                'health': self.get_health_status(),
                'config': {
                    'gtfs_interval': self.config.gtfs_interval,
                    'osm_interval': self.config.osm_interval,
                    'integration_interval': self.config.integration_interval,
                    'streaming_enabled': self.config.streaming_enabled,
                    'cache_strategy': self.config.cache_strategy
                }
            }
            
            import aiofiles
            # Converter datetime para string
            def json_serializer(obj):
                if hasattr(obj, 'isoformat'):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(state, indent=2, ensure_ascii=False, default=json_serializer))
            
            logger.info(f"📁 Estado do pipeline exportado para {file_path}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao exportar estado do pipeline: {e}")
