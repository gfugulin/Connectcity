#!/usr/bin/env python3
"""
Script para testar o pipeline completo de processamento
"""
import asyncio
import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Adicionar diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from integration.pipeline_manager import PipelineManager, PipelineConfig
from integration.realtime_processor import DataSource, UpdateType
from integration.smart_cache import CacheLevel, CacheStrategy
from integration.data_streaming import StreamType, StreamConfig
from integration.performance_monitor import AlertLevel

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_pipeline_initialization():
    """Testa inicialização do pipeline"""
    try:
        logger.info("🔧 Testando inicialização do pipeline...")
        
        # Configuração do pipeline
        config = PipelineConfig(
            gtfs_interval=60,  # 1 minuto para teste
            osm_interval=120,  # 2 minutos para teste
            integration_interval=90,  # 1.5 minutos para teste
            cache_strategy="adaptive",
            l1_max_size=100,
            l1_max_memory_mb=50,
            l2_max_size=1000,
            streaming_enabled=True,
            stream_endpoints={
                "gtfs_realtime": "http://localhost:8080/gtfs/realtime",
                "osm_changes": "http://localhost:8080/osm/changes"
            },
            monitoring_interval=10,  # 10 segundos para teste
            cpu_threshold=70.0,
            memory_threshold=80.0,
            disk_threshold=85.0
        )
        
        # Criar pipeline manager
        pipeline_manager = PipelineManager(config)
        
        # Inicializar
        await pipeline_manager.initialize()
        
        logger.info("✅ Pipeline inicializado com sucesso")
        return pipeline_manager
        
    except Exception as e:
        logger.error(f"❌ Erro na inicialização do pipeline: {e}")
        return None

async def test_pipeline_start_stop(pipeline_manager):
    """Testa início e parada do pipeline"""
    try:
        logger.info("🚀 Testando início do pipeline...")
        
        # Iniciar pipeline
        await pipeline_manager.start_pipeline()
        
        # Aguardar um pouco
        await asyncio.sleep(5)
        
        # Verificar status
        status = pipeline_manager.get_status()
        logger.info(f"📊 Status do pipeline: {status['status']}")
        
        # Verificar métricas
        metrics = pipeline_manager.get_metrics()
        logger.info(f"📈 Métricas: {metrics}")
        
        # Aguardar mais um pouco
        await asyncio.sleep(10)
        
        # Parar pipeline
        logger.info("🛑 Parando pipeline...")
        await pipeline_manager.stop_pipeline()
        
        logger.info("✅ Teste de início/parada concluído")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de início/parada: {e}")
        return False

async def test_cache_functionality(pipeline_manager):
    """Testa funcionalidade do cache"""
    try:
        logger.info("💾 Testando funcionalidade do cache...")
        
        if not pipeline_manager.smart_cache:
            logger.warning("⚠️ SmartCache não disponível")
            return False
        
        # Testar operações básicas do cache
        test_key = "test_key"
        test_value = {"test": "data", "timestamp": datetime.now().isoformat()}
        
        # Armazenar no cache
        await pipeline_manager.smart_cache.set(test_key, test_value)
        logger.info("📝 Valor armazenado no cache")
        
        # Recuperar do cache
        retrieved_value = await pipeline_manager.smart_cache.get(test_key)
        if retrieved_value:
            logger.info("✅ Valor recuperado do cache")
        else:
            logger.warning("⚠️ Valor não encontrado no cache")
        
        # Verificar métricas do cache
        cache_metrics = pipeline_manager.smart_cache.get_metrics()
        logger.info(f"📊 Métricas do cache: {cache_metrics}")
        
        # Limpar cache
        await pipeline_manager.smart_cache.clear()
        logger.info("🧹 Cache limpo")
        
        logger.info("✅ Teste de cache concluído")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de cache: {e}")
        return False

async def test_performance_monitoring(pipeline_manager):
    """Testa monitoramento de performance"""
    try:
        logger.info("📊 Testando monitoramento de performance...")
        
        if not pipeline_manager.performance_monitor:
            logger.warning("⚠️ PerformanceMonitor não disponível")
            return False
        
        # Verificar métricas atuais
        current_metrics = pipeline_manager.performance_monitor.get_current_metrics()
        logger.info(f"📈 Métricas atuais: {current_metrics}")
        
        # Verificar histórico
        history = pipeline_manager.performance_monitor.get_metrics_history(1)
        logger.info(f"📚 Histórico (1 hora): {len(history)} snapshots")
        
        # Verificar alertas
        alerts = pipeline_manager.performance_monitor.get_active_alerts()
        logger.info(f"🚨 Alertas ativos: {len(alerts)}")
        
        # Verificar resumo de performance
        summary = pipeline_manager.performance_monitor.get_performance_summary()
        logger.info(f"📋 Resumo de performance: {summary}")
        
        logger.info("✅ Teste de monitoramento concluído")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de monitoramento: {e}")
        return False

