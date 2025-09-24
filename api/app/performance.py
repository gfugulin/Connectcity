"""
Módulo de métricas e otimizações de performance
"""
import time
import threading
from typing import Dict, Any, Optional
from collections import defaultdict, deque
import statistics

class PerformanceMetrics:
    """Coletor de métricas de performance"""
    
    def __init__(self):
        self.lock = threading.RLock()
        self.request_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.total_requests: Dict[str, int] = defaultdict(int)
        self.start_time = time.time()
    
    def record_request(self, endpoint: str, duration_ms: float, status_code: int):
        """Registra uma requisição"""
        with self.lock:
            self.request_times[endpoint].append(duration_ms)
            self.total_requests[endpoint] += 1
            
            if status_code >= 400:
                self.error_counts[endpoint] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de performance"""
        with self.lock:
            stats = {
                'uptime_seconds': time.time() - self.start_time,
                'endpoints': {}
            }
            
            for endpoint in self.request_times:
                times = list(self.request_times[endpoint])
                if times:
                    stats['endpoints'][endpoint] = {
                        'total_requests': self.total_requests[endpoint],
                        'error_count': self.error_counts[endpoint],
                        'error_rate': self.error_counts[endpoint] / max(self.total_requests[endpoint], 1),
                        'avg_response_time_ms': statistics.mean(times),
                        'p50_response_time_ms': statistics.median(times),
                        'p95_response_time_ms': statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times),
                        'p99_response_time_ms': statistics.quantiles(times, n=100)[98] if len(times) >= 100 else max(times),
                        'min_response_time_ms': min(times),
                        'max_response_time_ms': max(times)
                    }
            
            return stats
    
    def reset(self):
        """Reseta todas as métricas"""
        with self.lock:
            self.request_times.clear()
            self.error_counts.clear()
            self.total_requests.clear()
            self.start_time = time.time()

# Instância global de métricas
metrics = PerformanceMetrics()

def measure_performance(endpoint: str):
    """Decorator para medir performance de endpoints"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status_code = 200
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = getattr(e, 'status_code', 500)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                metrics.record_request(endpoint, duration_ms, status_code)
        
        return wrapper
    return decorator

class PerformanceOptimizer:
    """Otimizador de performance"""
    
    @staticmethod
    def optimize_graph_loading():
        """Otimizações para carregamento do grafo"""
        # Em uma implementação real, poderíamos:
        # - Usar estruturas de dados mais eficientes
        # - Implementar lazy loading
        # - Usar índices para busca rápida
        pass
    
    @staticmethod
    def optimize_route_calculation():
        """Otimizações para cálculo de rotas"""
        # Em uma implementação real, poderíamos:
        # - Implementar cache de rotas frequentes
        # - Usar algoritmos mais eficientes
        # - Paralelizar cálculos quando possível
        pass
    
    @staticmethod
    def optimize_memory_usage():
        """Otimizações de uso de memória"""
        # Em uma implementação real, poderíamos:
        # - Implementar garbage collection manual
        # - Usar estruturas de dados mais compactas
        # - Limitar tamanho de caches
        pass

def get_performance_recommendations() -> Dict[str, Any]:
    """Retorna recomendações de performance baseadas nas métricas"""
    stats = metrics.get_stats()
    recommendations = []
    
    for endpoint, data in stats['endpoints'].items():
        # Verificar tempo de resposta
        if data['p95_response_time_ms'] > 1000:
            recommendations.append({
                'endpoint': endpoint,
                'issue': 'high_response_time',
                'severity': 'high',
                'message': f'P95 response time ({data["p95_response_time_ms"]:.1f}ms) is too high',
                'suggestion': 'Consider caching or algorithm optimization'
            })
        
        # Verificar taxa de erro
        if data['error_rate'] > 0.05:  # 5%
            recommendations.append({
                'endpoint': endpoint,
                'issue': 'high_error_rate',
                'severity': 'high',
                'message': f'Error rate ({data["error_rate"]:.1%}) is too high',
                'suggestion': 'Review error handling and input validation'
            })
        
        # Verificar volume de requisições
        if data['total_requests'] > 10000:
            recommendations.append({
                'endpoint': endpoint,
                'issue': 'high_volume',
                'severity': 'medium',
                'message': f'High request volume ({data["total_requests"]} requests)',
                'suggestion': 'Consider rate limiting or load balancing'
            })
    
    return {
        'recommendations': recommendations,
        'total_recommendations': len(recommendations),
        'high_severity_count': len([r for r in recommendations if r['severity'] == 'high'])
    }
