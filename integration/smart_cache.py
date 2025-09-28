#!/usr/bin/env python3
"""
Sistema de cache inteligente para Conneccity
"""
import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import pickle

logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    """Estratégias de cache"""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    ADAPTIVE = "adaptive"  # Adaptativa baseada em padrões

class CacheLevel(Enum):
    """Níveis de cache"""
    L1 = "l1"  # Cache em memória (rápido)
    L2 = "l2"  # Cache em disco (médio)
    L3 = "l3"  # Cache distribuído (lento)

@dataclass
class CacheEntry:
    """Entrada do cache"""
    key: str
    value: Any
    timestamp: datetime
    access_count: int = 0
    last_access: datetime = field(default_factory=datetime.now)
    ttl: Optional[int] = None
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CacheMetrics:
    """Métricas do cache"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_size_bytes: int = 0
    hit_rate: float = 0.0
    avg_access_time: float = 0.0
    memory_usage: float = 0.0

class SmartCache:
    """
    Sistema de cache inteligente com múltiplas estratégias e níveis
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Cache L1 (memória)
        self.l1_cache: Dict[str, CacheEntry] = {}
        self.l1_max_size = config.get('l1_max_size', 1000)
        self.l1_max_memory = config.get('l1_max_memory_mb', 100) * 1024 * 1024
        
        # Cache L2 (disco)
        self.l2_cache_path = config.get('l2_cache_path', 'cache/l2')
        self.l2_max_size = config.get('l2_max_size', 10000)
        
        # Cache L3 (distribuído)
        self.l3_enabled = config.get('l3_enabled', False)
        self.l3_nodes = config.get('l3_nodes', [])
        
        # Estratégias de cache
        self.strategy = CacheStrategy(config.get('cache_strategy', 'adaptive'))
        self.default_ttl = config.get('default_ttl', 3600)
        
        # Métricas
        self.metrics = CacheMetrics()
        
        # Configurações de limpeza
        self.cleanup_interval = config.get('cleanup_interval', 300)  # 5 minutos
        self.cleanup_threshold = config.get('cleanup_threshold', 0.8)  # 80%
        
        # Padrões de acesso
        self.access_patterns = {}
        self.pattern_analysis_interval = config.get('pattern_analysis_interval', 3600)  # 1 hora
        
        # Inicializar
        self._initialize_cache()
    
    def _initialize_cache(self):
        """Inicializa o sistema de cache"""
        import os
        
        # Criar diretório L2 se não existir
        os.makedirs(self.l2_cache_path, exist_ok=True)
        
        # Iniciar tarefas de manutenção
        self._start_maintenance_tasks()
        
        logger.info("✅ Sistema de cache inteligente inicializado")
    
    def _start_maintenance_tasks(self):
        """Inicia tarefas de manutenção do cache"""
        asyncio.create_task(self._cleanup_task())
        asyncio.create_task(self._pattern_analysis_task())
        asyncio.create_task(self._metrics_update_task())
    
    async def get(self, key: str, cache_level: Optional[CacheLevel] = None) -> Optional[Any]:
        """Recupera valor do cache"""
        start_time = time.time()
        
        try:
            # Tentar L1 primeiro
            if cache_level is None or cache_level == CacheLevel.L1:
                value = await self._get_from_l1(key)
                if value is not None:
                    self.metrics.hits += 1
                    self._update_access_pattern(key, 'l1_hit')
                    return value
            
            # Tentar L2
            if cache_level is None or cache_level == CacheLevel.L2:
                value = await self._get_from_l2(key)
                if value is not None:
                    # Promover para L1
                    await self._promote_to_l1(key, value)
                    self.metrics.hits += 1
                    self._update_access_pattern(key, 'l2_hit')
                    return value
            
            # Tentar L3 (se habilitado)
            if self.l3_enabled and (cache_level is None or cache_level == CacheLevel.L3):
                value = await self._get_from_l3(key)
                if value is not None:
                    # Promover para L1 e L2
                    await self._promote_to_l1(key, value)
                    await self._promote_to_l2(key, value)
                    self.metrics.hits += 1
                    self._update_access_pattern(key, 'l3_hit')
                    return value
            
            # Cache miss
            self.metrics.misses += 1
            self._update_access_pattern(key, 'miss')
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao recuperar do cache: {e}")
            return None
        finally:
            # Atualizar métricas
            access_time = time.time() - start_time
            self._update_avg_access_time(access_time)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, 
                  cache_level: CacheLevel = CacheLevel.L1, metadata: Optional[Dict] = None) -> bool:
        """Armazena valor no cache"""
        try:
            # Calcular TTL
            if ttl is None:
                ttl = self._calculate_adaptive_ttl(key, value)
            
            # Criar entrada do cache
            entry = CacheEntry(
                key=key,
                value=value,
                timestamp=datetime.now(),
                ttl=ttl,
                size_bytes=self._calculate_size(value),
                metadata=metadata or {}
            )
            
            # Armazenar no nível apropriado
            if cache_level == CacheLevel.L1:
                await self._set_in_l1(key, entry)
            elif cache_level == CacheLevel.L2:
                await self._set_in_l2(key, entry)
            elif cache_level == CacheLevel.L3:
                await self._set_in_l3(key, entry)
            
            # Atualizar padrões de acesso
            self._update_access_pattern(key, 'set')
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao armazenar no cache: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Remove valor do cache"""
        try:
            # Remover de todos os níveis
            removed = False
            
            if key in self.l1_cache:
                del self.l1_cache[key]
                removed = True
            
            if await self._delete_from_l2(key):
                removed = True
            
            if self.l3_enabled and await self._delete_from_l3(key):
                removed = True
            
            return removed
            
        except Exception as e:
            logger.error(f"❌ Erro ao remover do cache: {e}")
            return False
    
    async def clear(self, cache_level: Optional[CacheLevel] = None):
        """Limpa cache"""
        try:
            if cache_level is None or cache_level == CacheLevel.L1:
                self.l1_cache.clear()
            
            if cache_level is None or cache_level == CacheLevel.L2:
                await self._clear_l2()
            
            if cache_level is None or cache_level == CacheLevel.L3:
                if self.l3_enabled:
                    await self._clear_l3()
            
            logger.info("🧹 Cache limpo")
            
        except Exception as e:
            logger.error(f"❌ Erro ao limpar cache: {e}")
    
    async def _get_from_l1(self, key: str) -> Optional[Any]:
        """Recupera do cache L1"""
        if key not in self.l1_cache:
            return None
        
        entry = self.l1_cache[key]
        
        # Verificar TTL
        if entry.ttl and (datetime.now() - entry.timestamp).total_seconds() > entry.ttl:
            del self.l1_cache[key]
            return None
        
        # Atualizar estatísticas de acesso
        entry.access_count += 1
        entry.last_access = datetime.now()
        
        return entry.value
    
    async def _get_from_l2(self, key: str) -> Optional[Any]:
        """Recupera do cache L2"""
        try:
            import os
            file_path = os.path.join(self.l2_cache_path, f"{key}.cache")
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'rb') as f:
                entry = pickle.load(f)
            
            # Verificar TTL
            if entry.ttl and (datetime.now() - entry.timestamp).total_seconds() > entry.ttl:
                os.remove(file_path)
                return None
            
            # Atualizar estatísticas
            entry.access_count += 1
            entry.last_access = datetime.now()
            
            # Salvar estatísticas atualizadas
            with open(file_path, 'wb') as f:
                pickle.dump(entry, f)
            
            return entry.value
            
        except Exception as e:
            logger.error(f"❌ Erro ao recuperar do L2: {e}")
            return None
    
    async def _get_from_l3(self, key: str) -> Optional[Any]:
        """Recupera do cache L3 (distribuído)"""
        # Implementar cache distribuído
        # Por enquanto, retorna None
        return None
    
    async def _set_in_l1(self, key: str, entry: CacheEntry):
        """Armazena no cache L1"""
        # Verificar se precisa evictar
        if len(self.l1_cache) >= self.l1_max_size:
            await self._evict_from_l1()
        
        # Verificar uso de memória
        if self._get_l1_memory_usage() + entry.size_bytes > self.l1_max_memory:
            await self._evict_from_l1()
        
        self.l1_cache[key] = entry
    
    async def _set_in_l2(self, key: str, entry: CacheEntry):
        """Armazena no cache L2"""
        try:
            import os
            file_path = os.path.join(self.l2_cache_path, f"{key}.cache")
            
            with open(file_path, 'wb') as f:
                pickle.dump(entry, f)
                
        except Exception as e:
            logger.error(f"❌ Erro ao armazenar no L2: {e}")
    
    async def _set_in_l3(self, key: str, entry: CacheEntry):
        """Armazena no cache L3 (distribuído)"""
        # Implementar cache distribuído
        pass
    
    async def _promote_to_l1(self, key: str, value: Any):
        """Promove valor para L1"""
        entry = CacheEntry(
            key=key,
            value=value,
            timestamp=datetime.now(),
            ttl=self.default_ttl,
            size_bytes=self._calculate_size(value)
        )
        
        await self._set_in_l1(key, entry)
    
    async def _promote_to_l2(self, key: str, value: Any):
        """Promove valor para L2"""
        entry = CacheEntry(
            key=key,
            value=value,
            timestamp=datetime.now(),
            ttl=self.default_ttl,
            size_bytes=self._calculate_size(value)
        )
        
        await self._set_in_l2(key, entry)
    
    async def _evict_from_l1(self):
        """Remove entradas do L1 baseado na estratégia"""
        if not self.l1_cache:
            return
        
        if self.strategy == CacheStrategy.LRU:
            # Remover menos recentemente usado
            oldest_key = min(self.l1_cache.keys(), 
                           key=lambda k: self.l1_cache[k].last_access)
            del self.l1_cache[oldest_key]
            
        elif self.strategy == CacheStrategy.LFU:
            # Remover menos frequentemente usado
            least_used_key = min(self.l1_cache.keys(),
                               key=lambda k: self.l1_cache[k].access_count)
            del self.l1_cache[least_used_key]
            
        elif self.strategy == CacheStrategy.TTL:
            # Remover mais antigo
            oldest_key = min(self.l1_cache.keys(),
                           key=lambda k: self.l1_cache[k].timestamp)
            del self.l1_cache[oldest_key]
            
        elif self.strategy == CacheStrategy.ADAPTIVE:
            # Remover baseado em padrões de acesso
            await self._adaptive_eviction()
        
        self.metrics.evictions += 1
    
    async def _adaptive_eviction(self):
        """Evicção adaptativa baseada em padrões"""
        # Analisar padrões de acesso
        current_time = datetime.now()
        
        # Calcular score de cada entrada
        scores = {}
        for key, entry in self.l1_cache.items():
            score = self._calculate_access_score(entry, current_time)
            scores[key] = score
        
        # Remover entrada com menor score
        if scores:
            worst_key = min(scores.keys(), key=lambda k: scores[k])
            del self.l1_cache[worst_key]
    
    def _calculate_access_score(self, entry: CacheEntry, current_time: datetime) -> float:
        """Calcula score de acesso para evicção adaptativa"""
        # Fatores: frequência, recência, tamanho
        frequency_score = entry.access_count / max(1, (current_time - entry.timestamp).total_seconds() / 3600)
        recency_score = 1.0 / max(1, (current_time - entry.last_access).total_seconds() / 3600)
        size_penalty = entry.size_bytes / (1024 * 1024)  # Penalizar entradas grandes
        
        return frequency_score * 0.4 + recency_score * 0.6 - size_penalty * 0.1
    
    def _calculate_adaptive_ttl(self, key: str, value: Any) -> int:
        """Calcula TTL adaptativo baseado em padrões"""
        # TTL baseado no tipo de dados
        if isinstance(value, dict):
            if 'nodes' in value:
                return 86400  # 24 horas para dados de nós
            elif 'edges' in value:
                return 43200  # 12 horas para dados de arestas
            else:
                return 3600  # 1 hora para outros dados
        
        # TTL baseado em padrões de acesso
        if key in self.access_patterns:
            pattern = self.access_patterns[key]
            if pattern.get('frequency', 0) > 10:  # Acesso frequente
                return 7200  # 2 horas
            elif pattern.get('frequency', 0) > 5:  # Acesso moderado
                return 3600  # 1 hora
            else:  # Acesso baixo
                return 1800  # 30 minutos
        
        return self.default_ttl
    
    def _calculate_size(self, value: Any) -> int:
        """Calcula tamanho em bytes de um valor"""
        try:
            return len(pickle.dumps(value))
        except:
            return 1024  # Tamanho padrão
    
    def _get_l1_memory_usage(self) -> int:
        """Calcula uso de memória do L1"""
        return sum(entry.size_bytes for entry in self.l1_cache.values())
    
    def _update_access_pattern(self, key: str, access_type: str):
        """Atualiza padrões de acesso"""
        if key not in self.access_patterns:
            self.access_patterns[key] = {
                'frequency': 0,
                'last_access': datetime.now(),
                'access_types': []
            }
        
        pattern = self.access_patterns[key]
        pattern['frequency'] += 1
        pattern['last_access'] = datetime.now()
        pattern['access_types'].append(access_type)
        
        # Manter apenas últimos 100 acessos
        if len(pattern['access_types']) > 100:
            pattern['access_types'] = pattern['access_types'][-100:]
    
    def _update_avg_access_time(self, access_time: float):
        """Atualiza tempo médio de acesso"""
        total_requests = self.metrics.hits + self.metrics.misses
        if total_requests > 0:
            self.metrics.avg_access_time = (
                (self.metrics.avg_access_time * (total_requests - 1) + access_time) / total_requests
            )
    
    async def _cleanup_task(self):
        """Tarefa de limpeza automática"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                # Verificar se precisa limpar
                usage_ratio = len(self.l1_cache) / self.l1_max_size
                if usage_ratio > self.cleanup_threshold:
                    await self._cleanup_expired_entries()
                    await self._cleanup_old_patterns()
                
            except Exception as e:
                logger.error(f"❌ Erro na tarefa de limpeza: {e}")
    
    async def _cleanup_expired_entries(self):
        """Remove entradas expiradas"""
        current_time = datetime.now()
        expired_keys = []
        
        for key, entry in self.l1_cache.items():
            if entry.ttl and (current_time - entry.timestamp).total_seconds() > entry.ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.l1_cache[key]
        
        if expired_keys:
            logger.info(f"🧹 Removidas {len(expired_keys)} entradas expiradas do L1")
    
    async def _cleanup_old_patterns(self):
        """Remove padrões antigos"""
        current_time = datetime.now()
        old_patterns = []
        
        for key, pattern in self.access_patterns.items():
            if (current_time - pattern['last_access']).total_seconds() > 86400:  # 24 horas
                old_patterns.append(key)
        
        for key in old_patterns:
            del self.access_patterns[key]
    
    async def _pattern_analysis_task(self):
        """Tarefa de análise de padrões"""
        while True:
            try:
                await asyncio.sleep(self.pattern_analysis_interval)
                await self._analyze_access_patterns()
                
            except Exception as e:
                logger.error(f"❌ Erro na análise de padrões: {e}")
    
    async def _analyze_access_patterns(self):
        """Analisa padrões de acesso para otimização"""
        logger.info("📊 Analisando padrões de acesso...")
        
        # Calcular métricas de padrões
        total_patterns = len(self.access_patterns)
        if total_patterns == 0:
            return
        
        # Encontrar padrões mais comuns
        access_types = {}
        for pattern in self.access_patterns.values():
            for access_type in pattern['access_types']:
                access_types[access_type] = access_types.get(access_type, 0) + 1
        
        logger.info(f"📈 Padrões de acesso: {access_types}")
        
        # Otimizar estratégia baseada em padrões
        await self._optimize_cache_strategy()
    
    async def _optimize_cache_strategy(self):
        """Otimiza estratégia de cache baseada em padrões"""
        # Implementar otimizações baseadas em padrões
        pass
    
    async def _metrics_update_task(self):
        """Tarefa de atualização de métricas"""
        while True:
            try:
                await asyncio.sleep(60)  # 1 minuto
                self._update_metrics()
                
            except Exception as e:
                logger.error(f"❌ Erro na atualização de métricas: {e}")
    
    def _update_metrics(self):
        """Atualiza métricas do cache"""
        total_requests = self.metrics.hits + self.metrics.misses
        if total_requests > 0:
            self.metrics.hit_rate = self.metrics.hits / total_requests
        
        self.metrics.total_size_bytes = self._get_l1_memory_usage()
        self.metrics.memory_usage = self.metrics.total_size_bytes / (1024 * 1024)  # MB
    
    async def _delete_from_l2(self, key: str) -> bool:
        """Remove do cache L2"""
        try:
            import os
            file_path = os.path.join(self.l2_cache_path, f"{key}.cache")
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao remover do L2: {e}")
            return False
    
    async def _delete_from_l3(self, key: str) -> bool:
        """Remove do cache L3"""
        # Implementar remoção do cache distribuído
        return False
    
    async def _clear_l2(self):
        """Limpa cache L2"""
        try:
            import os
            import shutil
            if os.path.exists(self.l2_cache_path):
                shutil.rmtree(self.l2_cache_path)
                os.makedirs(self.l2_cache_path, exist_ok=True)
        except Exception as e:
            logger.error(f"❌ Erro ao limpar L2: {e}")
    
    async def _clear_l3(self):
        """Limpa cache L3"""
        # Implementar limpeza do cache distribuído
        pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas do cache"""
        return {
            'hits': self.metrics.hits,
            'misses': self.metrics.misses,
            'hit_rate': self.metrics.hit_rate,
            'evictions': self.metrics.evictions,
            'total_size_bytes': self.metrics.total_size_bytes,
            'memory_usage_mb': self.metrics.memory_usage,
            'avg_access_time': self.metrics.avg_access_time,
            'l1_size': len(self.l1_cache),
            'l1_max_size': self.l1_max_size,
            'l1_usage_ratio': len(self.l1_cache) / self.l1_max_size,
            'access_patterns_count': len(self.access_patterns),
            'strategy': self.strategy.value
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status do cache"""
        return {
            'l1_cache': {
                'size': len(self.l1_cache),
                'max_size': self.l1_max_size,
                'usage_ratio': len(self.l1_cache) / self.l1_max_size,
                'memory_usage_mb': self.metrics.memory_usage
            },
            'l2_cache': {
                'enabled': True,
                'path': self.l2_cache_path,
                'max_size': self.l2_max_size
            },
            'l3_cache': {
                'enabled': self.l3_enabled,
                'nodes': len(self.l3_nodes)
            },
            'strategy': self.strategy.value,
            'metrics': self.get_metrics()
        }


