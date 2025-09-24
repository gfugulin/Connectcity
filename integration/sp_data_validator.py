#!/usr/bin/env python3
"""
Validador de dados específicos de São Paulo para Conneccity
"""
import asyncio
import json
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import aiohttp

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    """Níveis de validação"""
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"

class ValidationResult:
    """Resultado de validação"""
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.score: float = 0.0
        self.valid: bool = True
    
    def add_error(self, message: str):
        """Adiciona erro"""
        self.errors.append(message)
        self.valid = False
    
    def add_warning(self, message: str):
        """Adiciona warning"""
        self.warnings.append(message)
    
    def add_info(self, message: str):
        """Adiciona informação"""
        self.info.append(message)
    
    def calculate_score(self) -> float:
        """Calcula score de validação"""
        total_checks = len(self.errors) + len(self.warnings) + len(self.info)
        if total_checks == 0:
            return 1.0
        
        error_weight = 0.0
        warning_weight = 0.5
        info_weight = 1.0
        
        score = (
            (len(self.info) * info_weight + 
             len(self.warnings) * warning_weight + 
             len(self.errors) * error_weight) / 
            (total_checks * info_weight)
        )
        
        self.score = max(0.0, min(1.0, score))
        return self.score

@dataclass
class ValidationRule:
    """Regra de validação"""
    name: str
    description: str
    level: ValidationLevel
    weight: float = 1.0
    enabled: bool = True

@dataclass
class SPBounds:
    """Limites geográficos de São Paulo"""
    min_lat: float = -23.8
    max_lat: float = -23.4
    min_lon: float = -46.8
    max_lon: float = -46.3
    
    def contains(self, lat: float, lon: float) -> bool:
        """Verifica se coordenadas estão dentro dos limites"""
        return (self.min_lat <= lat <= self.max_lat and 
                self.min_lon <= lon <= self.max_lon)

