"""
API para integração com dados reais (GTFS + OpenStreetMap)
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Dict, List, Any, Optional, Tuple
import logging
import asyncio
from pathlib import Path

from integration.data_integrator import DataIntegrator, CITY_BOUNDS, GTFS_SOURCES
from integration.gtfs_processor import GTFSProcessor
from integration.osm_processor import OSMProcessor
from .exceptions import ConneccityException, CoreLibraryException
import os
import pandas as pd

logger = logging.getLogger(__name__)

# Router para dados reais
real_data_router = APIRouter(prefix="/real-data", tags=["Real Data Integration"])

# Instância global do integrador
data_integrator = DataIntegrator()

@real_data_router.get("/cities/available")
async def get_available_cities():
    """Retorna cidades disponíveis para integração"""
    try:
        cities = []
        
        for city_name, bbox in CITY_BOUNDS.items():
            city_info = {
                "name": city_name,
                "display_name": city_name.replace("_", " ").title(),
                "bbox": bbox,
                "gtfs_available": city_name in GTFS_SOURCES,
                "gtfs_url": GTFS_SOURCES.get(city_name)
            }
            cities.append(city_info)
        
        return {
            "cities": cities,
            "total_cities": len(cities)
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter cidades disponíveis: {str(e)}")
        raise CoreLibraryException(f"Erro ao obter cidades: {str(e)}")

@real_data_router.post("/integrate/{city_name}")
async def integrate_city_data(
    city_name: str,
    background_tasks: BackgroundTasks,
    gtfs_url: Optional[str] = None,
    bbox: Optional[List[float]] = None
):
    """Inicia integração de dados para uma cidade"""
    try:
        # Validar cidade
        if city_name not in CITY_BOUNDS:
            raise HTTPException(
                status_code=400,
                detail=f"Cidade '{city_name}' não suportada. Cidades disponíveis: {list(CITY_BOUNDS.keys())}"
            )
        
        # Usar bbox padrão se não fornecido
        if bbox is None:
            bbox = CITY_BOUNDS[city_name]
        elif len(bbox) != 4:
            raise HTTPException(
                status_code=400,
                detail="Bbox deve ter 4 valores: [min_lon, min_lat, max_lon, max_lat]"
            )
        
        # Usar URL GTFS padrão se não fornecida
        if gtfs_url is None:
            gtfs_url = GTFS_SOURCES.get(city_name)
            if not gtfs_url:
                raise HTTPException(
                    status_code=400,
                    detail=f"URL GTFS não fornecida e não disponível para {city_name}"
                )
        
        # Executar integração em background
        background_tasks.add_task(
            _run_integration_task,
            city_name,
            gtfs_url,
            tuple(bbox)
        )
        
        return {
            "message": f"Integração iniciada para {city_name}",
            "city": city_name,
            "gtfs_url": gtfs_url,
            "bbox": bbox,
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao iniciar integração: {str(e)}")
        raise CoreLibraryException(f"Erro ao iniciar integração: {str(e)}")

@real_data_router.get("/hybrid/status")
async def get_hybrid_status():
    """
    Retorna status das fontes de dados híbridas (API Olho Vivo + GTFS Local)
    """
    try:
        from integration.hybrid_data_processor import HybridDataProcessor
        import os
        
        olho_vivo_token = os.getenv(
            "OLHO_VIVO_TOKEN",
            "1abf7ba19b22829e9d95648f8affe9afaf8c64b9cbb8c8042e6b50cb5d63be81"
        )
        gtfs_dir = os.getenv("GTFS_LOCAL_DIR", "GTFS")
        
        processor = HybridDataProcessor(
            olho_vivo_token=olho_vivo_token,
            gtfs_dir=gtfs_dir if os.path.isdir(gtfs_dir) else None
        )
        
        status = processor.initialize()
        info = processor.get_data_source_info()
        
        return {
            "status": status,
            "info": info,
            "recommendation": (
                "✅ Configuração ideal: ambas as fontes disponíveis" 
                if status['olho_vivo'] and status['gtfs_local']
                else "⚠️ Recomendado ter ambas as fontes para melhor experiência"
            )
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter status híbrido: {str(e)}")
        raise CoreLibraryException(f"Erro ao obter status: {str(e)}")

@real_data_router.post("/process-local-gtfs")
async def process_local_gtfs(gtfs_dir: str = Query(..., description="Caminho do diretório com arquivos GTFS")):
    """
    Processa arquivos GTFS de um diretório local (já extraídos)
    
    Exemplo: /process-local-gtfs?gtfs_dir=GTFS
    """
    try:
        # Verificar se o diretório existe
        if not os.path.isdir(gtfs_dir):
            raise HTTPException(
                status_code=404,
                detail=f"Diretório não encontrado: {gtfs_dir}"
            )
        
        # Verificar se há arquivos GTFS essenciais
        required_files = ["stops.txt", "routes.txt", "trips.txt", "stop_times.txt"]
        missing_files = []
        for file in required_files:
            file_path = os.path.join(gtfs_dir, file)
            if not os.path.isfile(file_path):
                missing_files.append(file)
        
        if missing_files:
            raise HTTPException(
                status_code=400,
                detail=f"Arquivos GTFS essenciais não encontrados: {', '.join(missing_files)}"
            )
        
        # Processar arquivos GTFS
        gtfs_processor = GTFSProcessor()
        gtfs_processor.process_local_gtfs_directory(gtfs_dir)
        
        # Converter para formato Conneccity (retorna listas de dicionários)
        nodes_list, edges_list = gtfs_processor.convert_to_conneccity_format()
        
        # Converter para DataFrames
        nodes_df = pd.DataFrame(nodes_list)
        edges_df = pd.DataFrame(edges_list)
        
        # Salvar dados processados
        output_dir = os.path.join("data", "gtfs", "processed")
        os.makedirs(output_dir, exist_ok=True)
        
        nodes_file = os.path.join(output_dir, "nodes.csv")
        edges_file = os.path.join(output_dir, "edges.csv")
        
        nodes_df.to_csv(nodes_file, index=False)
        edges_df.to_csv(edges_file, index=False)
        
        return {
            "message": "Arquivos GTFS processados com sucesso",
            "gtfs_directory": gtfs_dir,
            "nodes_count": len(nodes_df),
            "edges_count": len(edges_df),
            "output_files": {
                "nodes": nodes_file,
                "edges": edges_file
            },
            "note": "Use /real-data/integrate para integrar com dados OSM"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar GTFS local: {str(e)}")
        raise CoreLibraryException(f"Erro ao processar GTFS local: {str(e)}")

@real_data_router.post("/export-to-main")
async def export_integrated_to_main():
    """Exporta dados integrados para nodes.csv e edges.csv principais"""
    try:
        import shutil
        from pathlib import Path
        
        integrated_nodes = Path("data/integrated/integrated_nodes.csv")
        integrated_edges = Path("data/integrated/integrated_edges.csv")
        
        main_nodes = Path("data/nodes.csv")
        main_edges = Path("data/edges.csv")
        
        if not integrated_nodes.exists() or not integrated_edges.exists():
            raise HTTPException(
                status_code=404,
                detail="Dados integrados não encontrados. Execute a integração primeiro."
            )
        
        # Criar backup dos arquivos atuais
        if main_nodes.exists():
            shutil.copy(main_nodes, Path("data/nodes.csv.backup"))
        if main_edges.exists():
            shutil.copy(main_edges, Path("data/edges.csv.backup"))
        
        # Copiar dados integrados
        shutil.copy(integrated_nodes, main_nodes)
        shutil.copy(integrated_edges, main_edges)
        
        # Contar linhas
        nodes_count = sum(1 for _ in open(main_nodes)) - 1  # -1 para header
        edges_count = sum(1 for _ in open(main_edges)) - 1
        
        return {
            "message": "Dados integrados exportados com sucesso",
            "nodes_file": str(main_nodes),
            "edges_file": str(main_edges),
            "nodes_count": nodes_count,
            "edges_count": edges_count,
            "note": "Reinicie a API para carregar os novos dados"
        }
        
    except Exception as e:
        logger.error(f"Erro ao exportar dados: {str(e)}")
        raise CoreLibraryException(f"Erro ao exportar dados: {str(e)}")

async def _run_integration_task(city_name: str, gtfs_url: str, bbox: Tuple[float, float, float, float]):
    """Executa integração em background"""
    try:
        logger.info(f"Iniciando integração em background para {city_name}")
        
        # Executar em thread separada para não bloquear
        loop = asyncio.get_event_loop()
        stats = await loop.run_in_executor(
            None,
            data_integrator.integrate_city_data,
            city_name,
            gtfs_url,
            bbox
        )
        
        logger.info(f"Integração concluída para {city_name}: {stats}")
        
    except Exception as e:
        logger.error(f"Erro na integração em background: {str(e)}")

@real_data_router.get("/integration/status/{city_name}")
async def get_integration_status(city_name: str):
    """Retorna status da integração de uma cidade"""
    try:
        # Verificar se existem dados integrados
        output_dir = Path("data/integrated")
        stats_file = output_dir / "integration_stats.json"
        
        if not stats_file.exists():
            return {
                "city": city_name,
                "status": "not_integrated",
                "message": "Dados não integrados ainda"
            }
        
        # Carregar estatísticas
        import json
        with open(stats_file, 'r', encoding='utf-8') as f:
            stats = json.load(f)
        
        return {
            "city": city_name,
            "status": "integrated",
            "stats": stats,
            "summary": data_integrator.get_integration_summary()
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter status: {str(e)}")
        raise CoreLibraryException(f"Erro ao obter status: {str(e)}")

@real_data_router.get("/gtfs/stops/{city_name}")
async def get_gtfs_stops(city_name: str, limit: int = Query(100, le=1000)):
    """Retorna paradas GTFS de uma cidade"""
    try:
        # Verificar se dados GTFS estão carregados
        if not data_integrator.gtfs_processor.stops:
            raise HTTPException(
                status_code=404,
                detail=f"Dados GTFS não carregados para {city_name}"
            )
        
        stops = []
        count = 0
        
        for stop in data_integrator.gtfs_processor.stops.values():
            if count >= limit:
                break
            
            stop_data = {
                "stop_id": stop.stop_id,
                "stop_name": stop.stop_name,
                "lat": stop.stop_lat,
                "lon": stop.stop_lon,
                "stop_type": stop.stop_type,
                "wheelchair_accessible": stop.wheelchair_accessible,
                "zone_id": stop.zone_id
            }
            stops.append(stop_data)
            count += 1
        
        return {
            "city": city_name,
            "stops": stops,
            "total_stops": len(data_integrator.gtfs_processor.stops),
            "returned_count": len(stops)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter paradas GTFS: {str(e)}")
        raise CoreLibraryException(f"Erro ao obter paradas: {str(e)}")

@real_data_router.get("/gtfs/routes/{city_name}")
async def get_gtfs_routes(city_name: str, route_type: Optional[int] = None):
    """Retorna rotas GTFS de uma cidade"""
    try:
        if not data_integrator.gtfs_processor.routes:
            raise HTTPException(
                status_code=404,
                detail=f"Dados GTFS não carregados para {city_name}"
            )
        
        routes = []
        
        for route in data_integrator.gtfs_processor.routes.values():
            if route_type is not None and route.route_type != route_type:
                continue
            
            route_data = {
                "route_id": route.route_id,
                "route_short_name": route.route_short_name,
                "route_long_name": route.route_long_name,
                "route_type": route.route_type,
                "route_color": route.route_color,
                "route_text_color": route.route_text_color
            }
            routes.append(route_data)
        
        return {
            "city": city_name,
            "routes": routes,
            "total_routes": len(routes),
            "filtered_by_type": route_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter rotas GTFS: {str(e)}")
        raise CoreLibraryException(f"Erro ao obter rotas: {str(e)}")

@real_data_router.get("/osm/analysis/{city_name}")
async def get_osm_analysis(city_name: str):
    """Retorna análises OSM de uma cidade"""
    try:
        if not data_integrator.osm_processor.nodes:
            raise HTTPException(
                status_code=404,
                detail=f"Dados OSM não carregados para {city_name}"
            )
        
        # Executar análises
        accessibility = data_integrator.osm_processor.analyze_accessibility()
        surface_quality = data_integrator.osm_processor.analyze_surface_quality()
        flood_risk = data_integrator.osm_processor.analyze_flood_risk()
        
        return {
            "city": city_name,
            "analysis": {
                "accessibility": accessibility,
                "surface_quality": surface_quality,
                "flood_risk": flood_risk
            },
            "summary": {
                "total_nodes": len(data_integrator.osm_processor.nodes),
                "total_ways": len(data_integrator.osm_processor.ways),
                "total_relations": len(data_integrator.osm_processor.relations)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter análise OSM: {str(e)}")
        raise CoreLibraryException(f"Erro ao obter análise: {str(e)}")

@real_data_router.get("/integrated/nodes/{city_name}")
async def get_integrated_nodes(
    city_name: str,
    limit: int = Query(100, le=1000),
    tipo: Optional[str] = None,
    min_accessibility: Optional[float] = None
):
    """Retorna nós integrados de uma cidade"""
    try:
        if not data_integrator.integrated_nodes:
            raise HTTPException(
                status_code=404,
                detail=f"Dados integrados não disponíveis para {city_name}"
            )
        
        nodes = []
        count = 0
        
        for node in data_integrator.integrated_nodes.values():
            if count >= limit:
                break
            
            # Aplicar filtros
            if tipo and node.tipo != tipo:
                continue
            
            if min_accessibility and node.accessibility_score < min_accessibility:
                continue
            
            node_data = {
                "id": node.id,
                "name": node.name,
                "lat": node.lat,
                "lon": node.lon,
                "tipo": node.tipo,
                "accessibility_score": node.accessibility_score,
                "flood_risk": node.flood_risk,
                "has_gtfs_data": node.gtfs_data is not None,
                "has_osm_data": node.osm_data is not None
            }
            nodes.append(node_data)
            count += 1
        
        return {
            "city": city_name,
            "nodes": nodes,
            "total_nodes": len(data_integrator.integrated_nodes),
            "returned_count": len(nodes),
            "filters": {
                "tipo": tipo,
                "min_accessibility": min_accessibility
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter nós integrados: {str(e)}")
        raise CoreLibraryException(f"Erro ao obter nós: {str(e)}")

@real_data_router.get("/integrated/edges/{city_name}")
async def get_integrated_edges(
    city_name: str,
    limit: int = Query(100, le=1000),
    modo: Optional[str] = None,
    has_barriers: Optional[bool] = None
):
    """Retorna arestas integradas de uma cidade"""
    try:
        if not data_integrator.integrated_edges:
            raise HTTPException(
                status_code=404,
                detail=f"Dados integrados não disponíveis para {city_name}"
            )
        
        edges = []
        count = 0
        
        for edge in data_integrator.integrated_edges:
            if count >= limit:
                break
            
            # Aplicar filtros
            if modo and edge.modo != modo:
                continue
            
            if has_barriers is not None:
                has_any_barrier = edge.escada > 0 or edge.calcada_ruim > 0 or edge.risco_alag > 0
                if has_barriers != has_any_barrier:
                    continue
            
            edge_data = {
                "from": edge.from_id,
                "to": edge.to_id,
                "tempo_min": edge.tempo_min,
                "transferencia": edge.transferencia,
                "escada": edge.escada,
                "calcada_ruim": edge.calcada_ruim,
                "risco_alag": edge.risco_alag,
                "modo": edge.modo,
                "confidence_score": edge.confidence_score,
                "has_gtfs_data": edge.gtfs_data is not None,
                "has_osm_data": edge.osm_data is not None
            }
            edges.append(edge_data)
            count += 1
        
        return {
            "city": city_name,
            "edges": edges,
            "total_edges": len(data_integrator.integrated_edges),
            "returned_count": len(edges),
            "filters": {
                "modo": modo,
                "has_barriers": has_barriers
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter arestas integradas: {str(e)}")
        raise CoreLibraryException(f"Erro ao obter arestas: {str(e)}")

@real_data_router.get("/accessibility/report/{city_name}")
async def get_accessibility_report(city_name: str):
    """Retorna relatório de acessibilidade de uma cidade"""
    try:
        if not data_integrator.integrated_nodes:
            raise HTTPException(
                status_code=404,
                detail=f"Dados integrados não disponíveis para {city_name}"
            )
        
        # Calcular métricas de acessibilidade
        total_nodes = len(data_integrator.integrated_nodes)
        accessible_nodes = len([n for n in data_integrator.integrated_nodes.values() if n.accessibility_score > 0.7])
        partially_accessible = len([n for n in data_integrator.integrated_nodes.values() if 0.3 <= n.accessibility_score <= 0.7])
        inaccessible_nodes = len([n for n in data_integrator.integrated_nodes.values() if n.accessibility_score < 0.3])
        
        # Análise por tipo
        type_analysis = {}
        for node in data_integrator.integrated_nodes.values():
            if node.tipo not in type_analysis:
                type_analysis[node.tipo] = {
                    'total': 0,
                    'accessible': 0,
                    'partially_accessible': 0,
                    'inaccessible': 0
                }
            
            type_analysis[node.tipo]['total'] += 1
            if node.accessibility_score > 0.7:
                type_analysis[node.tipo]['accessible'] += 1
            elif node.accessibility_score >= 0.3:
                type_analysis[node.tipo]['partially_accessible'] += 1
            else:
                type_analysis[node.tipo]['inaccessible'] += 1
        
        return {
            "city": city_name,
            "accessibility_report": {
                "overall": {
                    "total_nodes": total_nodes,
                    "accessible_nodes": accessible_nodes,
                    "partially_accessible_nodes": partially_accessible,
                    "inaccessible_nodes": inaccessible_nodes,
                    "accessibility_percentage": (accessible_nodes / total_nodes * 100) if total_nodes > 0 else 0
                },
                "by_type": type_analysis,
                "recommendations": _generate_accessibility_recommendations(type_analysis)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar relatório de acessibilidade: {str(e)}")
        raise CoreLibraryException(f"Erro ao gerar relatório: {str(e)}")

def _generate_accessibility_recommendations(type_analysis: Dict) -> List[str]:
    """Gera recomendações de acessibilidade"""
    recommendations = []
    
    for tipo, data in type_analysis.items():
        if data['total'] > 0:
            accessibility_rate = data['accessible'] / data['total']
            
            if accessibility_rate < 0.5:
                recommendations.append(
                    f"Melhorar acessibilidade em {tipo}: apenas {accessibility_rate:.1%} são acessíveis"
                )
            
            if data['inaccessible'] > data['accessible']:
                recommendations.append(
                    f"Priorizar melhorias de acessibilidade em {tipo}: {data['inaccessible']} inacessíveis vs {data['accessible']} acessíveis"
                )
    
    if not recommendations:
        recommendations.append("Níveis de acessibilidade estão adequados")
    
    return recommendations
