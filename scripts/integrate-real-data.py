#!/usr/bin/env python3
"""
Script para demonstrar integração com dados reais (GTFS + OpenStreetMap)
"""
import sys
import os
import asyncio
import logging
from pathlib import Path

# Adicionar o diretório pai ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from integration.data_integrator import DataIntegrator, CITY_BOUNDS, GTFS_SOURCES
from integration.gtfs_processor import GTFSProcessor
from integration.osm_processor import OSMProcessor

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def demonstrate_gtfs_integration():
    """Demonstra integração com dados GTFS"""
    print("\n🚌 === DEMONSTRAÇÃO DE INTEGRAÇÃO GTFS ===")
    
    # Exemplo com Belo Horizonte (dados públicos)
    city_name = "belo_horizonte"
    
    if city_name not in GTFS_SOURCES:
        print(f"❌ Dados GTFS não disponíveis para {city_name}")
        return
    
    try:
        print(f"📥 Baixando dados GTFS para {city_name}...")
        
        # Criar processador GTFS
        gtfs_processor = GTFSProcessor()
        
        # Baixar dados (simulação - em produção usaria URL real)
        print("⚠️  Nota: Em produção, isso baixaria dados reais de:")
        print(f"   {GTFS_SOURCES[city_name]}")
        
        # Simular processamento com dados de exemplo
        print("📊 Processando dados GTFS...")
        
        # Criar dados de exemplo
        from integration.gtfs_processor import GTFSStop, GTFSRoute, GTFSTrip, GTFSStopTime
        
        # Adicionar algumas paradas de exemplo
        stops = [
            GTFSStop("ST001", "Estação Central", -19.9167, -43.9345, "station"),
            GTFSStop("ST002", "Praça da Liberdade", -19.9317, -43.9378, "stop"),
            GTFSStop("ST003", "Mercado Central", -19.9200, -43.9400, "stop"),
            GTFSStop("ST004", "Terminal Rodoviário", -19.9100, -43.9300, "station"),
            GTFSStop("ST005", "Shopping Center", -19.9250, -43.9450, "stop")
        ]
        
        for stop in stops:
            gtfs_processor.stops[stop.stop_id] = stop
        
        # Adicionar rotas de exemplo
        routes = [
            GTFSRoute("R001", "1001", "Circular Centro", 3),  # Bus
            GTFSRoute("R002", "M1", "Metrô Linha 1", 1),      # Metro
            GTFSRoute("R003", "2001", "Expresso Norte", 3)    # Bus
        ]
        
        for route in routes:
            gtfs_processor.routes[route.route_id] = route
        
        print(f"✅ Processados {len(gtfs_processor.stops)} paradas e {len(gtfs_processor.routes)} rotas")
        
        # Converter para formato Conneccity
        nodes, edges = gtfs_processor.convert_to_conneccity_format()
        
        print(f"🔄 Convertidos para {len(nodes)} nós e {len(edges)} arestas Conneccity")
        
        # Mostrar exemplo de dados
        if nodes:
            print("\n📋 Exemplo de nó GTFS convertido:")
            print(f"   {nodes[0]}")
        
        if edges:
            print("\n🛣️  Exemplo de aresta GTFS convertida:")
            print(f"   {edges[0]}")
        
        return gtfs_processor
        
    except Exception as e:
        print(f"❌ Erro na integração GTFS: {str(e)}")
        return None

