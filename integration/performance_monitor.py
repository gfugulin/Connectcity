#!/usr/bin/env python3
"""
Sistema de monitoramento de performance para Conneccity
"""
import asyncio
import json
import logging
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import statistics

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Tipos de métricas"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    CACHE = "cache"
    API = "api"
    DATABASE = "database"
    CUSTOM = "custom"

class AlertLevel(Enum):
    """Níveis de alerta"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Metric:
    """Métrica individual"""
    name: str
    value: float
    timestamp: datetime
    metric_type: MetricType
    unit: str = ""
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class Alert:
    """Alerta de performance"""
    level: AlertLevel
    message: str
    metric_name: str
    current_value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False

@dataclass
class PerformanceSnapshot:
    """Snapshot de performance"""
    timestamp: datetime
    metrics: Dict[str, Metric]
    alerts: List[Alert]
    summary: Dict[str, Any]

class PerformanceMonitor:
    """
    Sistema de monitoramento de performance em tempo real
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Configurações
        self.monitoring_interval = config.get('monitoring_interval', 30)  # 30 segundos
        self.retention_hours = config.get('retention_hours', 24)  # 24 horas
        self.alert_cooldown = config.get('alert_cooldown', 300)  # 5 minutos
        
        # Armazenamento
        self.metrics_history: List[PerformanceSnapshot] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_callbacks: List[Callable] = []
        
        # Thresholds
        self.thresholds = {
            'cpu_usage': config.get('cpu_threshold', 80.0),
            'memory_usage': config.get('memory_threshold', 85.0),
            'disk_usage': config.get('disk_threshold', 90.0),
            'response_time': config.get('response_time_threshold', 5.0),
            'error_rate': config.get('error_rate_threshold', 5.0)
        }
        
        # Métricas customizadas
        self.custom_metrics: Dict[str, float] = {}
        
        # Status
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        logger.info("✅ Performance Monitor inicializado")
    
    async def start_monitoring(self):
        """Inicia o monitoramento"""
        if self.is_monitoring:
            logger.warning("⚠️ Monitoramento já está ativo")
            return
        
        logger.info("🚀 Iniciando monitoramento de performance...")
        self.is_monitoring = True
        
        # Iniciar tarefa de monitoramento
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("✅ Monitoramento de performance iniciado")
    
    async def stop_monitoring(self):
        """Para o monitoramento"""
        if not self.is_monitoring:
            logger.warning("⚠️ Monitoramento não está ativo")
            return
        
        logger.info("🛑 Parando monitoramento de performance...")
        self.is_monitoring = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("✅ Monitoramento de performance parado")
    
    async def _monitoring_loop(self):
        """Loop principal de monitoramento"""
        while self.is_monitoring:
            try:
                # Coletar métricas
                snapshot = await self._collect_metrics()
                
                # Verificar alertas
                await self._check_alerts(snapshot)
                
                # Armazenar snapshot
                self.metrics_history.append(snapshot)
                
                # Limpar histórico antigo
                await self._cleanup_history()
                
                # Aguardar próximo ciclo
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"❌ Erro no loop de monitoramento: {e}")
                await asyncio.sleep(60)  # Aguardar 1 minuto antes de tentar novamente
    
    async def _collect_metrics(self) -> PerformanceSnapshot:
        """Coleta métricas do sistema"""
        timestamp = datetime.now()
        metrics = {}
        alerts = []
        
        try:
            # Métricas de CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics['cpu_usage'] = Metric(
                name='cpu_usage',
                value=cpu_percent,
                timestamp=timestamp,
                metric_type=MetricType.CPU,
                unit='%'
            )
            
            # Métricas de memória
            memory = psutil.virtual_memory()
            metrics['memory_usage'] = Metric(
                name='memory_usage',
                value=memory.percent,
                timestamp=timestamp,
                metric_type=MetricType.MEMORY,
                unit='%'
            )
            
            metrics['memory_available'] = Metric(
                name='memory_available',
                value=memory.available / (1024**3),  # GB
                timestamp=timestamp,
                metric_type=MetricType.MEMORY,
                unit='GB'
            )
            
            # Métricas de disco
            disk = psutil.disk_usage('/')
            metrics['disk_usage'] = Metric(
                name='disk_usage',
                value=(disk.used / disk.total) * 100,
                timestamp=timestamp,
                metric_type=MetricType.DISK,
                unit='%'
            )
            
            metrics['disk_free'] = Metric(
                name='disk_free',
                value=disk.free / (1024**3),  # GB
                timestamp=timestamp,
                metric_type=MetricType.DISK,
                unit='GB'
            )
            
            # Métricas de rede
            network = psutil.net_io_counters()
            metrics['network_bytes_sent'] = Metric(
                name='network_bytes_sent',
                value=network.bytes_sent,
                timestamp=timestamp,
                metric_type=MetricType.NETWORK,
                unit='bytes'
            )
            
            metrics['network_bytes_recv'] = Metric(
                name='network_bytes_recv',
                value=network.bytes_recv,
                timestamp=timestamp,
                metric_type=MetricType.NETWORK,
                unit='bytes'
            )
            
            # Métricas customizadas
            for name, value in self.custom_metrics.items():
                metrics[f'custom_{name}'] = Metric(
                    name=f'custom_{name}',
                    value=value,
                    timestamp=timestamp,
                    metric_type=MetricType.CUSTOM,
                    unit=''
                )
            
            # Calcular resumo
            summary = await self._calculate_summary(metrics)
            
            return PerformanceSnapshot(
                timestamp=timestamp,
                metrics=metrics,
                alerts=alerts,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"❌ Erro ao coletar métricas: {e}")
            return PerformanceSnapshot(
                timestamp=timestamp,
                metrics={},
                alerts=[],
                summary={}
            )
    
    async def _calculate_summary(self, metrics: Dict[str, Metric]) -> Dict[str, Any]:
        """Calcula resumo das métricas"""
        summary = {
            'total_metrics': len(metrics),
            'cpu_usage': metrics.get('cpu_usage', {}).get('value', 0),
            'memory_usage': metrics.get('memory_usage', {}).get('value', 0),
            'disk_usage': metrics.get('disk_usage', {}).get('value', 0),
            'network_activity': (
                metrics.get('network_bytes_sent', {}).get('value', 0) +
                metrics.get('network_bytes_recv', {}).get('value', 0)
            ),
            'health_score': 0.0
        }
        
        # Calcular score de saúde
        health_factors = []
        
        if 'cpu_usage' in metrics:
            cpu_usage = metrics['cpu_usage'].value
            health_factors.append(max(0, 100 - cpu_usage) / 100)
        
        if 'memory_usage' in metrics:
            memory_usage = metrics['memory_usage'].value
            health_factors.append(max(0, 100 - memory_usage) / 100)
        
        if 'disk_usage' in metrics:
            disk_usage = metrics['disk_usage'].value
            health_factors.append(max(0, 100 - disk_usage) / 100)
        
        if health_factors:
            summary['health_score'] = sum(health_factors) / len(health_factors)
        
        return summary
    
    async def _check_alerts(self, snapshot: PerformanceSnapshot):
        """Verifica alertas de performance"""
        current_time = datetime.now()
        
        # Verificar CPU
        if 'cpu_usage' in snapshot.metrics:
            cpu_usage = snapshot.metrics['cpu_usage'].value
            if cpu_usage > self.thresholds['cpu_usage']:
                await self._trigger_alert(
                    'cpu_usage',
                    cpu_usage,
                    self.thresholds['cpu_usage'],
                    AlertLevel.WARNING,
                    f"CPU usage is {cpu_usage:.1f}% (threshold: {self.thresholds['cpu_usage']}%)"
                )
        
        # Verificar memória
        if 'memory_usage' in snapshot.metrics:
            memory_usage = snapshot.metrics['memory_usage'].value
            if memory_usage > self.thresholds['memory_usage']:
                await self._trigger_alert(
                    'memory_usage',
                    memory_usage,
                    self.thresholds['memory_usage'],
                    AlertLevel.WARNING,
                    f"Memory usage is {memory_usage:.1f}% (threshold: {self.thresholds['memory_usage']}%)"
                )
        
        # Verificar disco
        if 'disk_usage' in snapshot.metrics:
            disk_usage = snapshot.metrics['disk_usage'].value
            if disk_usage > self.thresholds['disk_usage']:
                await self._trigger_alert(
                    'disk_usage',
                    disk_usage,
                    self.thresholds['disk_usage'],
                    AlertLevel.ERROR,
                    f"Disk usage is {disk_usage:.1f}% (threshold: {self.thresholds['disk_usage']}%)"
                )
        
        # Verificar score de saúde
        health_score = snapshot.summary.get('health_score', 0)
        if health_score < 0.5:
            await self._trigger_alert(
                'health_score',
                health_score,
                0.5,
                AlertLevel.CRITICAL,
                f"System health score is {health_score:.2f} (threshold: 0.5)"
            )
    
    async def _trigger_alert(self, metric_name: str, current_value: float, threshold: float, 
                           level: AlertLevel, message: str):
        """Dispara um alerta"""
        alert_key = f"{metric_name}_{level.value}"
        current_time = datetime.now()
        
        # Verificar cooldown
        if alert_key in self.active_alerts:
            last_alert = self.active_alerts[alert_key]
            if (current_time - last_alert.timestamp).total_seconds() < self.alert_cooldown:
                return
        
        # Criar alerta
        alert = Alert(
            level=level,
            message=message,
            metric_name=metric_name,
            current_value=current_value,
            threshold=threshold,
            timestamp=current_time
        )
        
        # Armazenar alerta
        self.active_alerts[alert_key] = alert
        
        # Notificar callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"❌ Erro ao notificar alerta: {e}")
        
        logger.warning(f"🚨 {level.value.upper()}: {message}")
    
    def add_alert_callback(self, callback: Callable):
        """Adiciona callback para alertas"""
        self.alert_callbacks.append(callback)
        logger.info("📝 Callback de alerta adicionado")
    
    def remove_alert_callback(self, callback: Callable):
        """Remove callback de alertas"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
            logger.info("📝 Callback de alerta removido")
    
    def set_custom_metric(self, name: str, value: float):
        """Define métrica customizada"""
        self.custom_metrics[name] = value
        logger.debug(f"📊 Métrica customizada {name} = {value}")
    
    def get_custom_metric(self, name: str) -> Optional[float]:
        """Recupera métrica customizada"""
        return self.custom_metrics.get(name)
    
    async def _cleanup_history(self):
        """Limpa histórico antigo"""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        # Remover snapshots antigos
        self.metrics_history = [
            snapshot for snapshot in self.metrics_history
            if snapshot.timestamp > cutoff_time
        ]
        
        # Remover alertas antigos
        old_alerts = []
        for key, alert in self.active_alerts.items():
            if (datetime.now() - alert.timestamp).total_seconds() > 3600:  # 1 hora
                old_alerts.append(key)
        
        for key in old_alerts:
            del self.active_alerts[key]
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Retorna métricas atuais"""
        if not self.metrics_history:
            return {}
        
        latest_snapshot = self.metrics_history[-1]
        return {
            'timestamp': latest_snapshot.timestamp.isoformat(),
            'metrics': {
                name: {
                    'value': metric.value,
                    'unit': metric.unit,
                    'type': metric.metric_type.value
                }
                for name, metric in latest_snapshot.metrics.items()
            },
            'summary': latest_snapshot.summary,
            'alerts_count': len(latest_snapshot.alerts)
        }
    
    def get_metrics_history(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Retorna histórico de métricas"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        history = []
        for snapshot in self.metrics_history:
            if snapshot.timestamp > cutoff_time:
                history.append({
                    'timestamp': snapshot.timestamp.isoformat(),
                    'metrics': {
                        name: {
                            'value': metric.value,
                            'unit': metric.unit
                        }
                        for name, metric in snapshot.metrics.items()
                    },
                    'summary': snapshot.summary
                })
        
        return history
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Retorna alertas ativos"""
        return [
            {
                'level': alert.level.value,
                'message': alert.message,
                'metric_name': alert.metric_name,
                'current_value': alert.current_value,
                'threshold': alert.threshold,
                'timestamp': alert.timestamp.isoformat()
            }
            for alert in self.active_alerts.values()
        ]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Retorna resumo de performance"""
        if not self.metrics_history:
            return {}
        
        # Calcular estatísticas dos últimos snapshots
        recent_snapshots = self.metrics_history[-10:]  # Últimos 10 snapshots
        
        cpu_values = []
        memory_values = []
        disk_values = []
        health_scores = []
        
        for snapshot in recent_snapshots:
            if 'cpu_usage' in snapshot.metrics:
                cpu_values.append(snapshot.metrics['cpu_usage'].value)
            if 'memory_usage' in snapshot.metrics:
                memory_values.append(snapshot.metrics['memory_usage'].value)
            if 'disk_usage' in snapshot.metrics:
                disk_values.append(snapshot.metrics['disk_usage'].value)
            if 'health_score' in snapshot.summary:
                health_scores.append(snapshot.summary['health_score'])
        
        return {
            'monitoring_active': self.is_monitoring,
            'total_snapshots': len(self.metrics_history),
            'active_alerts': len(self.active_alerts),
            'cpu_stats': {
                'current': cpu_values[-1] if cpu_values else 0,
                'average': statistics.mean(cpu_values) if cpu_values else 0,
                'max': max(cpu_values) if cpu_values else 0,
                'min': min(cpu_values) if cpu_values else 0
            },
            'memory_stats': {
                'current': memory_values[-1] if memory_values else 0,
                'average': statistics.mean(memory_values) if memory_values else 0,
                'max': max(memory_values) if memory_values else 0,
                'min': min(memory_values) if memory_values else 0
            },
            'disk_stats': {
                'current': disk_values[-1] if disk_values else 0,
                'average': statistics.mean(disk_values) if disk_values else 0,
                'max': max(disk_values) if disk_values else 0,
                'min': min(disk_values) if disk_values else 0
            },
            'health_stats': {
                'current': health_scores[-1] if health_scores else 0,
                'average': statistics.mean(health_scores) if health_scores else 0,
                'max': max(health_scores) if health_scores else 0,
                'min': min(health_scores) if health_scores else 0
            },
            'thresholds': self.thresholds
        }
    
    def export_metrics(self, file_path: str, hours: int = 24):
        """Exporta métricas para arquivo"""
        try:
            history = self.get_metrics_history(hours)
            
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'hours_covered': hours,
                'total_snapshots': len(history),
                'metrics_history': history,
                'active_alerts': self.get_active_alerts(),
                'performance_summary': self.get_performance_summary()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📁 Métricas exportadas para {file_path}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao exportar métricas: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status do monitor"""
        return {
            'is_monitoring': self.is_monitoring,
            'monitoring_interval': self.monitoring_interval,
            'retention_hours': self.retention_hours,
            'total_snapshots': len(self.metrics_history),
            'active_alerts': len(self.active_alerts),
            'custom_metrics_count': len(self.custom_metrics),
            'alert_callbacks': len(self.alert_callbacks),
            'thresholds': self.thresholds
        }
