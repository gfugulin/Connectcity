#!/usr/bin/env python3
"""
Sistema de streaming de dados para Conneccity
"""
import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
import aiohttp
import aiofiles

logger = logging.getLogger(__name__)

class StreamType(Enum):
    """Tipos de stream"""
    GTFS_REALTIME = "gtfs_realtime"
    OSM_CHANGES = "osm_changes"
    INTEGRATION_UPDATES = "integration_updates"
    ROUTE_CALCULATIONS = "route_calculations"

class StreamStatus(Enum):
    """Status do stream"""
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"

@dataclass
class StreamMessage:
    """Mensagem do stream"""
    stream_type: StreamType
    timestamp: datetime
    data: Dict[str, Any]
    message_id: str
    priority: int = 1
    metadata: Dict[str, Any] = None

@dataclass
class StreamConfig:
    """Configuração do stream"""
    stream_type: StreamType
    endpoint: str
    interval: int = 30  # segundos
    timeout: int = 30
    retry_attempts: int = 3
    buffer_size: int = 1000
    compression: bool = True

class DataStreamer:
    """
    Sistema de streaming de dados em tempo real
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.streams: Dict[StreamType, StreamConfig] = {}
        self.active_streams: Dict[StreamType, asyncio.Task] = {}
        self.subscribers: Dict[StreamType, List[Callable]] = {}
        self.message_buffer: Dict[StreamType, List[StreamMessage]] = {}
        self.is_running = False
        
        # Configurações
        self.max_buffer_size = config.get('max_buffer_size', 10000)
        self.cleanup_interval = config.get('cleanup_interval', 300)  # 5 minutos
        self.retry_delay = config.get('retry_delay', 60)  # 1 minuto
        
        # Métricas
        self.metrics = {
            'total_messages': 0,
            'successful_streams': 0,
            'failed_streams': 0,
            'buffer_usage': 0,
            'last_activity': None
        }
    
    async def start_streaming(self):
        """Inicia o sistema de streaming"""
        logger.info("🚀 Iniciando sistema de streaming...")
        self.is_running = True
        
        # Iniciar streams configurados
        for stream_type, stream_config in self.streams.items():
            await self._start_stream(stream_type, stream_config)
        
        # Iniciar tarefas de manutenção
        asyncio.create_task(self._cleanup_task())
        asyncio.create_task(self._metrics_task())
        
        logger.info("✅ Sistema de streaming iniciado")
    
    async def stop_streaming(self):
        """Para o sistema de streaming"""
        logger.info("🛑 Parando sistema de streaming...")
        self.is_running = False
        
        # Parar todos os streams
        for stream_type, task in self.active_streams.items():
            task.cancel()
        
        # Aguardar conclusão
        await asyncio.gather(*self.active_streams.values(), return_exceptions=True)
        
        logger.info("✅ Sistema de streaming parado")
    
    def add_stream(self, stream_type: StreamType, config: StreamConfig):
        """Adiciona um novo stream"""
        self.streams[stream_type] = config
        self.message_buffer[stream_type] = []
        self.subscribers[stream_type] = []
        
        logger.info(f"📝 Stream {stream_type.value} adicionado")
    
    def remove_stream(self, stream_type: StreamType):
        """Remove um stream"""
        if stream_type in self.streams:
            del self.streams[stream_type]
        
        if stream_type in self.active_streams:
            self.active_streams[stream_type].cancel()
            del self.active_streams[stream_type]
        
        if stream_type in self.message_buffer:
            del self.message_buffer[stream_type]
        
        if stream_type in self.subscribers:
            del self.subscribers[stream_type]
        
        logger.info(f"📝 Stream {stream_type.value} removido")
    
    async def _start_stream(self, stream_type: StreamType, config: StreamConfig):
        """Inicia um stream específico"""
        try:
            task = asyncio.create_task(self._stream_worker(stream_type, config))
            self.active_streams[stream_type] = task
            logger.info(f"✅ Stream {stream_type.value} iniciado")
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar stream {stream_type.value}: {e}")
    
    async def _stream_worker(self, stream_type: StreamType, config: StreamConfig):
        """Worker para um stream específico"""
        retry_count = 0
        
        while self.is_running and retry_count < config.retry_attempts:
            try:
                # Fazer requisição
                data = await self._fetch_stream_data(stream_type, config)
                
                if data:
                    # Processar dados
                    messages = await self._process_stream_data(stream_type, data)
                    
                    # Adicionar ao buffer
                    for message in messages:
                        await self._add_to_buffer(stream_type, message)
                    
                    # Notificar subscribers
                    await self._notify_subscribers(stream_type, messages)
                    
                    # Reset retry count
                    retry_count = 0
                    
                    # Atualizar métricas
                    self.metrics['successful_streams'] += 1
                    self.metrics['last_activity'] = datetime.now()
                
                # Aguardar próximo ciclo
                await asyncio.sleep(config.interval)
                
            except Exception as e:
                logger.error(f"❌ Erro no stream {stream_type.value}: {e}")
                retry_count += 1
                
                if retry_count < config.retry_attempts:
                    logger.info(f"🔄 Tentando novamente em {self.retry_delay}s...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(f"❌ Stream {stream_type.value} falhou após {config.retry_attempts} tentativas")
                    self.metrics['failed_streams'] += 1
                    break
    
    async def _fetch_stream_data(self, stream_type: StreamType, config: StreamConfig) -> Optional[Dict[str, Any]]:
        """Busca dados do stream"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.timeout)) as session:
                async with session.get(config.endpoint) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        logger.warning(f"⚠️ Status HTTP {response.status} para {stream_type.value}")
                        return None
        except Exception as e:
            logger.error(f"❌ Erro ao buscar dados do stream {stream_type.value}: {e}")
            return None
    
    async def _process_stream_data(self, stream_type: StreamType, data: Dict[str, Any]) -> List[StreamMessage]:
        """Processa dados do stream"""
        messages = []
        
        try:
            if stream_type == StreamType.GTFS_REALTIME:
                messages = await self._process_gtfs_realtime(data)
            elif stream_type == StreamType.OSM_CHANGES:
                messages = await self._process_osm_changes(data)
            elif stream_type == StreamType.INTEGRATION_UPDATES:
                messages = await self._process_integration_updates(data)
            elif stream_type == StreamType.ROUTE_CALCULATIONS:
                messages = await self._process_route_calculations(data)
            
            return messages
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar dados do stream {stream_type.value}: {e}")
            return []
    
    async def _process_gtfs_realtime(self, data: Dict[str, Any]) -> List[StreamMessage]:
        """Processa dados GTFS em tempo real"""
        messages = []
        
        # Processar paradas
        if 'stops' in data:
            for stop in data['stops']:
                message = StreamMessage(
                    stream_type=StreamType.GTFS_REALTIME,
                    timestamp=datetime.now(),
                    data=stop,
                    message_id=f"gtfs_stop_{stop.get('id', 'unknown')}",
                    priority=2,
                    metadata={'type': 'stop_update'}
                )
                messages.append(message)
        
        # Processar rotas
        if 'routes' in data:
            for route in data['routes']:
                message = StreamMessage(
                    stream_type=StreamType.GTFS_REALTIME,
                    timestamp=datetime.now(),
                    data=route,
                    message_id=f"gtfs_route_{route.get('id', 'unknown')}",
                    priority=1,
                    metadata={'type': 'route_update'}
                )
                messages.append(message)
        
        return messages
    
    async def _process_osm_changes(self, data: Dict[str, Any]) -> List[StreamMessage]:
        """Processa mudanças OSM"""
        messages = []
        
        # Processar nós
        if 'nodes' in data:
            for node in data['nodes']:
                message = StreamMessage(
                    stream_type=StreamType.OSM_CHANGES,
                    timestamp=datetime.now(),
                    data=node,
                    message_id=f"osm_node_{node.get('id', 'unknown')}",
                    priority=2,
                    metadata={'type': 'node_change'}
                )
                messages.append(message)
        
        # Processar vias
        if 'ways' in data:
            for way in data['ways']:
                message = StreamMessage(
                    stream_type=StreamType.OSM_CHANGES,
                    timestamp=datetime.now(),
                    data=way,
                    message_id=f"osm_way_{way.get('id', 'unknown')}",
                    priority=1,
                    metadata={'type': 'way_change'}
                )
                messages.append(message)
        
        return messages
    
    async def _process_integration_updates(self, data: Dict[str, Any]) -> List[StreamMessage]:
        """Processa atualizações de integração"""
        messages = []
        
        # Processar nós integrados
        if 'integrated_nodes' in data:
            for node in data['integrated_nodes']:
                message = StreamMessage(
                    stream_type=StreamType.INTEGRATION_UPDATES,
                    timestamp=datetime.now(),
                    data=node,
                    message_id=f"integrated_node_{node.get('id', 'unknown')}",
                    priority=3,
                    metadata={'type': 'integrated_node'}
                )
                messages.append(message)
        
        # Processar arestas integradas
        if 'integrated_edges' in data:
            for edge in data['integrated_edges']:
                message = StreamMessage(
                    stream_type=StreamType.INTEGRATION_UPDATES,
                    timestamp=datetime.now(),
                    data=edge,
                    message_id=f"integrated_edge_{edge.get('id', 'unknown')}",
                    priority=3,
                    metadata={'type': 'integrated_edge'}
                )
                messages.append(message)
        
        return messages
    
    async def _process_route_calculations(self, data: Dict[str, Any]) -> List[StreamMessage]:
        """Processa cálculos de rota"""
        messages = []
        
        # Processar rotas calculadas
        if 'routes' in data:
            for route in data['routes']:
                message = StreamMessage(
                    stream_type=StreamType.ROUTE_CALCULATIONS,
                    timestamp=datetime.now(),
                    data=route,
                    message_id=f"route_{route.get('id', 'unknown')}",
                    priority=1,
                    metadata={'type': 'route_calculation'}
                )
                messages.append(message)
        
        return messages
    
    async def _add_to_buffer(self, stream_type: StreamType, message: StreamMessage):
        """Adiciona mensagem ao buffer"""
        if stream_type not in self.message_buffer:
            self.message_buffer[stream_type] = []
        
        self.message_buffer[stream_type].append(message)
        
        # Verificar tamanho do buffer
        if len(self.message_buffer[stream_type]) > self.max_buffer_size:
            # Remover mensagens mais antigas
            self.message_buffer[stream_type] = self.message_buffer[stream_type][-self.max_buffer_size:]
        
        self.metrics['total_messages'] += 1
        self.metrics['buffer_usage'] = sum(len(buffer) for buffer in self.message_buffer.values())
    
    async def _notify_subscribers(self, stream_type: StreamType, messages: List[StreamMessage]):
        """Notifica subscribers sobre novas mensagens"""
        if stream_type not in self.subscribers:
            return
        
        for callback in self.subscribers[stream_type]:
            try:
                await callback(stream_type, messages)
            except Exception as e:
                logger.error(f"❌ Erro ao notificar subscriber: {e}")
    
    def subscribe(self, stream_type: StreamType, callback: Callable):
        """Registra um subscriber para um stream"""
        if stream_type not in self.subscribers:
            self.subscribers[stream_type] = []
        
        self.subscribers[stream_type].append(callback)
        logger.info(f"📝 Subscriber registrado para {stream_type.value}")
    
    def unsubscribe(self, stream_type: StreamType, callback: Callable):
        """Remove um subscriber"""
        if stream_type in self.subscribers and callback in self.subscribers[stream_type]:
            self.subscribers[stream_type].remove(callback)
            logger.info(f"📝 Subscriber removido de {stream_type.value}")
    
    async def get_messages(self, stream_type: StreamType, limit: int = 100) -> List[StreamMessage]:
        """Recupera mensagens de um stream"""
        if stream_type not in self.message_buffer:
            return []
        
        messages = self.message_buffer[stream_type]
        return messages[-limit:] if limit > 0 else messages
    
    async def get_latest_messages(self, stream_type: StreamType, count: int = 10) -> List[StreamMessage]:
        """Recupera as mensagens mais recentes"""
        messages = await self.get_messages(stream_type, count)
        return sorted(messages, key=lambda m: m.timestamp, reverse=True)[:count]
    
    async def get_messages_by_priority(self, stream_type: StreamType, min_priority: int = 1) -> List[StreamMessage]:
        """Recupera mensagens por prioridade"""
        if stream_type not in self.message_buffer:
            return []
        
        messages = self.message_buffer[stream_type]
        return [msg for msg in messages if msg.priority >= min_priority]
    
    async def _cleanup_task(self):
        """Tarefa de limpeza do buffer"""
        while self.is_running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                # Limpar mensagens antigas
                current_time = datetime.now()
                max_age = 3600  # 1 hora
                
                for stream_type, messages in self.message_buffer.items():
                    # Remover mensagens mais antigas que max_age
                    self.message_buffer[stream_type] = [
                        msg for msg in messages
                        if (current_time - msg.timestamp).total_seconds() < max_age
                    ]
                
                logger.debug("🧹 Buffer limpo")
                
            except Exception as e:
                logger.error(f"❌ Erro na tarefa de limpeza: {e}")
    
    async def _metrics_task(self):
        """Tarefa de atualização de métricas"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # 1 minuto
                
                # Atualizar métricas
                self.metrics['buffer_usage'] = sum(len(buffer) for buffer in self.message_buffer.values())
                
                # Log de métricas
                logger.debug(f"📊 Métricas: {self.metrics}")
                
            except Exception as e:
                logger.error(f"❌ Erro na tarefa de métricas: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas do streaming"""
        return {
            'total_messages': self.metrics['total_messages'],
            'successful_streams': self.metrics['successful_streams'],
            'failed_streams': self.metrics['failed_streams'],
            'buffer_usage': self.metrics['buffer_usage'],
            'last_activity': self.metrics['last_activity'].isoformat() if self.metrics['last_activity'] else None,
            'active_streams': len(self.active_streams),
            'total_streams': len(self.streams),
            'subscribers': {stream_type.value: len(callbacks) for stream_type, callbacks in self.subscribers.items()}
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status do streaming"""
        return {
            'is_running': self.is_running,
            'active_streams': list(self.active_streams.keys()),
            'configured_streams': list(self.streams.keys()),
            'buffer_sizes': {stream_type.value: len(messages) for stream_type, messages in self.message_buffer.items()},
            'metrics': self.get_metrics()
        }
    
    async def export_messages(self, stream_type: StreamType, file_path: str):
        """Exporta mensagens para arquivo"""
        try:
            messages = await self.get_messages(stream_type)
            
            # Converter para formato exportável
            export_data = []
            for message in messages:
                export_data.append({
                    'stream_type': message.stream_type.value,
                    'timestamp': message.timestamp.isoformat(),
                    'message_id': message.message_id,
                    'priority': message.priority,
                    'data': message.data,
                    'metadata': message.metadata
                })
            
            # Salvar arquivo
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(export_data, indent=2, ensure_ascii=False))
            
            logger.info(f"📁 Mensagens exportadas para {file_path}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao exportar mensagens: {e}")
    
    async def import_messages(self, file_path: str, stream_type: StreamType):
        """Importa mensagens de arquivo"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content)
            
            # Processar mensagens importadas
            for item in data:
                message = StreamMessage(
                    stream_type=StreamType(item['stream_type']),
                    timestamp=datetime.fromisoformat(item['timestamp']),
                    data=item['data'],
                    message_id=item['message_id'],
                    priority=item['priority'],
                    metadata=item.get('metadata', {})
                )
                
                await self._add_to_buffer(stream_type, message)
            
            logger.info(f"📁 Mensagens importadas de {file_path}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao importar mensagens: {e}")
