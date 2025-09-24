"""
Processador de dados OpenStreetMap (OSM)
Integra dados reais de infraestrutura urbana
"""
import requests
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass
from pathlib import Path
import time

logger = logging.getLogger(__name__)

@dataclass
class OSMNode:
    """Representa um nó OSM"""
    id: str
    lat: float
    lon: float
    tags: Dict[str, str]
    elevation: Optional[float] = None

@dataclass
class OSMWay:
    """Representa uma via OSM"""
    id: str
    nodes: List[str]
    tags: Dict[str, str]
    length: Optional[float] = None

@dataclass
class OSMRelation:
    """Representa uma relação OSM"""
    id: str
    members: List[Dict[str, Any]]
    tags: Dict[str, str]

class OSMProcessor:
    """Processador principal de dados OpenStreetMap"""
    
    def __init__(self, data_dir: str = "data/osm"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.nodes: Dict[str, OSMNode] = {}
        self.ways: Dict[str, OSMWay] = {}
        self.relations: Dict[str, OSMRelation] = {}
        
    def get_bbox_data(self, bbox: Tuple[float, float, float, float], 
                     timeout: int = 300) -> str:
        """
        Obtém dados OSM de uma bounding box
        
        Args:
            bbox: (min_lon, min_lat, max_lon, max_lat)
            timeout: Timeout em segundos
            
        Returns:
            Caminho do arquivo XML baixado
        """
        try:
            min_lon, min_lat, max_lon, max_lat = bbox
            
            # URL da API Overpass
            overpass_url = "http://overpass-api.de/api/interpreter"
            
            # Query Overpass QL para obter dados relevantes
            query = f"""
            [out:xml][timeout:{timeout}];
            (
              way["highway"~"^(primary|secondary|tertiary|residential|service|footway|cycleway|steps|path)$"]({min_lat},{min_lon},{max_lat},{max_lon});
              way["public_transport"="platform"]({min_lat},{min_lon},{max_lat},{max_lat});
              way["railway"~"^(tram|subway|light_rail)$"]({min_lat},{min_lon},{max_lat},{max_lon});
              node["public_transport"="stop_position"]({min_lat},{min_lon},{max_lat},{max_lon});
              node["railway"="station"]({min_lat},{min_lon},{max_lat},{max_lon});
              node["railway"="tram_stop"]({min_lat},{min_lon},{max_lat},{max_lon});
              node["railway"="subway_entrance"]({min_lat},{min_lon},{max_lat},{max_lon});
            );
            out geom;
            """
            
            logger.info(f"Fazendo requisição para Overpass API...")
            logger.info(f"Bbox: {bbox}")
            
            response = requests.post(overpass_url, data=query, timeout=timeout)
            response.raise_for_status()
            
            # Salvar resposta
            file_path = self.data_dir / f"osm_data_{int(time.time())}.xml"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            logger.info(f"Dados OSM salvos: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Erro ao obter dados OSM: {str(e)}")
            raise
    
    def parse_osm_xml(self, xml_file: str):
        """Parse arquivo XML OSM"""
        try:
            logger.info(f"Parseando arquivo OSM: {xml_file}")
            
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Parse nós
            for node_elem in root.findall('node'):
                node = self._parse_node(node_elem)
                if node:
                    self.nodes[node.id] = node
            
            # Parse vias
            for way_elem in root.findall('way'):
                way = self._parse_way(way_elem)
                if way:
                    self.ways[way.id] = way
            
            # Parse relações
            for rel_elem in root.findall('relation'):
                relation = self._parse_relation(rel_elem)
                if relation:
                    self.relations[relation.id] = relation
            
            logger.info(f"Parseados {len(self.nodes)} nós, {len(self.ways)} vias, {len(self.relations)} relações")
            
        except Exception as e:
            logger.error(f"Erro ao parsear XML OSM: {str(e)}")
            raise
    
    def _parse_node(self, node_elem) -> Optional[OSMNode]:
        """Parse um nó OSM"""
        try:
            node_id = node_elem.get('id')
            lat = float(node_elem.get('lat'))
            lon = float(node_elem.get('lon'))
            
            # Parse tags
            tags = {}
            for tag in node_elem.findall('tag'):
                key = tag.get('k')
                value = tag.get('v')
                if key and value:
                    tags[key] = value
            
            return OSMNode(
                id=node_id,
                lat=lat,
                lon=lon,
                tags=tags
            )
            
        except Exception as e:
            logger.warning(f"Erro ao parsear nó: {str(e)}")
            return None
    
    def _parse_way(self, way_elem) -> Optional[OSMWay]:
        """Parse uma via OSM"""
        try:
            way_id = way_elem.get('id')
            
            # Parse nós da via
            nodes = []
            for nd in way_elem.findall('nd'):
                ref = nd.get('ref')
                if ref:
                    nodes.append(ref)
            
            # Parse tags
            tags = {}
            for tag in way_elem.findall('tag'):
                key = tag.get('k')
                value = tag.get('v')
                if key and value:
                    tags[key] = value
            
            return OSMWay(
                id=way_id,
                nodes=nodes,
                tags=tags
            )
            
        except Exception as e:
            logger.warning(f"Erro ao parsear via: {str(e)}")
            return None
    
    def _parse_relation(self, rel_elem) -> Optional[OSMRelation]:
        """Parse uma relação OSM"""
        try:
            rel_id = rel_elem.get('id')
            
            # Parse membros
            members = []
            for member in rel_elem.findall('member'):
                member_data = {
                    'type': member.get('type'),
                    'ref': member.get('ref'),
                    'role': member.get('role')
                }
                members.append(member_data)
            
            # Parse tags
            tags = {}
            for tag in rel_elem.findall('tag'):
                key = tag.get('k')
                value = tag.get('v')
                if key and value:
                    tags[key] = value
            
            return OSMRelation(
                id=rel_id,
                members=members,
                tags=tags
            )
            
        except Exception as e:
            logger.warning(f"Erro ao parsear relação: {str(e)}")
            return None
    
    def analyze_accessibility(self) -> Dict[str, Any]:
        """Analisa acessibilidade das vias"""
        accessibility_data = {
            'total_ways': len(self.ways),
            'accessible_ways': 0,
            'inaccessible_ways': 0,
            'unknown_accessibility': 0,
            'barriers_found': [],
            'accessibility_features': []
        }
        
        for way in self.ways.values():
            tags = way.tags
            
            # Verificar acessibilidade
            if 'wheelchair' in tags:
                if tags['wheelchair'] == 'yes':
                    accessibility_data['accessible_ways'] += 1
                elif tags['wheelchair'] == 'no':
                    accessibility_data['inaccessible_ways'] += 1
                    accessibility_data['barriers_found'].append({
                        'way_id': way.id,
                        'barrier_type': 'wheelchair',
                        'reason': tags.get('wheelchair:description', 'No description')
                    })
                else:
                    accessibility_data['unknown_accessibility'] += 1
            else:
                accessibility_data['unknown_accessibility'] += 1
            
            # Verificar características de acessibilidade
            if 'tactile_paving' in tags and tags['tactile_paving'] == 'yes':
                accessibility_data['accessibility_features'].append({
                    'way_id': way.id,
                    'feature': 'tactile_paving'
                })
            
            if 'kerb' in tags and tags['kerb'] == 'lowered':
                accessibility_data['accessibility_features'].append({
                    'way_id': way.id,
                    'feature': 'lowered_kerb'
                })
        
        return accessibility_data
    
    def analyze_surface_quality(self) -> Dict[str, Any]:
        """Analisa qualidade das superfícies"""
        surface_data = {
            'total_ways': len(self.ways),
            'surface_types': {},
            'poor_surfaces': [],
            'good_surfaces': []
        }
        
        for way in self.ways.values():
            tags = way.tags
            surface = tags.get('surface', 'unknown')
            
            # Contar tipos de superfície
            if surface not in surface_data['surface_types']:
                surface_data['surface_types'][surface] = 0
            surface_data['surface_types'][surface] += 1
            
            # Classificar qualidade
            poor_surfaces = ['dirt', 'gravel', 'grass', 'mud', 'sand']
            good_surfaces = ['asphalt', 'concrete', 'paving_stones', 'brick']
            
            if surface in poor_surfaces:
                surface_data['poor_surfaces'].append({
                    'way_id': way.id,
                    'surface': surface,
                    'highway_type': tags.get('highway', 'unknown')
                })
            elif surface in good_surfaces:
                surface_data['good_surfaces'].append({
                    'way_id': way.id,
                    'surface': surface,
                    'highway_type': tags.get('highway', 'unknown')
                })
        
        return surface_data
    
    def analyze_flood_risk(self) -> Dict[str, Any]:
        """Analisa risco de alagamento"""
        flood_data = {
            'total_ways': len(self.ways),
            'flood_prone_areas': [],
            'water_features': [],
            'elevation_data': []
        }
        
        for way in self.ways.values():
            tags = way.tags
            
            # Verificar áreas propensas a alagamento
            if 'flood_prone' in tags and tags['flood_prone'] == 'yes':
                flood_data['flood_prone_areas'].append({
                    'way_id': way.id,
                    'highway_type': tags.get('highway', 'unknown'),
                    'description': tags.get('flood_prone:description', 'No description')
                })
            
            # Verificar características de água
            if 'natural' in tags and tags['natural'] == 'water':
                flood_data['water_features'].append({
                    'way_id': way.id,
                    'water_type': tags.get('water', 'unknown')
                })
            
            # Verificar elevação
            if 'ele' in tags:
                try:
                    elevation = float(tags['ele'])
                    flood_data['elevation_data'].append({
                        'way_id': way.id,
                        'elevation': elevation
                    })
                except ValueError:
                    pass
        
        return flood_data
    
    def convert_to_conneccity_edges(self) -> List[Dict]:
        """Converte dados OSM para arestas Conneccity"""
        edges = []
        
        for way in self.ways.values():
            if len(way.nodes) < 2:
                continue
            
            # Calcular custos baseados nas características
            calcada_ruim = self._assess_surface_quality(way.tags)
            escada = 1 if way.tags.get('highway') == 'steps' else 0
            risco_alag = self._assess_flood_risk(way.tags)
            
            # Criar arestas entre nós consecutivos
            for i in range(len(way.nodes) - 1):
                from_node = way.nodes[i]
                to_node = way.nodes[i + 1]
                
                # Calcular tempo baseado no tipo de via
                tempo_min = self._calculate_travel_time(way.tags)
                
                edge = {
                    'from': from_node,
                    'to': to_node,
                    'tempo_min': tempo_min,
                    'transferencia': 0,
                    'escada': escada,
                    'calcada_ruim': calcada_ruim,
                    'risco_alag': risco_alag,
                    'modo': self._get_transport_mode(way.tags)
                }
                edges.append(edge)
        
        return edges
    
    def _assess_surface_quality(self, tags: Dict[str, str]) -> int:
        """Avalia qualidade da superfície (0=boa, 1=ruim)"""
        surface = tags.get('surface', 'unknown')
        
        poor_surfaces = ['dirt', 'gravel', 'grass', 'mud', 'sand', 'unpaved']
        if surface in poor_surfaces:
            return 1
        
        # Verificar se há problemas de manutenção
        if tags.get('smoothness') in ['bad', 'very_bad', 'horrible']:
            return 1
        
        return 0
    
    def _assess_flood_risk(self, tags: Dict[str, str]) -> int:
        """Avalia risco de alagamento (0=baixo, 1=alto)"""
        if tags.get('flood_prone') == 'yes':
            return 1
        
        # Verificar proximidade com água
        if tags.get('natural') == 'water':
            return 1
        
        # Verificar elevação baixa
        if 'ele' in tags:
            try:
                elevation = float(tags['ele'])
                if elevation < 10:  # Menos de 10m de elevação
                    return 1
            except ValueError:
                pass
        
        return 0
    
    def _calculate_travel_time(self, tags: Dict[str, str]) -> float:
        """Calcula tempo de viagem baseado no tipo de via"""
        highway_type = tags.get('highway', 'unknown')
        
        # Tempos base por tipo de via (em minutos por 100m)
        time_mapping = {
            'motorway': 0.5,
            'trunk': 0.6,
            'primary': 0.8,
            'secondary': 1.0,
            'tertiary': 1.2,
            'residential': 1.5,
            'service': 2.0,
            'footway': 2.5,
            'cycleway': 2.0,
            'steps': 4.0,
            'path': 3.0
        }
        
        base_time = time_mapping.get(highway_type, 2.0)
        
        # Ajustar por qualidade da superfície
        surface = tags.get('surface', 'unknown')
        if surface in ['dirt', 'gravel', 'mud']:
            base_time *= 1.5
        elif surface in ['asphalt', 'concrete']:
            base_time *= 0.8
        
        return base_time
    
    def _get_transport_mode(self, tags: Dict[str, str]) -> str:
        """Determina modo de transporte baseado nas tags"""
        if tags.get('public_transport') == 'platform':
            return 'onibus'
        elif tags.get('railway') in ['tram', 'light_rail']:
            return 'tram'
        elif tags.get('railway') == 'subway':
            return 'metro'
        elif tags.get('highway') == 'cycleway':
            return 'bike'
        else:
            return 'pe'
    
    def export_analysis(self, output_dir: str):
        """Exporta análises para arquivos JSON"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Análise de acessibilidade
            accessibility = self.analyze_accessibility()
            with open(output_path / "accessibility_analysis.json", 'w', encoding='utf-8') as f:
                json.dump(accessibility, f, indent=2, ensure_ascii=False)
            
            # Análise de qualidade de superfície
            surface_quality = self.analyze_surface_quality()
            with open(output_path / "surface_quality_analysis.json", 'w', encoding='utf-8') as f:
                json.dump(surface_quality, f, indent=2, ensure_ascii=False)
            
            # Análise de risco de alagamento
            flood_risk = self.analyze_flood_risk()
            with open(output_path / "flood_risk_analysis.json", 'w', encoding='utf-8') as f:
                json.dump(flood_risk, f, indent=2, ensure_ascii=False)
            
            # Arestas convertidas
            edges = self.convert_to_conneccity_edges()
            with open(output_path / "osm_edges.json", 'w', encoding='utf-8') as f:
                json.dump(edges, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Análises exportadas para: {output_path}")
            
        except Exception as e:
            logger.error(f"Erro ao exportar análises: {str(e)}")
            raise

# Coordenadas de exemplo para cidades brasileiras
CITY_BOUNDS = {
    "belo_horizonte": (-44.1, -20.0, -43.8, -19.8),
    "sao_paulo": (-46.8, -23.8, -46.3, -23.4),
    "rio_de_janeiro": (-43.4, -23.1, -43.1, -22.8),
    "porto_alegre": (-51.3, -30.2, -51.0, -30.0),
    "curitiba": (-49.4, -25.6, -49.1, -25.3)
}
