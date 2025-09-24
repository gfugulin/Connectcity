"""
Integrador principal de dados GTFS e OpenStreetMap
Combina dados de transporte público e infraestrutura urbana
"""
import json
import csv
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import time

from .gtfs_processor import GTFSProcessor, GTFS_SOURCES
from .osm_processor import OSMProcessor, CITY_BOUNDS

logger = logging.getLogger(__name__)

@dataclass
class IntegratedNode:
    """Nó integrado com dados GTFS e OSM"""
    id: str
    name: str
    lat: float
    lon: float
    tipo: str
    gtfs_data: Optional[Dict] = None
    osm_data: Optional[Dict] = None
    accessibility_score: float = 0.0
    flood_risk: int = 0

@dataclass
class IntegratedEdge:
    """Aresta integrada com dados GTFS e OSM"""
    from_id: str
    to_id: str
    tempo_min: float
    transferencia: int
    escada: int
    calcada_ruim: int
    risco_alag: int
    modo: str
    gtfs_data: Optional[Dict] = None
    osm_data: Optional[Dict] = None
    confidence_score: float = 1.0

class DataIntegrator:
    """Integrador principal de dados"""
    
    def __init__(self, output_dir: str = "data/integrated"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.gtfs_processor = GTFSProcessor()
        self.osm_processor = OSMProcessor()
        
        self.integrated_nodes: Dict[str, IntegratedNode] = {}
        self.integrated_edges: List[IntegratedEdge] = []
        
    def integrate_city_data(self, city_name: str, 
                           gtfs_url: Optional[str] = None,
                           bbox: Optional[Tuple[float, float, float, float]] = None) -> Dict[str, Any]:
        """
        Integra dados de uma cidade específica
        
        Args:
            city_name: Nome da cidade
            gtfs_url: URL dos dados GTFS (opcional)
            bbox: Bounding box para dados OSM (opcional)
            
        Returns:
            Estatísticas da integração
        """
        try:
            logger.info(f"Iniciando integração de dados para {city_name}")
            
            stats = {
                'city': city_name,
                'start_time': time.time(),
                'gtfs_processed': False,
                'osm_processed': False,
                'integration_completed': False,
                'nodes_count': 0,
                'edges_count': 0,
                'errors': []
            }
            
            # Processar dados GTFS
            if gtfs_url:
                try:
                    self._process_gtfs_data(city_name, gtfs_url)
                    stats['gtfs_processed'] = True
                except Exception as e:
                    error_msg = f"Erro ao processar GTFS: {str(e)}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)
            
            # Processar dados OSM
            if bbox:
                try:
                    self._process_osm_data(city_name, bbox)
                    stats['osm_processed'] = True
                except Exception as e:
                    error_msg = f"Erro ao processar OSM: {str(e)}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)
            
            # Integrar dados
            try:
                self._integrate_data()
                stats['integration_completed'] = True
                stats['nodes_count'] = len(self.integrated_nodes)
                stats['edges_count'] = len(self.integrated_edges)
            except Exception as e:
                error_msg = f"Erro na integração: {str(e)}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)
            
            stats['end_time'] = time.time()
            stats['duration_seconds'] = stats['end_time'] - stats['start_time']
            
            # Exportar dados integrados
            self._export_integrated_data()
            
            logger.info(f"Integração concluída para {city_name}: {stats['nodes_count']} nós, {stats['edges_count']} arestas")
            return stats
            
        except Exception as e:
            logger.error(f"Erro na integração de dados: {str(e)}")
            raise
    
    def _process_gtfs_data(self, city_name: str, gtfs_url: str):
        """Processa dados GTFS"""
        logger.info(f"Processando dados GTFS para {city_name}")
        
        # Baixar dados GTFS
        zip_path = self.gtfs_processor.download_gtfs_data(gtfs_url, city_name)
        
        # Extrair dados
        extract_dir = self.gtfs_processor.extract_gtfs_data(zip_path)
        
        # Carregar dados
        self.gtfs_processor.load_stops(extract_dir)
        self.gtfs_processor.load_routes(extract_dir)
        self.gtfs_processor.load_trips(extract_dir)
        self.gtfs_processor.load_stop_times(extract_dir)
        
        logger.info("Dados GTFS processados com sucesso")
    
    def _process_osm_data(self, city_name: str, bbox: Tuple[float, float, float, float]):
        """Processa dados OSM"""
        logger.info(f"Processando dados OSM para {city_name}")
        
        # Obter dados OSM
        xml_path = self.osm_processor.get_bbox_data(bbox)
        
        # Parse dados
        self.osm_processor.parse_osm_xml(xml_path)
        
        logger.info("Dados OSM processados com sucesso")
    
    def _integrate_data(self):
        """Integra dados GTFS e OSM"""
        logger.info("Integrando dados GTFS e OSM")
        
        # Integrar nós
        self._integrate_nodes()
        
        # Integrar arestas
        self._integrate_edges()
        
        # Calcular métricas de qualidade
        self._calculate_quality_metrics()
        
        logger.info("Integração de dados concluída")
    
    def _integrate_nodes(self):
        """Integra nós GTFS e OSM"""
        # Começar com nós GTFS
        for stop in self.gtfs_processor.stops.values():
            node = IntegratedNode(
                id=stop.stop_id,
                name=stop.stop_name,
                lat=stop.stop_lat,
                lon=stop.stop_lon,
                tipo=self._map_gtfs_stop_type(stop),
                gtfs_data={
                    'wheelchair_accessible': stop.wheelchair_accessible,
                    'zone_id': stop.zone_id,
                    'stop_type': stop.stop_type
                }
            )
            self.integrated_nodes[node.id] = node
        
        # Adicionar nós OSM relevantes
        for osm_node in self.osm_processor.nodes.values():
            # Verificar se é um nó de transporte público
            if self._is_transport_node(osm_node):
                node_id = f"osm_{osm_node.id}"
                
                if node_id not in self.integrated_nodes:
                    node = IntegratedNode(
                        id=node_id,
                        name=osm_node.tags.get('name', f"OSM Node {osm_node.id}"),
                        lat=osm_node.lat,
                        lon=osm_node.lon,
                        tipo=self._map_osm_node_type(osm_node),
                        osm_data=osm_node.tags
                    )
                    self.integrated_nodes[node_id] = node
    
    def _integrate_edges(self):
        """Integra arestas GTFS e OSM"""
        # Começar com arestas GTFS
        gtfs_nodes, gtfs_edges = self.gtfs_processor.convert_to_conneccity_format()
        
        for edge_data in gtfs_edges:
            edge = IntegratedEdge(
                from_id=edge_data['from'],
                to_id=edge_data['to'],
                tempo_min=edge_data['tempo_min'],
                transferencia=edge_data['transferencia'],
                escada=edge_data['escada'],
                calcada_ruim=edge_data['calcada_ruim'],
                risco_alag=edge_data['risco_alag'],
                modo=edge_data['modo'],
                gtfs_data={'source': 'gtfs'}
            )
            self.integrated_edges.append(edge)
        
        # Adicionar arestas OSM
        osm_edges = self.osm_processor.convert_to_conneccity_edges()
        
        for edge_data in osm_edges:
            # Verificar se já existe aresta similar
            if not self._edge_exists(edge_data['from'], edge_data['to']):
                edge = IntegratedEdge(
                    from_id=edge_data['from'],
                    to_id=edge_data['to'],
                    tempo_min=edge_data['tempo_min'],
                    transferencia=edge_data['transferencia'],
                    escada=edge_data['escada'],
                    calcada_ruim=edge_data['calcada_ruim'],
                    risco_alag=edge_data['risco_alag'],
                    modo=edge_data['modo'],
                    osm_data={'source': 'osm'}
                )
                self.integrated_edges.append(edge)
    
    def _calculate_quality_metrics(self):
        """Calcula métricas de qualidade dos dados integrados"""
        logger.info("Calculando métricas de qualidade")
        
        # Análise de acessibilidade OSM
        accessibility_analysis = self.osm_processor.analyze_accessibility()
        
        # Análise de qualidade de superfície
        surface_analysis = self.osm_processor.analyze_surface_quality()
        
        # Análise de risco de alagamento
        flood_analysis = self.osm_processor.analyze_flood_risk()
        
        # Aplicar métricas aos nós
        for node in self.integrated_nodes.values():
            if node.osm_data:
                # Calcular score de acessibilidade
                node.accessibility_score = self._calculate_accessibility_score(node.osm_data)
                
                # Calcular risco de alagamento
                node.flood_risk = self._calculate_flood_risk(node.osm_data)
        
        # Aplicar métricas às arestas
        for edge in self.integrated_edges:
            if edge.osm_data:
                # Ajustar custos baseados em dados OSM
                edge.calcada_ruim = self._assess_surface_quality(edge.osm_data)
                edge.risco_alag = self._assess_flood_risk(edge.osm_data)
                edge.escada = self._assess_stairs(edge.osm_data)
    
    def _map_gtfs_stop_type(self, stop) -> str:
        """Mapeia tipo de parada GTFS para tipo Conneccity"""
        mapping = {
            'stop': 'onibus',
            'station': 'metro',
            'entrance': 'acesso'
        }
        return mapping.get(stop.stop_type, 'onibus')
    
    def _map_osm_node_type(self, osm_node) -> str:
        """Mapeia tipo de nó OSM para tipo Conneccity"""
        tags = osm_node.tags
        
        if tags.get('public_transport') == 'stop_position':
            return 'onibus'
        elif tags.get('railway') == 'station':
            return 'metro'
        elif tags.get('railway') == 'tram_stop':
            return 'tram'
        elif tags.get('railway') == 'subway_entrance':
            return 'acesso'
        else:
            return 'polo'
    
    def _is_transport_node(self, osm_node) -> bool:
        """Verifica se um nó OSM é relevante para transporte"""
        tags = osm_node.tags
        
        transport_tags = [
            'public_transport',
            'railway',
            'highway'
        ]
        
        return any(tag in tags for tag in transport_tags)
    
    def _edge_exists(self, from_id: str, to_id: str) -> bool:
        """Verifica se uma aresta já existe"""
        for edge in self.integrated_edges:
            if edge.from_id == from_id and edge.to_id == to_id:
                return True
        return False
    
    def _calculate_accessibility_score(self, osm_data: Dict) -> float:
        """Calcula score de acessibilidade (0-1)"""
        score = 0.5  # Score base
        
        if osm_data.get('wheelchair') == 'yes':
            score += 0.3
        elif osm_data.get('wheelchair') == 'no':
            score -= 0.3
        
        if osm_data.get('tactile_paving') == 'yes':
            score += 0.2
        
        if osm_data.get('kerb') == 'lowered':
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_flood_risk(self, osm_data: Dict) -> int:
        """Calcula risco de alagamento (0-1)"""
        if osm_data.get('flood_prone') == 'yes':
            return 1
        
        if osm_data.get('natural') == 'water':
            return 1
        
        return 0
    
    def _assess_surface_quality(self, osm_data: Dict) -> int:
        """Avalia qualidade da superfície"""
        surface = osm_data.get('surface', 'unknown')
        poor_surfaces = ['dirt', 'gravel', 'grass', 'mud', 'sand']
        
        if surface in poor_surfaces:
            return 1
        
        if osm_data.get('smoothness') in ['bad', 'very_bad', 'horrible']:
            return 1
        
        return 0
    
    def _assess_flood_risk(self, osm_data: Dict) -> int:
        """Avalia risco de alagamento"""
        if osm_data.get('flood_prone') == 'yes':
            return 1
        
        if osm_data.get('natural') == 'water':
            return 1
        
        return 0
    
    def _assess_stairs(self, osm_data: Dict) -> int:
        """Avalia presença de escadas"""
        if osm_data.get('highway') == 'steps':
            return 1
        
        return 0
    
    def _export_integrated_data(self):
        """Exporta dados integrados para CSV"""
        try:
            # Exportar nós
            nodes_file = self.output_dir / "integrated_nodes.csv"
            with open(nodes_file, 'w', newline='', encoding='utf-8') as f:
                if self.integrated_nodes:
                    fieldnames = ['id', 'name', 'lat', 'lon', 'tipo', 'accessibility_score', 'flood_risk']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for node in self.integrated_nodes.values():
                        writer.writerow({
                            'id': node.id,
                            'name': node.name,
                            'lat': node.lat,
                            'lon': node.lon,
                            'tipo': node.tipo,
                            'accessibility_score': node.accessibility_score,
                            'flood_risk': node.flood_risk
                        })
            
            # Exportar arestas
            edges_file = self.output_dir / "integrated_edges.csv"
            with open(edges_file, 'w', newline='', encoding='utf-8') as f:
                if self.integrated_edges:
                    fieldnames = ['from', 'to', 'tempo_min', 'transferencia', 'escada', 'calcada_ruim', 'risco_alag', 'modo']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for edge in self.integrated_edges:
                        writer.writerow({
                            'from': edge.from_id,
                            'to': edge.to_id,
                            'tempo_min': edge.tempo_min,
                            'transferencia': edge.transferencia,
                            'escada': edge.escada,
                            'calcada_ruim': edge.calcada_ruim,
                            'risco_alag': edge.risco_alag,
                            'modo': edge.modo
                        })
            
            # Exportar estatísticas
            stats_file = self.output_dir / "integration_stats.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                stats = {
                    'total_nodes': len(self.integrated_nodes),
                    'total_edges': len(self.integrated_edges),
                    'gtfs_stops': len(self.gtfs_processor.stops),
                    'osm_nodes': len(self.osm_processor.nodes),
                    'osm_ways': len(self.osm_processor.ways),
                    'accessibility_analysis': self.osm_processor.analyze_accessibility(),
                    'surface_quality_analysis': self.osm_processor.analyze_surface_quality(),
                    'flood_risk_analysis': self.osm_processor.analyze_flood_risk()
                }
                json.dump(stats, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Dados integrados exportados para: {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Erro ao exportar dados integrados: {str(e)}")
            raise
    
    def get_integration_summary(self) -> Dict[str, Any]:
        """Retorna resumo da integração"""
        return {
            'total_nodes': len(self.integrated_nodes),
            'total_edges': len(self.integrated_edges),
            'gtfs_data_available': len(self.gtfs_processor.stops) > 0,
            'osm_data_available': len(self.osm_processor.nodes) > 0,
            'accessible_stops': len([n for n in self.integrated_nodes.values() if n.accessibility_score > 0.7]),
            'flood_risk_areas': len([n for n in self.integrated_nodes.values() if n.flood_risk > 0])
        }
