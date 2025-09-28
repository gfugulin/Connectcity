#!/usr/bin/env python3
"""
Script de configuração para dados de São Paulo
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

async def setup_directories():
    """Cria diretórios necessários"""
    try:
        logger.info("Criando diretórios...")
        
        directories = [
            "data/sp/gtfs",
            "data/sp/osm", 
            "data/sp/integrated",
            "config",
            "logs"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"Diretório criado: {directory}")
        
        logger.info("Diretórios criados com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro ao criar diretórios: {str(e)}")
        raise

async def setup_configuration():
    """Configura dados de São Paulo"""
    try:
        logger.info("Configurando dados de São Paulo...")
        
        # Criar coletor
        collector = SPDataCollector()
        
        # Exibir configuração atual
        logger.info("=== CONFIGURAÇÃO ATUAL ===")
        logger.info(f"Fontes GTFS: {list(collector.config.gtfs_sources.keys())}")
        logger.info(f"Áreas OSM: {list(collector.config.osm_areas.keys())}")
        logger.info(f"Intervalos de atualização: {collector.config.update_intervals}")
        logger.info(f"TTL do cache: {collector.config.cache_ttl}")
        
        # Verificar se configuração está correta
        if not collector.config.gtfs_sources:
            logger.warning("Nenhuma fonte GTFS configurada!")
            return False
        
        if not collector.config.osm_areas:
            logger.warning("Nenhuma área OSM configurada!")
            return False
        
        logger.info("Configuração válida!")
        return True
        
    except Exception as e:
        logger.error(f"Erro na configuração: {str(e)}")
        return False

async def test_connections():
    """Testa conexões com fontes de dados"""
    try:
        logger.info("Testando conexões...")
        
        collector = SPDataCollector()
        
        # Testar conexões GTFS
        logger.info("Testando fontes GTFS...")
        for source_name, url in collector.config.gtfs_sources.items():
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.head(url, timeout=10) as response:
                        if response.status == 200:
                            logger.info(f"✅ {source_name}: OK")
                        else:
                            logger.warning(f"⚠️ {source_name}: HTTP {response.status}")
            except Exception as e:
                logger.error(f"❌ {source_name}: {str(e)}")
        
        # Testar conexão OSM
        logger.info("Testando conexão OSM...")
        try:
            import aiohttp
            overpass_url = "http://overpass-api.de/api/interpreter"
            async with aiohttp.ClientSession() as session:
                async with session.head(overpass_url, timeout=10) as response:
                    if response.status == 200:
                        logger.info("✅ OSM Overpass: OK")
                    else:
                        logger.warning(f"⚠️ OSM Overpass: HTTP {response.status}")
        except Exception as e:
            logger.error(f"❌ OSM Overpass: {str(e)}")
        
        logger.info("Teste de conexões concluído!")
        
    except Exception as e:
        logger.error(f"Erro no teste de conexões: {str(e)}")
        raise

async def create_sample_data():
    """Cria dados de exemplo para teste"""
    try:
        logger.info("Criando dados de exemplo...")
        
        # Dados de exemplo para São Paulo
        sample_nodes = [
            {
                "id": "sp_centro_1",
                "name": "Estação Sé",
                "lat": -23.5505,
                "lon": -46.6333,
                "tipo": "metro"
            },
            {
                "id": "sp_centro_2", 
                "name": "Estação Paulista",
                "lat": -23.5615,
                "lon": -46.6565,
                "tipo": "metro"
            },
            {
                "id": "sp_centro_3",
                "name": "Terminal Bandeira",
                "lat": -23.5505,
                "lon": -46.6333,
                "tipo": "onibus"
            }
        ]
        
        sample_edges = [
            {
                "from": "sp_centro_1",
                "to": "sp_centro_2",
                "tempo_min": 5.0,
                "transferencia": 0,
                "escada": 0,
                "calcada_ruim": 0,
                "risco_alag": 0,
                "modo": "metro"
            },
            {
                "from": "sp_centro_2",
                "to": "sp_centro_3",
                "tempo_min": 3.0,
                "transferencia": 1,
                "escada": 0,
                "calcada_ruim": 1,
                "risco_alag": 0,
                "modo": "pe"
            }
        ]
        
        # Salvar dados de exemplo
        sample_dir = Path("data/sp/sample")
        sample_dir.mkdir(parents=True, exist_ok=True)
        
        # Salvar nós
        nodes_file = sample_dir / "nodes.csv"
        with open(nodes_file, 'w', newline='', encoding='utf-8') as f:
            import csv
            if sample_nodes:
                writer = csv.DictWriter(f, fieldnames=sample_nodes[0].keys())
                writer.writeheader()
                writer.writerows(sample_nodes)
        
        # Salvar arestas
        edges_file = sample_dir / "edges.csv"
        with open(edges_file, 'w', newline='', encoding='utf-8') as f:
            import csv
            if sample_edges:
                writer = csv.DictWriter(f, fieldnames=sample_edges[0].keys())
                writer.writeheader()
                writer.writerows(sample_edges)
        
        logger.info(f"Dados de exemplo criados em: {sample_dir}")
        
    except Exception as e:
        logger.error(f"Erro ao criar dados de exemplo: {str(e)}")
        raise

async def main():
    """Função principal"""
    try:
        logger.info("=== CONFIGURAÇÃO DE DADOS DE SÃO PAULO ===")
        
        # Passo 1: Criar diretórios
        await setup_directories()
        
        # Passo 2: Configurar dados
        config_ok = await setup_configuration()
        if not config_ok:
            logger.error("Configuração inválida!")
            return
        
        # Passo 3: Testar conexões
        await test_connections()
        
        # Passo 4: Criar dados de exemplo
        await create_sample_data()
        
        logger.info("=== CONFIGURAÇÃO CONCLUÍDA ===")
        logger.info("Próximos passos:")
        logger.info("1. Execute: python scripts/test_sp_data_collection.py")
        logger.info("2. Teste a API: curl http://localhost:8080/sp-data/status")
        logger.info("3. Colete dados: curl -X POST http://localhost:8080/sp-data/collect")
        
    except Exception as e:
        logger.error(f"Erro na configuração: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

