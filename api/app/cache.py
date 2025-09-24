"""
Sistema de cache para otimização de performance
"""
import time
import hashlib
import json
from typing import Any, Optional, Dict
from functools import wraps
import threading

class LRUCache:
    """Cache LRU simples para otimização"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl  # Time to live em segundos
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        self.lock = threading.RLock()
    
    def _is_expired(self, key: str) -> bool:
        """Verifica se uma entrada expirou"""
        if key not in self.cache:
            return True
        return time.time() - self.cache[key]['timestamp'] > self.ttl
    
    def _evict_lru(self):
        """Remove a entrada menos recentemente usada"""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        self._remove_key(lru_key)
    
    def _remove_key(self, key: str):
        """Remove uma chave do cache"""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)
    
    def get(self, key: str) -> Optional[Any]:
        """Obtém valor do cache"""
        with self.lock:
            if key not in self.cache or self._is_expired(key):
                if key in self.cache:
                    self._remove_key(key)
                return None
            
            self.access_times[key] = time.time()
            return self.cache[key]['value']
    
    def set(self, key: str, value: Any):
        """Define valor no cache"""
        with self.lock:
            # Remover se já existe
            if key in self.cache:
                self._remove_key(key)
            
            # Evict se necessário
            if len(self.cache) >= self.max_size:
                self._evict_lru()
            
            self.cache[key] = {
                'value': value,
                'timestamp': time.time()
            }
            self.access_times[key] = time.time()
    
    def clear(self):
        """Limpa o cache"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        with self.lock:
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'ttl': self.ttl,
                'hit_ratio': getattr(self, '_hit_count', 0) / max(getattr(self, '_access_count', 1), 1)
            }

# Cache global
route_cache = LRUCache(max_size=500, ttl=300)  # 5 minutos
alternatives_cache = LRUCache(max_size=200, ttl=180)  # 3 minutos
edge_analysis_cache = LRUCache(max_size=50, ttl=600)  # 10 minutos

def cache_key(*args, **kwargs) -> str:
    """Gera chave de cache baseada nos argumentos"""
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    key_str = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()

def cached_route(cache_instance: LRUCache):
    """Decorator para cache de rotas"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gerar chave de cache
            key = cache_key(*args, **kwargs)
            
            # Tentar obter do cache
            cached_result = cache_instance.get(key)
            if cached_result is not None:
                return cached_result
            
            # Executar função e cachear resultado
            result = func(*args, **kwargs)
            cache_instance.set(key, result)
            return result
        
        return wrapper
    return decorator

def get_cache_stats() -> Dict[str, Any]:
    """Retorna estatísticas de todos os caches"""
    return {
        'route_cache': route_cache.stats(),
        'alternatives_cache': alternatives_cache.stats(),
        'edge_analysis_cache': edge_analysis_cache.stats()
    }

def clear_all_caches():
    """Limpa todos os caches"""
    route_cache.clear()
    alternatives_cache.clear()
    edge_analysis_cache.clear()