class SPDataValidator:
    """
    Validador de dados específicos de São Paulo
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Limites de São Paulo
        self.sp_bounds = SPBounds()
        
        # Níveis de validação
        self.validation_level = ValidationLevel(
            self.config.get('validation_level', 'moderate')
        )
        
        # Regras de validação
        self.validation_rules = self._load_validation_rules()
        
        # Dados de referência
        self.reference_data = self._load_reference_data()
        
        # Configurações específicas
        self.gtfs_validation_config = {
            'min_stop_name_length': 3,
            'max_coordinate_error': 0.01,  # ~1km
            'required_stop_fields': ['stop_id', 'stop_name', 'stop_lat', 'stop_lon'],
            'required_route_fields': ['route_id', 'route_short_name', 'route_long_name']
        }
        
        self.osm_validation_config = {
            'min_way_length': 10,  # metros
            'max_way_length': 50000,  # metros
            'required_way_tags': ['highway'],
            'accessibility_tags': ['wheelchair', 'tactile_paving', 'kerb']
        }
        
        # Estatísticas
        self.validation_stats = {
            'total_validations': 0,
            'successful_validations': 0,
            'failed_validations': 0,
            'avg_score': 0.0
        }
        
        logger.info("✅ SP Data Validator inicializado")
    
    def _load_validation_rules(self) -> List[ValidationRule]:
        """Carrega regras de validação"""
        rules = [
            ValidationRule(
                name="geographic_bounds",
                description="Verifica se dados estão dentro dos limites de SP",
                level=ValidationLevel.STRICT,
                weight=2.0
            ),
            ValidationRule(
                name="data_completeness",
                description="Verifica completude dos dados obrigatórios",
                level=ValidationLevel.STRICT,
                weight=1.5
            ),
            ValidationRule(
                name="coordinate_accuracy",
                description="Verifica precisão das coordenadas",
                level=ValidationLevel.MODERATE,
                weight=1.0
            ),
            ValidationRule(
                name="accessibility_consistency",
                description="Verifica consistência dos dados de acessibilidade",
                level=ValidationLevel.MODERATE,
                weight=1.0
            ),
            ValidationRule(
                name="naming_conventions",
                description="Verifica convenções de nomenclatura",
                level=ValidationLevel.LENIENT,
                weight=0.5
            )
        ]
        
        return rules
    
    def _load_reference_data(self) -> Dict[str, Any]:
        """Carrega dados de referência"""
        return {
            'known_stops': self._load_known_stops(),
            'known_routes': self._load_known_routes(),
            'accessibility_features': self._load_accessibility_features(),
            'geographic_landmarks': self._load_geographic_landmarks()
        }
    
    def _load_known_stops(self) -> Set[str]:
        """Carrega paradas conhecidas de SP"""
        # Paradas principais de SP (exemplos)
        return {
            'Sé', 'Paulista', 'Trianon-MASP', 'Bandeira', 'Ibirapuera',
            'Vila Madalena', 'Pinheiros', 'Itaim Bibi', 'Vila Olímpia',
            'Centro', 'Liberdade', 'Bela Vista', 'Consolação', 'Higienópolis'
        }
    
    def _load_known_routes(self) -> Set[str]:
        """Carrega rotas conhecidas de SP"""
        # Rotas principais de SP (exemplos)
        return {
            '107P', '107T', '107C', '107N', '107R',  # Linha 107
            '175P', '175T', '175C', '175N', '175R',  # Linha 175
            'Metrô Linha 1', 'Metrô Linha 2', 'Metrô Linha 3',
            'Metrô Linha 4', 'Metrô Linha 5', 'CPTM'
        }
    
    def _load_accessibility_features(self) -> Set[str]:
        """Carrega características de acessibilidade"""
        return {
            'wheelchair', 'tactile_paving', 'kerb', 'ramp',
            'elevator', 'accessible_entrance', 'audio_signals'
        }
    
    def _load_geographic_landmarks(self) -> Dict[str, Tuple[float, float]]:
        """Carrega marcos geográficos de SP"""
        return {
            'centro_sp': (-23.5505, -46.6333),
            'paulista': (-23.5614, -46.6565),
            'ibirapuera': (-23.5874, -46.6576),
            'vila_madalena': (-23.5469, -46.6932),
            'pinheiros': (-23.5679, -46.6969)
        }
    
    async def validate_gtfs_data(self, gtfs_data: Dict[str, Any]) -> ValidationResult:
        """Valida dados GTFS de São Paulo"""
        logger.info("🔍 Validando dados GTFS de São Paulo...")
        result = ValidationResult()
        
        try:
            # Validar estrutura básica
            await self._validate_gtfs_structure(gtfs_data, result)
            
            # Validar paradas
            if 'stops' in gtfs_data:
                await self._validate_gtfs_stops(gtfs_data['stops'], result)
            
            # Validar rotas
            if 'routes' in gtfs_data:
                await self._validate_gtfs_routes(gtfs_data['routes'], result)
            
            # Validar viagens
            if 'trips' in gtfs_data:
                await self._validate_gtfs_trips(gtfs_data['trips'], result)
            
            # Validar horários
            if 'stop_times' in gtfs_data:
                await self._validate_gtfs_stop_times(gtfs_data['stop_times'], result)
            
            # Calcular score final
            result.calculate_score()
            
            # Atualizar estatísticas
            self._update_validation_stats(result)
            
            logger.info(f"✅ Validação GTFS concluída - Score: {result.score:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Erro na validação GTFS: {e}")
            result.add_error(f"Erro na validação GTFS: {str(e)}")
        
        return result
    
    async def validate_osm_data(self, osm_data: Dict[str, Any]) -> ValidationResult:
        """Valida dados OSM de São Paulo"""
        logger.info("🔍 Validando dados OSM de São Paulo...")
        result = ValidationResult()
        
        try:
            # Validar estrutura básica
            await self._validate_osm_structure(osm_data, result)
            
            # Validar nós
            if 'nodes' in osm_data:
                await self._validate_osm_nodes(osm_data['nodes'], result)
            
            # Validar vias
            if 'ways' in osm_data:
                await self._validate_osm_ways(osm_data['ways'], result)
            
            # Validar relações
            if 'relations' in osm_data:
                await self._validate_osm_relations(osm_data['relations'], result)
            
            # Validar acessibilidade
            await self._validate_accessibility_data(osm_data, result)
            
            # Calcular score final
            result.calculate_score()
            
            # Atualizar estatísticas
            self._update_validation_stats(result)
            
            logger.info(f"✅ Validação OSM concluída - Score: {result.score:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Erro na validação OSM: {e}")
            result.add_error(f"Erro na validação OSM: {str(e)}")
        
        return result
    
    async def validate_integrated_data(self, integrated_data: Dict[str, Any]) -> ValidationResult:
        """Valida dados integrados"""
        logger.info("🔍 Validando dados integrados...")
        result = ValidationResult()
        
        try:
            # Validar estrutura
            await self._validate_integrated_structure(integrated_data, result)
            
            # Validar nós integrados
            if 'nodes' in integrated_data:
                await self._validate_integrated_nodes(integrated_data['nodes'], result)
            
            # Validar arestas integradas
            if 'edges' in integrated_data:
                await self._validate_integrated_edges(integrated_data['edges'], result)
            
            # Validar consistência
            await self._validate_data_consistency(integrated_data, result)
            
            # Calcular score final
            result.calculate_score()
            
            # Atualizar estatísticas
            self._update_validation_stats(result)
            
            logger.info(f"✅ Validação integrada concluída - Score: {result.score:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Erro na validação integrada: {e}")
            result.add_error(f"Erro na validação integrada: {str(e)}")
        
        return result
    
    async def _validate_gtfs_structure(self, gtfs_data: Dict[str, Any], result: ValidationResult):
        """Valida estrutura dos dados GTFS"""
        required_files = ['stops', 'routes', 'trips', 'stop_times']
        
        for file_name in required_files:
            if file_name not in gtfs_data:
                result.add_error(f"Arquivo GTFS obrigatório ausente: {file_name}")
            elif not gtfs_data[file_name]:
                result.add_warning(f"Arquivo GTFS vazio: {file_name}")
            else:
                result.add_info(f"Arquivo GTFS presente: {file_name}")
    
    async def _validate_gtfs_stops(self, stops: List[Dict[str, Any]], result: ValidationResult):
        """Valida paradas GTFS"""
        if not stops:
            result.add_error("Nenhuma parada encontrada")
            return
        
        result.add_info(f"Total de paradas: {len(stops)}")
        
        valid_stops = 0
        for stop in stops:
            if self._validate_single_stop(stop, result):
                valid_stops += 1
        
        result.add_info(f"Paradas válidas: {valid_stops}/{len(stops)}")
        
        # Verificar distribuição geográfica
        await self._validate_geographic_distribution(stops, result)
    
    def _validate_single_stop(self, stop: Dict[str, Any], result: ValidationResult) -> bool:
        """Valida uma única parada"""
        is_valid = True
        
        # Verificar campos obrigatórios
        required_fields = self.gtfs_validation_config['required_stop_fields']
        for field in required_fields:
            if field not in stop or not stop[field]:
                result.add_error(f"Campo obrigatório ausente na parada {stop.get('stop_id', 'unknown')}: {field}")
                is_valid = False
        
        # Verificar coordenadas
        if 'stop_lat' in stop and 'stop_lon' in stop:
            lat, lon = float(stop['stop_lat']), float(stop['stop_lon'])
            
            if not self.sp_bounds.contains(lat, lon):
                result.add_error(f"Parada {stop.get('stop_id', 'unknown')} fora dos limites de SP: ({lat}, {lon})")
                is_valid = False
            
            # Verificar precisão das coordenadas
            if not self._validate_coordinate_precision(lat, lon):
                result.add_warning(f"Coordenadas imprecisas para parada {stop.get('stop_id', 'unknown')}")
        
        # Verificar nome da parada
        if 'stop_name' in stop:
            stop_name = stop['stop_name']
            if len(stop_name) < self.gtfs_validation_config['min_stop_name_length']:
                result.add_warning(f"Nome de parada muito curto: {stop_name}")
            
            # Verificar se é uma parada conhecida
            if any(known in stop_name for known in self.reference_data['known_stops']):
                result.add_info(f"Parada conhecida identificada: {stop_name}")
        
        return is_valid
    
    def _validate_coordinate_precision(self, lat: float, lon: float) -> bool:
        """Valida precisão das coordenadas"""
        # Verificar se coordenadas não são muito redondas (indicando imprecisão)
        lat_decimal = lat % 0.001
        lon_decimal = lon % 0.001
        
        return lat_decimal != 0.0 or lon_decimal != 0.0
    
    async def _validate_geographic_distribution(self, stops: List[Dict[str, Any]], result: ValidationResult):
        """Valida distribuição geográfica das paradas"""
        if not stops:
            return
        
        # Calcular centroide
        total_lat = sum(float(stop.get('stop_lat', 0)) for stop in stops)
        total_lon = sum(float(stop.get('stop_lon', 0)) for stop in stops)
        center_lat = total_lat / len(stops)
        center_lon = total_lon / len(stops)
        
        # Verificar se centroide está próximo ao centro de SP
        sp_center = (-23.5505, -46.6333)
        distance = self._calculate_distance(center_lat, center_lon, sp_center[0], sp_center[1])
        
        if distance > 20:  # 20km do centro
            result.add_warning(f"Distribuição geográfica suspeita - centroide a {distance:.1f}km do centro de SP")
        else:
            result.add_info(f"Distribuição geográfica adequada - centroide a {distance:.1f}km do centro de SP")
    
    async def _validate_gtfs_routes(self, routes: List[Dict[str, Any]], result: ValidationResult):
        """Valida rotas GTFS"""
        if not routes:
            result.add_error("Nenhuma rota encontrada")
            return
        
        result.add_info(f"Total de rotas: {len(routes)}")
        
        valid_routes = 0
        for route in routes:
            if self._validate_single_route(route, result):
                valid_routes += 1
        
        result.add_info(f"Rotas válidas: {valid_routes}/{len(routes)}")
    
    def _validate_single_route(self, route: Dict[str, Any], result: ValidationResult) -> bool:
        """Valida uma única rota"""
        is_valid = True
        
        # Verificar campos obrigatórios
        required_fields = self.gtfs_validation_config['required_route_fields']
        for field in required_fields:
            if field not in route or not route[field]:
                result.add_error(f"Campo obrigatório ausente na rota {route.get('route_id', 'unknown')}: {field}")
                is_valid = False
        
        # Verificar se é uma rota conhecida
        route_name = route.get('route_short_name', '') + route.get('route_long_name', '')
        if any(known in route_name for known in self.reference_data['known_routes']):
            result.add_info(f"Rota conhecida identificada: {route_name}")
        
        return is_valid
    
    async def _validate_gtfs_trips(self, trips: List[Dict[str, Any]], result: ValidationResult):
        """Valida viagens GTFS"""
        if not trips:
            result.add_warning("Nenhuma viagem encontrada")
            return
        
        result.add_info(f"Total de viagens: {len(trips)}")
    
    async def _validate_gtfs_stop_times(self, stop_times: List[Dict[str, Any]], result: ValidationResult):
        """Valida horários GTFS"""
        if not stop_times:
            result.add_warning("Nenhum horário encontrado")
            return
        
        result.add_info(f"Total de horários: {len(stop_times)}")
    
    async def _validate_osm_structure(self, osm_data: Dict[str, Any], result: ValidationResult):
        """Valida estrutura dos dados OSM"""
        if 'nodes' not in osm_data and 'ways' not in osm_data:
            result.add_error("Nenhum dado OSM encontrado (nós ou vias)")
            return
        
        if 'nodes' in osm_data:
            result.add_info(f"Total de nós OSM: {len(osm_data['nodes'])}")
        
        if 'ways' in osm_data:
            result.add_info(f"Total de vias OSM: {len(osm_data['ways'])}")
    
    async def _validate_osm_nodes(self, nodes: List[Dict[str, Any]], result: ValidationResult):
        """Valida nós OSM"""
        if not nodes:
            result.add_warning("Nenhum nó OSM encontrado")
            return
        
        valid_nodes = 0
        for node in nodes:
            if self._validate_single_osm_node(node, result):
                valid_nodes += 1
        
        result.add_info(f"Nós OSM válidos: {valid_nodes}/{len(nodes)}")
    
    def _validate_single_osm_node(self, node: Dict[str, Any], result: ValidationResult) -> bool:
        """Valida um único nó OSM"""
        is_valid = True
        
        # Verificar coordenadas
        if 'lat' in node and 'lon' in node:
            lat, lon = float(node['lat']), float(node['lon'])
            
            if not self.sp_bounds.contains(lat, lon):
                result.add_warning(f"Nó OSM {node.get('id', 'unknown')} fora dos limites de SP")
                is_valid = False
        
        return is_valid
    
    async def _validate_osm_ways(self, ways: List[Dict[str, Any]], result: ValidationResult):
        """Valida vias OSM"""
        if not ways:
            result.add_warning("Nenhuma via OSM encontrada")
            return
        
        valid_ways = 0
        for way in ways:
            if self._validate_single_osm_way(way, result):
                valid_ways += 1
        
        result.add_info(f"Vias OSM válidas: {valid_ways}/{len(ways)}")
    
    def _validate_single_osm_way(self, way: Dict[str, Any], result: ValidationResult) -> bool:
        """Valida uma única via OSM"""
        is_valid = True
        
        # Verificar tags obrigatórias
        tags = way.get('tags', {})
        required_tags = self.osm_validation_config['required_way_tags']
        
        for tag in required_tags:
            if tag not in tags:
                result.add_warning(f"Via OSM {way.get('id', 'unknown')} sem tag obrigatória: {tag}")
                is_valid = False
        
        # Verificar tags de acessibilidade
        accessibility_tags = self.osm_validation_config['accessibility_tags']
        has_accessibility = any(tag in tags for tag in accessibility_tags)
        
        if has_accessibility:
            result.add_info(f"Via OSM {way.get('id', 'unknown')} com dados de acessibilidade")
        
        return is_valid
    
    async def _validate_osm_relations(self, relations: List[Dict[str, Any]], result: ValidationResult):
        """Valida relações OSM"""
        if not relations:
            result.add_info("Nenhuma relação OSM encontrada")
            return
        
        result.add_info(f"Total de relações OSM: {len(relations)}")
    
    async def _validate_accessibility_data(self, osm_data: Dict[str, Any], result: ValidationResult):
        """Valida dados de acessibilidade"""
        accessibility_features = self.reference_data['accessibility_features']
        found_features = set()
        
        # Verificar em vias
        if 'ways' in osm_data:
            for way in osm_data['ways']:
                tags = way.get('tags', {})
                for feature in accessibility_features:
                    if feature in tags:
                        found_features.add(feature)
        
        result.add_info(f"Características de acessibilidade encontradas: {len(found_features)}")
        
        if found_features:
            result.add_info(f"Features: {', '.join(found_features)}")
        else:
            result.add_warning("Nenhuma característica de acessibilidade encontrada")
    
    async def _validate_integrated_structure(self, integrated_data: Dict[str, Any], result: ValidationResult):
        """Valida estrutura dos dados integrados"""
        required_fields = ['nodes', 'edges']
        
        for field in required_fields:
            if field not in integrated_data:
                result.add_error(f"Campo obrigatório ausente nos dados integrados: {field}")
            elif not integrated_data[field]:
                result.add_warning(f"Campo vazio nos dados integrados: {field}")
            else:
                result.add_info(f"Campo presente nos dados integrados: {field}")
    
    async def _validate_integrated_nodes(self, nodes: List[Dict[str, Any]], result: ValidationResult):
        """Valida nós integrados"""
        if not nodes:
            result.add_error("Nenhum nó integrado encontrado")
            return
        
        result.add_info(f"Total de nós integrados: {len(nodes)}")
        
        # Verificar tipos de nós
        node_types = {}
        for node in nodes:
            node_type = node.get('type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        for node_type, count in node_types.items():
            result.add_info(f"Nós do tipo {node_type}: {count}")
    
    async def _validate_integrated_edges(self, edges: List[Dict[str, Any]], result: ValidationResult):
        """Valida arestas integradas"""
        if not edges:
            result.add_error("Nenhuma aresta integrada encontrada")
            return
        
        result.add_info(f"Total de arestas integradas: {len(edges)}")
        
        # Verificar tipos de arestas
        edge_types = {}
        for edge in edges:
            edge_type = edge.get('type', 'unknown')
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
        
        for edge_type, count in edge_types.items():
            result.add_info(f"Arestas do tipo {edge_type}: {count}")
    
    async def _validate_data_consistency(self, integrated_data: Dict[str, Any], result: ValidationResult):
        """Valida consistência dos dados integrados"""
        nodes = integrated_data.get('nodes', [])
        edges = integrated_data.get('edges', [])
        
        if not nodes or not edges:
            result.add_warning("Dados insuficientes para verificar consistência")
            return
        
        # Verificar se arestas referenciam nós existentes
        node_ids = {node.get('id') for node in nodes}
        invalid_edges = 0
        
        for edge in edges:
            from_node = edge.get('from_node')
            to_node = edge.get('to_node')
            
            if from_node not in node_ids or to_node not in node_ids:
                invalid_edges += 1
        
        if invalid_edges > 0:
            result.add_warning(f"Arestas com referências inválidas: {invalid_edges}")
        else:
            result.add_info("Todas as arestas têm referências válidas")
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcula distância entre duas coordenadas (em km)"""
        R = 6371  # Raio da Terra em km
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _update_validation_stats(self, result: ValidationResult):
        """Atualiza estatísticas de validação"""
        self.validation_stats['total_validations'] += 1
        
        if result.valid:
            self.validation_stats['successful_validations'] += 1
        else:
            self.validation_stats['failed_validations'] += 1
        
        # Atualizar score médio
        total = self.validation_stats['total_validations']
        current_avg = self.validation_stats['avg_score']
        self.validation_stats['avg_score'] = (current_avg * (total - 1) + result.score) / total
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de validação"""
        return {
            'total_validations': self.validation_stats['total_validations'],
            'successful_validations': self.validation_stats['successful_validations'],
            'failed_validations': self.validation_stats['failed_validations'],
            'success_rate': (
                self.validation_stats['successful_validations'] / 
                max(1, self.validation_stats['total_validations'])
            ),
            'avg_score': self.validation_stats['avg_score'],
            'validation_level': self.validation_level.value,
            'active_rules': len([rule for rule in self.validation_rules if rule.enabled])
        }
    
    def get_validation_rules(self) -> List[Dict[str, Any]]:
        """Retorna regras de validação"""
        return [
            {
                'name': rule.name,
                'description': rule.description,
                'level': rule.level.value,
                'weight': rule.weight,
                'enabled': rule.enabled
            }
            for rule in self.validation_rules
        ]
    
    def update_validation_level(self, level: ValidationLevel):
        """Atualiza nível de validação"""
        self.validation_level = level
        logger.info(f"📝 Nível de validação atualizado para: {level.value}")
    
    def enable_validation_rule(self, rule_name: str):
        """Habilita regra de validação"""
        for rule in self.validation_rules:
            if rule.name == rule_name:
                rule.enabled = True
                logger.info(f"📝 Regra de validação habilitada: {rule_name}")
                return
        
        logger.warning(f"⚠️ Regra de validação não encontrada: {rule_name}")
    
    def disable_validation_rule(self, rule_name: str):
        """Desabilita regra de validação"""
        for rule in self.validation_rules:
            if rule.name == rule_name:
                rule.enabled = False
                logger.info(f"📝 Regra de validação desabilitada: {rule_name}")
                return
        
        logger.warning(f"⚠️ Regra de validação não encontrada: {rule_name}")