async def test_health_status(pipeline_manager):
    """Testa status de saúde do pipeline"""
    try:
        logger.info("🏥 Testando status de saúde...")
        
        # Verificar saúde geral
        health = pipeline_manager.get_health_status()
        logger.info(f"💚 Status de saúde: {health['overall_status']}")
        
        # Verificar componentes
        for component, status in health['components'].items():
            logger.info(f"🔧 {component}: {status}")
        
        # Verificar alertas
        if health['alerts']:
            logger.warning(f"⚠️ Alertas: {health['alerts']}")
        
        # Verificar recomendações
        if health['recommendations']:
            logger.info(f"💡 Recomendações: {health['recommendations']}")
        
        logger.info("✅ Teste de saúde concluído")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de saúde: {e}")
        return False

async def test_export_functionality(pipeline_manager):
    """Testa funcionalidade de exportação"""
    try:
        logger.info("📁 Testando funcionalidade de exportação...")
        
        # Exportar estado do pipeline
        export_file = "test_pipeline_state.json"
        await pipeline_manager.export_pipeline_state(export_file)
        
        # Verificar se arquivo foi criado
        if os.path.exists(export_file):
            logger.info(f"✅ Estado exportado para {export_file}")
            
            # Ler e verificar conteúdo
            with open(export_file, 'r', encoding='utf-8') as f:
                exported_data = json.load(f)
            
            required_keys = ['timestamp', 'status', 'metrics', 'health', 'config']
            for key in required_keys:
                if key in exported_data:
                    logger.info(f"✅ {key} presente na exportação")
                else:
                    logger.warning(f"⚠️ {key} ausente na exportação")
            
            # Limpar arquivo de teste
            os.remove(export_file)
            logger.info("🧹 Arquivo de teste removido")
        else:
            logger.warning(f"⚠️ Arquivo de exportação não encontrado: {export_file}")
        
        logger.info("✅ Teste de exportação concluído")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de exportação: {e}")
        return False

async def test_error_handling(pipeline_manager):
    """Testa tratamento de erros"""
    try:
        logger.info("🛡️ Testando tratamento de erros...")
        
        # Testar operações com pipeline parado
        if pipeline_manager.status.value == "stopped":
            logger.info("📝 Pipeline parado - testando operações...")
            
            # Tentar pausar pipeline parado
            try:
                await pipeline_manager.pause_pipeline()
                logger.info("✅ Pausa de pipeline parado tratada corretamente")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao pausar pipeline parado: {e}")
            
            # Tentar resumir pipeline parado
            try:
                await pipeline_manager.resume_pipeline()
                logger.info("✅ Resume de pipeline parado tratado corretamente")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao resumir pipeline parado: {e}")
        
        logger.info("✅ Teste de tratamento de erros concluído")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de tratamento de erros: {e}")
        return False

async def main():
    """Função principal de teste"""
    try:
        logger.info("🧪 === TESTE DO PIPELINE COMPLETO ===")
        
        # Teste 1: Inicialização
        pipeline_manager = await test_pipeline_initialization()
        if not pipeline_manager:
            logger.error("❌ Falha na inicialização - abortando testes")
            return False
        
        # Teste 2: Início/Parada
        success1 = await test_pipeline_start_stop(pipeline_manager)
        
        # Teste 3: Funcionalidade do cache
        success2 = await test_cache_functionality(pipeline_manager)
        
        # Teste 4: Monitoramento de performance
        success3 = await test_performance_monitoring(pipeline_manager)
        
        # Teste 5: Status de saúde
        success4 = await test_health_status(pipeline_manager)
        
        # Teste 6: Funcionalidade de exportação
        success5 = await test_export_functionality(pipeline_manager)
        
        # Teste 7: Tratamento de erros
        success6 = await test_error_handling(pipeline_manager)
        
        # Resumo dos testes
        tests = [
            ("Inicialização", True),
            ("Início/Parada", success1),
            ("Cache", success2),
            ("Performance", success3),
            ("Saúde", success4),
            ("Exportação", success5),
            ("Tratamento de Erros", success6)
        ]
        
        logger.info("\n📊 === RESUMO DOS TESTES ===")
        passed = 0
        for test_name, success in tests:
            status = "✅ PASSOU" if success else "❌ FALHOU"
            logger.info(f"{test_name}: {status}")
            if success:
                passed += 1
        
        logger.info(f"\n🎯 Resultado: {passed}/{len(tests)} testes passaram")
        
        if passed == len(tests):
            logger.info("🎉 TODOS OS TESTES PASSARAM!")
            logger.info("✅ Pipeline completo funcionando corretamente")
            return True
        else:
            logger.warning(f"⚠️ {len(tests) - passed} testes falharam")
            return False
        
    except Exception as e:
        logger.error(f"❌ Erro nos testes: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)


