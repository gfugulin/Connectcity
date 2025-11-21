"""
Utilitários espaciais para cálculos geográficos e índices espaciais
Otimizado para performance com grandes volumes de dados
"""
import math
import logging
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula distância em metros entre duas coordenadas usando fórmula de Haversine
    
    Args:
        lat1, lon1: Coordenadas do primeiro ponto (graus)
        lat2, lon2: Coordenadas do segundo ponto (graus)
        
    Returns:
        Distância em metros
    """
    R = 6371000  # Raio da Terra em metros
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


class SpatialIndex:
    """
    Índice espacial simples baseado em grid para busca eficiente de pontos próximos
    Otimizado para evitar comparações O(n²)
    """
    
    def __init__(self, nodes: List[Dict], grid_size_m: float = 1000):
        """
        Inicializa índice espacial
        
        Args:
            nodes: Lista de nós com 'lat' e 'lon'
            grid_size_m: Tamanho da célula do grid em metros (padrão: 1km)
        """
        self.grid_size_m = grid_size_m
        self.grid: Dict[Tuple[int, int], List[int]] = defaultdict(list)
        self.nodes = nodes
        
        # Construir grid
        for idx, node in enumerate(nodes):
            if 'lat' in node and 'lon' in node:
                cell = self._get_cell(node['lat'], node['lon'])
                self.grid[cell].append(idx)
        
        logger.info(f"Índice espacial criado: {len(self.grid)} células, {len(nodes)} nós")
    
    def _get_cell(self, lat: float, lon: float) -> Tuple[int, int]:
        """
        Converte coordenadas para célula do grid
        
        Aproximação: 1 grau ≈ 111km
        """
        # Converter para células do grid
        lat_cell = int(lat * 111000 / self.grid_size_m)
        lon_cell = int(lon * 111000 * math.cos(math.radians(lat)) / self.grid_size_m)
        return (lat_cell, lon_cell)
    
    def find_nearby_nodes(self, lat: float, lon: float, max_distance_m: float) -> List[Tuple[int, float]]:
        """
        Encontra nós próximos a um ponto
        
        Args:
            lat, lon: Coordenadas do ponto
            max_distance_m: Distância máxima em metros
            
        Returns:
            Lista de tuplas (índice_do_nó, distância_em_metros)
        """
        nearby = []
        center_cell = self._get_cell(lat, lon)
        
        # Calcular quantas células verificar (baseado na distância máxima)
        cells_to_check = max(1, int(math.ceil(max_distance_m / self.grid_size_m)))
        
        # Verificar células adjacentes
        for lat_offset in range(-cells_to_check, cells_to_check + 1):
            for lon_offset in range(-cells_to_check, cells_to_check + 1):
                cell = (center_cell[0] + lat_offset, center_cell[1] + lon_offset)
                
                if cell in self.grid:
                    for node_idx in self.grid[cell]:
                        node = self.nodes[node_idx]
                        distance = haversine_distance(
                            lat, lon,
                            node['lat'], node['lon']
                        )
                        
                        if distance <= max_distance_m:
                            nearby.append((node_idx, distance))
        
        return nearby


def create_walking_connections(
    nodes: List[Dict],
    max_distance_m: float = 500,
    max_connections_per_node: int = 10,
    walking_speed_kmh: float = 5.0,
    bidirectional: bool = True
) -> List[Dict]:
    """
    Cria conexões de caminhada entre nós próximos de forma otimizada
    
    Args:
        nodes: Lista de nós com 'id', 'lat', 'lon'
        max_distance_m: Distância máxima para criar conexão (metros)
        max_connections_per_node: Máximo de conexões por nó (para limitar complexidade)
        walking_speed_kmh: Velocidade de caminhada (km/h)
        bidirectional: Se True, cria conexões bidirecionais (padrão: True)
        
    Returns:
        Lista de arestas de caminhada
    """
    if len(nodes) == 0:
        return []
    
    logger.info(f"Criando conexões de caminhada (máx {max_distance_m}m, {max_connections_per_node} por nó)...")
    
    # Criar índice espacial
    spatial_index = SpatialIndex(nodes, grid_size_m=max_distance_m)
    
    edges = []
    edges_set = set()  # Para evitar duplicatas
    
    # Para cada nó, encontrar nós próximos
    for i, from_node in enumerate(nodes):
        if 'lat' not in from_node or 'lon' not in from_node:
            continue
        
        # Encontrar nós próximos usando índice espacial
        nearby = spatial_index.find_nearby_nodes(
            from_node['lat'], from_node['lon'],
            max_distance_m
        )
        
        # Ordenar por distância e limitar número de conexões
        nearby.sort(key=lambda x: x[1])
        nearby = nearby[:max_connections_per_node]
        
        for node_idx, distance in nearby:
            # Não criar conexão com o próprio nó
            if node_idx == i:
                continue
            
            to_node = nodes[node_idx]
            
            # Criar chave única para evitar duplicatas
            edge_key = (from_node['id'], to_node['id'])
            reverse_key = (to_node['id'], from_node['id'])
            
            # Verificar se já existe (em qualquer direção)
            if edge_key in edges_set or reverse_key in edges_set:
                continue
            
            # Calcular tempo de caminhada
            # Distância em km / velocidade em km/h * 60 min
            walking_time = (distance / 1000) / walking_speed_kmh * 60
            
            # Criar aresta (bidirecional se habilitado)
            edge1 = {
                'from': from_node['id'],
                'to': to_node['id'],
                'tempo_min': round(walking_time, 1),
                'transferencia': 0,
                'escada': 0,
                'calcada_ruim': 0,
                'risco_alag': 0,
                'modo': 'pe'
            }
            
            edges.append(edge1)
            edges_set.add(edge_key)
            
            # Criar aresta reversa se bidirecional
            if bidirectional:
                edge2 = {
                    'from': to_node['id'],
                    'to': from_node['id'],
                    'tempo_min': round(walking_time, 1),
                    'transferencia': 0,
                    'escada': 0,
                    'calcada_ruim': 0,
                    'risco_alag': 0,
                    'modo': 'pe'
                }
                edges.append(edge2)
                edges_set.add(reverse_key)
    
    logger.info(f"✅ Criadas {len(edges)} conexões de caminhada")
    return edges


def calculate_walking_time(distance_m: float, walking_speed_kmh: float = 5.0) -> float:
    """
    Calcula tempo de caminhada baseado em distância
    
    Args:
        distance_m: Distância em metros
        walking_speed_kmh: Velocidade de caminhada (km/h)
        
    Returns:
        Tempo em minutos
    """
    return (distance_m / 1000) / walking_speed_kmh * 60

