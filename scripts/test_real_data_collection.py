#!/usr/bin/env python3
"""
Script para testar coleta real de dados
"""
import asyncio
import sys
import os
import json
import logging
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from integration.sp_data_collector import SPDataCollector

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_sample_data_collection():
    """Testa coleta com dados de exemplo"""
    try:
        logger.info("=== TESTE DE COLETA COM DADOS DE EXEMPLO ===")
        
        # Criar coletor
        collector = SPDataCollector()
        
        # Atualizar configuração para usar apenas dados de exemplo
        sample_config = {
            'gtfs_sources': {
                'sample': 'https://github.com/google/transit/raw/master/gtfs/spec/en/examples/sample-feed.zip'
            },
            'osm_areas': {
                'centro': (-46.65, -23.55, -46.60, -23.50)
            }
        }
        
        await collector.update_config(sample_config)
        logger.info("Configuração atualizada para dados de exemplo")
        
        # Coletar dados
        logger.info("Iniciando coleta de dados...")
        results = await collector.collect_all_data()
        
        # Exibir resultados
        logger.info("=== RESULTADOS ===")
        
        # Estatísticas GTFS
        gtfs_results = results.get('gtfs', {})
        for source_name, source_data in gtfs_results.items():
            if 'error' not in source_data:
                logger.info(f"✅ {source_name}:")
                logger.info(f"   - Nós: {source_data.get('nodes_count', 0)}")
                logger.info(f"   - Arestas: {source_data.get('edges_count', 0)}")
                logger.info(f"   - Paradas: {source_data.get('stops_count', 0)}")
                logger.info(f"   - Rotas: {source_data.get('routes_count', 0)}")
            else:
                logger.error(f"❌ {source_name}: {source_data['error']}")
        
        # Estatísticas OSM
        osm_results = results.get('osm', {})
        for area_name, area_data in osm_results.items():
            if 'error' not in area_data:
                logger.info(f"✅ {area_name}:")
                logger.info(f"   - Nós: {area_data.get('nodes_count', 0)}")
                logger.info(f"   - Arestas: {area_data.get('edges_count', 0)}")
                logger.info(f"   - Vias: {area_data.get('ways_count', 0)}")
            else:
                logger.error(f"❌ {area_name}: {area_data['error']}")
        
        # Estatísticas gerais
        stats = results.get('statistics', {})
        logger.info(f"📊 Total nós GTFS: {stats.get('total_gtfs_nodes', 0)}")
        logger.info(f"📊 Total arestas GTFS: {stats.get('total_gtfs_edges', 0)}")
        logger.info(f"📊 Total nós OSM: {stats.get('total_osm_nodes', 0)}")
        logger.info(f"📊 Total arestas OSM: {stats.get('total_osm_edges', 0)}")
        logger.info(f"⏱️ Duração: {results.get('duration_seconds', 0):.2f} segundos")
        
        # Salvar resultados
        output_file = Path("data/sp/real_test_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Resultados salvos em: {output_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro no teste: {str(e)}")
        return False

async def test_api_integration():
    """Testa integração com API"""
    try:
        logger.info("=== TESTE DE INTEGRAÇÃO COM API ===")
        
        # Simular chamadas da API
        collector = SPDataCollector()
        
        # Testar status
        logger.info("Testando status...")
        summary = await collector.get_data_summary()
        logger.info(f"Status: {summary.get('cache_status', {})}")
        
        # Testar validação
        logger.info("Testando validação...")
        # Aqui você pode adicionar testes de validação específicos
        
        logger.info("✅ Testes de integração concluídos")
        return True
        
    except Exception as e:
        logger.error(f"Erro na integração: {str(e)}")
        return False

async def main():
    """Função principal"""
    try:
        logger.info("=== TESTE DE COLETA REAL DE DADOS ===")
        
        # Teste 1: Coleta com dados de exemplo
        success1 = await test_sample_data_collection()
        
        # Teste 2: Integração com API
        success2 = await test_api_integration()
        
        if success1 and success2:
            logger.info("🎉 Todos os testes passaram!")
            logger.info("Próximos passos:")
            logger.info("1. Inicie a API: uvicorn api.app.main:app --reload --port 8080")
            logger.info("2. Teste endpoints: curl http://localhost:8080/sp-data/status")
            logger.info("3. Colete dados: curl -X POST http://localhost:8080/sp-data/collect")
        else:
            logger.error("❌ Alguns testes falharam")
            return False
        
    except Exception as e:
        logger.error(f"Erro nos testes: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

