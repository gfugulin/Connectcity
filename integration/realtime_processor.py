#!/usr/bin/env python3
"""
Processador de dados em tempo real para Conneccity
"""
import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class DataSource(Enum):
    """Fontes de dados"""
    GTFS = "gtfs"
    OSM = "osm"
    INTEGRATED = "integrated"

class UpdateType(Enum):
    """Tipos de atualização"""
    FULL = "full"
    INCREMENTAL = "incremental"
    EMERGENCY = "emergency"

@dataclass
class DataUpdate:
    """Representa uma atualização de dados"""
    source: DataSource
    update_type: UpdateType
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    priority: int = 1  # 1=baixa, 2=média, 3=alta

@dataclass
class ProcessingMetrics:
    """Métricas de processamento"""
    total_updates: int = 0
    successful_updates: int = 0
    failed_updates: int = 0
    avg_processing_time: float = 0.0
    last_update: Optional[datetime] = None
    cache_hit_rate: float = 0.0
    error_rate: float = 0.0

class RealTimeProcessor:
    """
    Processador de dados em tempo real com cache inteligente e streaming
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cache = {}
        self.metrics = ProcessingMetrics()
        self.update_queue = asyncio.Queue()
        self.processing_tasks = []
        self.subscribers = {}
        self.is_running = False
        
        # Configurações de processamento
        self.processing_intervals = {
            DataSource.GTFS: config.get('gtfs_interval', 300),  # 5 minutos
            DataSource.OSM: config.get('osm_interval', 3600),   # 1 hora
            DataSource.INTEGRATED: config.get('integration_interval', 1800)  # 30 minutos
        }
        
        # Configurações de cache
        self.cache_ttl = {
            DataSource.GTFS: config.get('gtfs_cache_ttl', 3600),
            DataSource.OSM: config.get('osm_cache_ttl', 86400),
            DataSource.INTEGRATED: config.get('integration_cache_ttl', 1800)
        }
        
        # Configurações de qualidade
        self.quality_thresholds = {
            'min_data_freshness': config.get('min_data_freshness', 3600),  # 1 hora
            'max_processing_time': config.get('max_processing_time', 300),  # 5 minutos
            'min_cache_hit_rate': config.get('min_cache_hit_rate', 0.8)  # 80%
        }
    
    async def start_processing(self):
        """Inicia o processamento em tempo real"""
        logger.info("🚀 Iniciando processamento em tempo real...")
        self.is_running = True
        
        # Iniciar tarefas de processamento
        self.processing_tasks = [
            asyncio.create_task(self._process_gtfs_updates()),
            asyncio.create_task(self._process_osm_updates()),
            asyncio.create_task(self._process_integrated_updates()),
            asyncio.create_task(self._monitor_quality()),
            asyncio.create_task(self._process_update_queue())
        ]
        
        logger.info("✅ Processamento em tempo real iniciado")
    
    async def stop_processing(self):
        """Para o processamento em tempo real"""
        logger.info("🛑 Parando processamento em tempo real...")
        self.is_running = False
        
        # Cancelar todas as tarefas
        for task in self.processing_tasks:
            task.cancel()
        
        # Aguardar conclusão
        await asyncio.gather(*self.processing_tasks, return_exceptions=True)
        logger.info("✅ Processamento em tempo real parado")
    
    async def _process_gtfs_updates(self):
        """Processa atualizações GTFS em tempo real"""
        while self.is_running:
            try:
                logger.debug("🔍 Verificando atualizações GTFS...")
                
                # Verificar se há dados novos
                updates = await self._check_gtfs_updates()
                
                if updates:
                    logger.info(f"📥 {len(updates)} atualizações GTFS encontradas")
                    
                    for update in updates:
                        # Criar DataUpdate
                        data_update = DataUpdate(
                            source=DataSource.GTFS,
                            update_type=UpdateType.INCREMENTAL,
                            timestamp=datetime.now(),
                            data=update,
                            metadata={'source': 'gtfs_processor'},
                            priority=2
                        )
                        
                        # Adicionar à fila
                        await self.update_queue.put(data_update)
                
                # Aguardar próximo ciclo
                await asyncio.sleep(self.processing_intervals[DataSource.GTFS])
                
            except Exception as e:
                logger.error(f"❌ Erro no processamento GTFS: {e}")
                await asyncio.sleep(60)  # Aguardar 1 minuto antes de tentar novamente
    
    async def _process_osm_updates(self):
        """Processa atualizações OSM em tempo real"""
        while self.is_running:
            try:
                logger.debug("🔍 Verificando atualizações OSM...")
                
                # Verificar se há dados novos
                updates = await self._check_osm_updates()
                
                if updates:
                    logger.info(f"📥 {len(updates)} atualizações OSM encontradas")
                    
                    for update in updates:
                        # Criar DataUpdate
                        data_update = DataUpdate(
                            source=DataSource.OSM,
                            update_type=UpdateType.INCREMENTAL,
                            timestamp=datetime.now(),
                            data=update,
                            metadata={'source': 'osm_processor'},
                            priority=2
                        )
                        
                        # Adicionar à fila
                        await self.update_queue.put(data_update)
                
                # Aguardar próximo ciclo
                await asyncio.sleep(self.processing_intervals[DataSource.OSM])
                
            except Exception as e:
                logger.error(f"❌ Erro no processamento OSM: {e}")
                await asyncio.sleep(60)  # Aguardar 1 minuto antes de tentar novamente
    
    async def _process_integrated_updates(self):
        """Processa atualizações de dados integrados"""
        while self.is_running:
            try:
                logger.debug("🔍 Verificando atualizações integradas...")
                
                # Verificar se há dados novos para integrar
                updates = await self._check_integration_updates()
                
                if updates:
                    logger.info(f"📥 {len(updates)} atualizações integradas encontradas")
                    
                    for update in updates:
                        # Criar DataUpdate
                        data_update = DataUpdate(
                            source=DataSource.INTEGRATED,
                            update_type=UpdateType.FULL,
                            timestamp=datetime.now(),
                            data=update,
                            metadata={'source': 'integration_processor'},
                            priority=3
                        )
                        
                        # Adicionar à fila
                        await self.update_queue.put(data_update)
                
                # Aguardar próximo ciclo
                await asyncio.sleep(self.processing_intervals[DataSource.INTEGRATED])
                
            except Exception as e:
                logger.error(f"❌ Erro no processamento integrado: {e}")
                await asyncio.sleep(60)  # Aguardar 1 minuto antes de tentar novamente
    
    async def _process_update_queue(self):
        """Processa a fila de atualizações"""
        while self.is_running:
            try:
                # Aguardar atualização na fila
                update = await self.update_queue.get()
                
                logger.info(f"🔄 Processando atualização: {update.source.value}")
                
                start_time = time.time()
                
                # Processar atualização
                success = await self._process_single_update(update)
                
                processing_time = time.time() - start_time
                
                # Atualizar métricas
                self.metrics.total_updates += 1
                if success:
                    self.metrics.successful_updates += 1
                else:
                    self.metrics.failed_updates += 1
                
                # Atualizar tempo médio de processamento
                self.metrics.avg_processing_time = (
                    (self.metrics.avg_processing_time * (self.metrics.total_updates - 1) + processing_time) 
                    / self.metrics.total_updates
                )
                
                self.metrics.last_update = datetime.now()
                
                # Notificar subscribers
                await self._notify_subscribers(update, success)
                
                logger.info(f"✅ Atualização processada em {processing_time:.2f}s")
                
            except Exception as e:
                logger.error(f"❌ Erro no processamento da fila: {e}")
                await asyncio.sleep(1)
    
    async def _process_single_update(self, update: DataUpdate) -> bool:
        """Processa uma única atualização"""
        try:
            # Verificar se dados são válidos
            if not self._validate_update_data(update):
                logger.warning(f"⚠️ Dados inválidos para {update.source.value}")
                return False
            
            # Processar baseado na fonte
            if update.source == DataSource.GTFS:
                await self._process_gtfs_data(update.data)
            elif update.source == DataSource.OSM:
                await self._process_osm_data(update.data)
            elif update.source == DataSource.INTEGRATED:
                await self._process_integrated_data(update.data)
            
            # Atualizar cache
            await self._update_cache(update)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar atualização: {e}")
            return False
    
    async def _check_gtfs_updates(self) -> List[Dict[str, Any]]:
        """Verifica atualizações GTFS"""
        # Implementar verificação de atualizações GTFS
        # Por enquanto, retorna lista vazia
        return []
    
    async def _check_osm_updates(self) -> List[Dict[str, Any]]:
        """Verifica atualizações OSM"""
        # Implementar verificação de atualizações OSM
        # Por enquanto, retorna lista vazia
        return []
    
    async def _check_integration_updates(self) -> List[Dict[str, Any]]:
        """Verifica atualizações de integração"""
        # Implementar verificação de atualizações de integração
        # Por enquanto, retorna lista vazia
        return []
    
    def _validate_update_data(self, update: DataUpdate) -> bool:
        """Valida dados de atualização"""
        if not update.data:
            return False
        
        if not isinstance(update.data, dict):
            return False
        
        # Validações específicas por fonte
        if update.source == DataSource.GTFS:
            return 'stops' in update.data or 'routes' in update.data
        elif update.source == DataSource.OSM:
            return 'nodes' in update.data or 'ways' in update.data
        elif update.source == DataSource.INTEGRATED:
            return 'nodes' in update.data and 'edges' in update.data
        
        return True
    
    async def _process_gtfs_data(self, data: Dict[str, Any]):
        """Processa dados GTFS"""
        logger.debug("🔄 Processando dados GTFS...")
        # Implementar processamento específico de GTFS
        pass
    
    async def _process_osm_data(self, data: Dict[str, Any]):
        """Processa dados OSM"""
        logger.debug("🔄 Processando dados OSM...")
        # Implementar processamento específico de OSM
        pass
    
    async def _process_integrated_data(self, data: Dict[str, Any]):
        """Processa dados integrados"""
        logger.debug("🔄 Processando dados integrados...")
        # Implementar processamento específico de dados integrados
        pass
    
    async def _update_cache(self, update: DataUpdate):
        """Atualiza cache com dados processados"""
        cache_key = f"{update.source.value}_{update.timestamp.isoformat()}"
        self.cache[cache_key] = {
            'data': update.data,
            'timestamp': update.timestamp,
            'metadata': update.metadata
        }
        
        # Limpar cache antigo
        await self._cleanup_cache()
    
    async def _cleanup_cache(self):
        """Limpa cache antigo"""
        current_time = datetime.now()
        
        for key, value in list(self.cache.items()):
            if isinstance(value, dict) and 'timestamp' in value:
                age = (current_time - value['timestamp']).total_seconds()
                if age > 86400:  # 24 horas
                    del self.cache[key]
    
    async def _monitor_quality(self):
        """Monitora qualidade dos dados"""
        while self.is_running:
            try:
                # Verificar métricas de qualidade
                quality_score = await self._calculate_quality_score()
                
                if quality_score < 0.8:
                    logger.warning(f"⚠️ Qualidade dos dados baixa: {quality_score:.2f}")
                    await self._trigger_quality_improvement()
                
                # Aguardar próximo ciclo
                await asyncio.sleep(300)  # 5 minutos
                
            except Exception as e:
                logger.error(f"❌ Erro no monitoramento de qualidade: {e}")
                await asyncio.sleep(60)
    
    async def _calculate_quality_score(self) -> float:
        """Calcula score de qualidade dos dados"""
        if self.metrics.total_updates == 0:
            return 1.0
        
        # Calcular score baseado em várias métricas
        success_rate = self.metrics.successful_updates / self.metrics.total_updates
        freshness_score = self._calculate_freshness_score()
        cache_score = self.metrics.cache_hit_rate
        
        # Score combinado
        quality_score = (success_rate * 0.4 + freshness_score * 0.3 + cache_score * 0.3)
        
        return min(1.0, max(0.0, quality_score))
    
    def _calculate_freshness_score(self) -> float:
        """Calcula score de frescor dos dados"""
        if not self.metrics.last_update:
            return 0.0
        
        age = (datetime.now() - self.metrics.last_update).total_seconds()
        max_age = self.quality_thresholds['min_data_freshness']
        
        return max(0.0, 1.0 - (age / max_age))
    
    async def _trigger_quality_improvement(self):
        """Dispara melhorias de qualidade"""
        logger.info("🔧 Disparando melhorias de qualidade...")
        
        # Limpar cache
        self.cache.clear()
        
        # Forçar atualização de dados
        await self._force_data_refresh()
    
    async def _force_data_refresh(self):
        """Força atualização de dados"""
        logger.info("🔄 Forçando atualização de dados...")
        
        # Criar atualizações de emergência
        emergency_updates = [
            DataUpdate(
                source=DataSource.GTFS,
                update_type=UpdateType.EMERGENCY,
                timestamp=datetime.now(),
                data={},
                metadata={'reason': 'quality_improvement'},
                priority=3
            ),
            DataUpdate(
                source=DataSource.OSM,
                update_type=UpdateType.EMERGENCY,
                timestamp=datetime.now(),
                data={},
                metadata={'reason': 'quality_improvement'},
                priority=3
            )
        ]
        
        for update in emergency_updates:
            await self.update_queue.put(update)
    
    async def _notify_subscribers(self, update: DataUpdate, success: bool):
        """Notifica subscribers sobre atualizações"""
        for subscriber_id, callback in self.subscribers.items():
            try:
                await callback(update, success)
            except Exception as e:
                logger.error(f"❌ Erro ao notificar subscriber {subscriber_id}: {e}")
    
    def subscribe(self, subscriber_id: str, callback: Callable):
        """Registra um subscriber para notificações"""
        self.subscribers[subscriber_id] = callback
        logger.info(f"📝 Subscriber {subscriber_id} registrado")
    
    def unsubscribe(self, subscriber_id: str):
        """Remove um subscriber"""
        if subscriber_id in self.subscribers:
            del self.subscribers[subscriber_id]
            logger.info(f"📝 Subscriber {subscriber_id} removido")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas de processamento"""
        return {
            'total_updates': self.metrics.total_updates,
            'successful_updates': self.metrics.successful_updates,
            'failed_updates': self.metrics.failed_updates,
            'success_rate': self.metrics.successful_updates / max(1, self.metrics.total_updates),
            'avg_processing_time': self.metrics.avg_processing_time,
            'last_update': self.metrics.last_update.isoformat() if self.metrics.last_update else None,
            'cache_size': len(self.cache),
            'quality_score': 0.8,  # Valor padrão para evitar asyncio.run()
            'is_running': self.is_running
        }
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Retorna status do cache"""
        return {
            'cache_size': len(self.cache),
            'cache_keys': list(self.cache.keys()),
            'oldest_entry': min(
                (entry['timestamp'] for entry in self.cache.values() 
                 if isinstance(entry, dict) and 'timestamp' in entry),
                default=None
            ),
            'newest_entry': max(
                (entry['timestamp'] for entry in self.cache.values() 
                 if isinstance(entry, dict) and 'timestamp' in entry),
                default=None
            )
        }
