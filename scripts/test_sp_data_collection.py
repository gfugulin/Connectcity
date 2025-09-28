#!/usr/bin/env python3
"""
Script para testar coleta de dados de São Paulo
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

async def test_data_collection():
    """Testa coleta de dados de São Paulo"""
    try:
        logger.info("Iniciando teste de coleta de dados...")
        
        # Criar coletor
        collector = SPDataCollector()
        
        # Testar coleta de dados
        logger.info("Coletando dados...")
        results = await collector.collect_all_data()
        
        # Exibir resultados
        logger.info("=== RESULTADOS DA COLETA ===")
        
        # Estatísticas gerais
        stats = results.get('statistics', {})
        logger.info(f"Total nós GTFS: {stats.get('total_gtfs_nodes', 0)}")
        logger.info(f"Total arestas GTFS: {stats.get('total_gtfs_edges', 0)}")
        logger.info(f"Total nós OSM: {stats.get('total_osm_nodes', 0)}")
        logger.info(f"Total arestas OSM: {stats.get('total_osm_edges', 0)}")
        logger.info(f"Fontes GTFS processadas: {stats.get('gtfs_sources_processed', 0)}")
        logger.info(f"Áreas OSM processadas: {stats.get('osm_areas_processed', 0)}")
        
        # Erros
        errors = stats.get('errors', [])
        if errors:
            logger.warning("Erros encontrados:")
            for error in errors:
                logger.warning(f"  - {error}")
        
        # Duração
        duration = results.get('duration_seconds', 0)
        logger.info(f"Duração total: {duration:.2f} segundos")
        
        # Salvar resultados
        output_file = Path("data/sp/test_results.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Resultados salvos em: {output_file}")
        
        # Testar resumo
        logger.info("Obtendo resumo dos dados...")
        summary = await collector.get_data_summary()
        
        logger.info("=== RESUMO DOS DADOS ===")
        logger.info(f"Status do cache: {summary.get('cache_status', {})}")
        logger.info(f"Últimas atualizações: {summary.get('last_updates', {})}")
        logger.info(f"Contadores de dados: {summary.get('data_counts', {})}")
        
        logger.info("Teste concluído com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro no teste: {str(e)}")
        raise

async def test_configuration():
    """Testa configuração de dados"""
    try:
        logger.info("Testando configuração...")
        
        collector = SPDataCollector()
        
        # Exibir configuração atual
        logger.info("=== CONFIGURAÇÃO ATUAL ===")
        logger.info(f"Fontes GTFS: {collector.config.gtfs_sources}")
        logger.info(f"Áreas OSM: {collector.config.osm_areas}")
        logger.info(f"Intervalos de atualização: {collector.config.update_intervals}")
        logger.info(f"TTL do cache: {collector.config.cache_ttl}")
        
        # Testar atualização de configuração
        logger.info("Testando atualização de configuração...")
        
        new_config = {
            'update_intervals': {
                'gtfs': 1800,  # 30 minutos
                'osm': 43200,   # 12 horas
                'integration': 900  # 15 minutos
            }
        }
        
        await collector.update_config(new_config)
        logger.info("Configuração atualizada com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro no teste de configuração: {str(e)}")
        raise

async def test_cache_management():
    """Testa gerenciamento de cache"""
    try:
        logger.info("Testando gerenciamento de cache...")
        
        collector = SPDataCollector()
        
        # Limpar cache
        await collector.clear_cache()
        logger.info("Cache limpo")
        
        # Verificar status do cache
        summary = await collector.get_data_summary()
        logger.info(f"Status do cache após limpeza: {summary.get('cache_status', {})}")
        
    except Exception as e:
        logger.error(f"Erro no teste de cache: {str(e)}")
        raise

async def main():
    """Função principal"""
    try:
        logger.info("=== TESTE DE COLETA DE DADOS DE SÃO PAULO ===")
        
        # Teste 1: Configuração
        await test_configuration()
        
        # Teste 2: Gerenciamento de cache
        await test_cache_management()
        
        # Teste 3: Coleta de dados (comentado para evitar downloads desnecessários)
        # await test_data_collection()
        
        logger.info("Todos os testes concluídos com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro nos testes: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