async def demonstrate_osm_integration():
    """Demonstra integração com dados OpenStreetMap"""
    print("\n🗺️  === DEMONSTRAÇÃO DE INTEGRAÇÃO OSM ===")
    
    city_name = "belo_horizonte"
    
    if city_name not in CITY_BOUNDS:
        print(f"❌ Bounds não disponíveis para {city_name}")
        return
    
    try:
        print(f"📥 Obtendo dados OSM para {city_name}...")
        print(f"📍 Bbox: {CITY_BOUNDS[city_name]}")
        
        # Criar processador OSM
        osm_processor = OSMProcessor()
        
        # Em produção, isso faria uma requisição real para Overpass API
        print("⚠️  Nota: Em produção, isso faria requisição real para Overpass API")
        print("   Exemplo de query Overpass QL:")
        print("   [out:xml][timeout:300];")
        print("   (way[\"highway\"~\"^(primary|secondary|tertiary|residential)$\"](bbox);")
        print("    node[\"public_transport\"=\"stop_position\"](bbox););")
        print("   out geom;")
        
        # Simular dados OSM
        print("📊 Simulando dados OSM...")
        
        from integration.osm_processor import OSMNode, OSMWay
        
        # Criar nós de exemplo
        nodes = [
            OSMNode("N001", -19.9167, -43.9345, {"public_transport": "stop_position", "name": "Parada Central"}),
            OSMNode("N002", -19.9317, -43.9378, {"railway": "station", "name": "Estação Liberdade"}),
            OSMNode("N003", -19.9200, -43.9400, {"highway": "bus_stop", "name": "Mercado Central"})
        ]
        
        for node in nodes:
            osm_processor.nodes[node.id] = node
        
        # Criar vias de exemplo
        ways = [
            OSMWay("W001", ["N001", "N002"], {
                "highway": "primary",
                "surface": "asphalt",
                "wheelchair": "yes",
                "smoothness": "good"
            }),
            OSMWay("W002", ["N002", "N003"], {
                "highway": "secondary",
                "surface": "concrete",
                "wheelchair": "no",
                "smoothness": "bad"
            }),
            OSMWay("W003", ["N001", "N003"], {
                "highway": "steps",
                "surface": "stone",
                "wheelchair": "no"
            })
        ]
        
        for way in ways:
            osm_processor.ways[way.id] = way
        
        print(f"✅ Processados {len(osm_processor.nodes)} nós e {len(osm_processor.ways)} vias OSM")
        
        # Executar análises
        print("\n🔍 Executando análises OSM...")
        
        accessibility = osm_processor.analyze_accessibility()
        surface_quality = osm_processor.analyze_surface_quality()
        flood_risk = osm_processor.analyze_flood_risk()
        
        print(f"♿ Acessibilidade: {accessibility['accessible_ways']} vias acessíveis")
        print(f"🛣️  Qualidade de superfície: {len(surface_quality['good_surfaces'])} vias boas")
        print(f"🌊 Risco de alagamento: {len(flood_risk['flood_prone_areas'])} áreas de risco")
        
        # Converter para formato Conneccity
        edges = osm_processor.convert_to_conneccity_edges()
        print(f"🔄 Convertidos para {len(edges)} arestas Conneccity")
        
        if edges:
            print("\n🛣️  Exemplo de aresta OSM convertida:")
            print(f"   {edges[0]}")
        
        return osm_processor
        
    except Exception as e:
        print(f"❌ Erro na integração OSM: {str(e)}")
        return None

async def demonstrate_data_integration():
    """Demonstra integração completa de dados"""
    print("\n🔗 === DEMONSTRAÇÃO DE INTEGRAÇÃO COMPLETA ===")
    
    try:
        # Criar integrador
        integrator = DataIntegrator()
        
        print("📊 Integrando dados GTFS e OSM...")
        
        # Simular integração (em produção usaria dados reais)
        city_name = "belo_horizonte"
        
        # Simular dados integrados
        from integration.data_integrator import IntegratedNode, IntegratedEdge
        
        # Criar nós integrados
        nodes = [
            IntegratedNode("INT001", "Estação Central Integrada", -19.9167, -43.9345, "metro",
                          gtfs_data={"wheelchair_accessible": True},
                          osm_data={"wheelchair": "yes"},
                          accessibility_score=0.9, flood_risk=0),
            IntegratedNode("INT002", "Parada Liberdade", -19.9317, -43.9378, "onibus",
                          gtfs_data={"wheelchair_accessible": False},
                          osm_data={"wheelchair": "no"},
                          accessibility_score=0.2, flood_risk=0),
            IntegratedNode("INT003", "Mercado Central", -19.9200, -43.9400, "onibus",
                          gtfs_data={"wheelchair_accessible": True},
                          osm_data={"surface": "asphalt"},
                          accessibility_score=0.7, flood_risk=1)
        ]
        
        for node in nodes:
            integrator.integrated_nodes[node.id] = node
        
        # Criar arestas integradas
        edges = [
            IntegratedEdge("INT001", "INT002", 5.0, 1, 0, 0, 0, "metro",
                          gtfs_data={"source": "gtfs"},
                          osm_data={"surface": "asphalt"},
                          confidence_score=0.95),
            IntegratedEdge("INT002", "INT003", 8.0, 0, 0, 1, 0, "pe",
                          gtfs_data=None,
                          osm_data={"surface": "gravel", "smoothness": "bad"},
                          confidence_score=0.8),
            IntegratedEdge("INT001", "INT003", 12.0, 0, 1, 0, 1, "pe",
                          gtfs_data=None,
                          osm_data={"highway": "steps", "flood_prone": "yes"},
                          confidence_score=0.7)
        ]
        
        integrator.integrated_edges = edges
        
        print(f"✅ Integrados {len(integrator.integrated_nodes)} nós e {len(integrator.integrated_edges)} arestas")
        
        # Mostrar resumo
        summary = integrator.get_integration_summary()
        print(f"\n📈 Resumo da integração:")
        print(f"   • Total de nós: {summary['total_nodes']}")
        print(f"   • Total de arestas: {summary['total_edges']}")
        print(f"   • Paradas acessíveis: {summary['accessible_stops']}")
        print(f"   • Áreas de risco de alagamento: {summary['flood_risk_areas']}")
        
        # Mostrar exemplos
        if integrator.integrated_nodes:
            print(f"\n📋 Exemplo de nó integrado:")
            node = list(integrator.integrated_nodes.values())[0]
            print(f"   ID: {node.id}")
            print(f"   Nome: {node.name}")
            print(f"   Tipo: {node.tipo}")
            print(f"   Score de acessibilidade: {node.accessibility_score}")
            print(f"   Risco de alagamento: {node.flood_risk}")
            print(f"   Tem dados GTFS: {node.gtfs_data is not None}")
            print(f"   Tem dados OSM: {node.osm_data is not None}")
        
        if integrator.integrated_edges:
            print(f"\n🛣️  Exemplo de aresta integrada:")
            edge = integrator.integrated_edges[0]
            print(f"   De: {edge.from_id} → Para: {edge.to_id}")
            print(f"   Tempo: {edge.tempo_min} min")
            print(f"   Modo: {edge.modo}")
            print(f"   Escada: {edge.escada}, Calçada ruim: {edge.calcada_ruim}, Risco alagamento: {edge.risco_alag}")
            print(f"   Score de confiança: {edge.confidence_score}")
        
        return integrator
        
    except Exception as e:
        print(f"❌ Erro na integração completa: {str(e)}")
        return None

