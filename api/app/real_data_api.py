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