async def demonstrate_api_endpoints():
    """Demonstra endpoints da API para dados reais"""
    print("\n🌐 === DEMONSTRAÇÃO DE ENDPOINTS DA API ===")
    
    print("📡 Endpoints disponíveis para dados reais:")
    print("   GET  /real-data/cities/available")
    print("   POST /real-data/integrate/{city_name}")
    print("   GET  /real-data/integration/status/{city_name}")
    print("   GET  /real-data/gtfs/stops/{city_name}")
    print("   GET  /real-data/gtfs/routes/{city_name}")
    print("   GET  /real-data/osm/analysis/{city_name}")
    print("   GET  /real-data/integrated/nodes/{city_name}")
    print("   GET  /real-data/integrated/edges/{city_name}")
    print("   GET  /real-data/accessibility/report/{city_name}")
    
    print("\n💡 Exemplos de uso:")
    print("   # Listar cidades disponíveis")
    print("   curl http://localhost:8080/real-data/cities/available")
    print()
    print("   # Integrar dados de Belo Horizonte")
    print("   curl -X POST http://localhost:8080/real-data/integrate/belo_horizonte")
    print()
    print("   # Obter paradas GTFS")
    print("   curl http://localhost:8080/real-data/gtfs/stops/belo_horizonte?limit=10")
    print()
    print("   # Relatório de acessibilidade")
    print("   curl http://localhost:8080/real-data/accessibility/report/belo_horizonte")

async def main():
    """Função principal"""
    print("🚀 === DEMONSTRAÇÃO DE INTEGRAÇÃO COM DADOS REAIS ===")
    print("   GTFS (General Transit Feed Specification)")
    print("   OpenStreetMap (OSM)")
    print("   Conneccity API")
    
    # Demonstrar integração GTFS
    gtfs_processor = await demonstrate_gtfs_integration()
    
    # Demonstrar integração OSM
    osm_processor = await demonstrate_osm_integration()
    
    # Demonstrar integração completa
    integrator = await demonstrate_data_integration()
    
    # Demonstrar endpoints da API
    await demonstrate_api_endpoints()
    
    print("\n✅ === DEMONSTRAÇÃO CONCLUÍDA ===")
    print("🎯 Próximos passos:")
    print("   1. Configurar URLs reais de dados GTFS")
    print("   2. Ajustar bounding boxes para cidades específicas")
    print("   3. Implementar cache para dados OSM")
    print("   4. Adicionar validação de dados")
    print("   5. Implementar atualização automática de dados")
    
    print("\n📚 Recursos úteis:")
    print("   • GTFS: https://gtfs.org/")
    print("   • OpenStreetMap: https://www.openstreetmap.org/")
    print("   • Overpass API: https://overpass-api.de/")
    print("   • Belo Horizonte GTFS: https://ckan.pbh.gov.br/dataset/gtfs")

if __name__ == "__main__":
    asyncio.run(main())
