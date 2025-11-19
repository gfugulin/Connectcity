"""
Processador de dados GTFS (General Transit Feed Specification)
Integra dados reais de transporte público
"""
import csv
import zipfile
import requests
import os
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class GTFSStop:
    """Representa uma parada de transporte público"""
    stop_id: str
    stop_name: str
    stop_lat: float
    stop_lon: float
    stop_type: str = "bus"  # bus, metro, train
    wheelchair_accessible: bool = False
    zone_id: Optional[str] = None

@dataclass
class GTFSRoute:
    """Representa uma rota de transporte público"""
    route_id: str
    route_short_name: str
    route_long_name: str
    route_type: int  # 0=tram, 1=subway, 3=bus, etc.
    route_color: Optional[str] = None
    route_text_color: Optional[str] = None

@dataclass
class GTFSTrip:
    """Representa uma viagem específica"""
    trip_id: str
    route_id: str
    service_id: str
    trip_headsign: Optional[str] = None
    direction_id: Optional[int] = None
    wheelchair_accessible: bool = False

@dataclass
class GTFSStopTime:
    """Representa horário de parada"""
    trip_id: str
    stop_id: str
    arrival_time: str
    departure_time: str
    stop_sequence: int
    pickup_type: int = 0  # 0=regular, 1=none, 2=phone, 3=coordinate
    drop_off_type: int = 0

class GTFSProcessor:
    """Processador principal de dados GTFS"""
    
    def __init__(self, data_dir: str = "data/gtfs"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.stops: Dict[str, GTFSStop] = {}
        self.routes: Dict[str, GTFSRoute] = {}
        self.trips: Dict[str, GTFSTrip] = {}
        self.stop_times: List[GTFSStopTime] = []
        
    def download_gtfs_data(self, url: str, city_name: str) -> str:
        """
        Baixa dados GTFS de uma URL
        
        Args:
            url: URL do arquivo GTFS
            city_name: Nome da cidade para organização
            
        Returns:
            Caminho do arquivo baixado
        """
        try:
            logger.info(f"Baixando dados GTFS para {city_name}...")
            
            response = requests.get(url, timeout=300)
            response.raise_for_status()
            
            # Salvar arquivo
            file_path = self.data_dir / f"{city_name}_gtfs.zip"
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Dados GTFS baixados: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Erro ao baixar dados GTFS: {str(e)}")
            raise
    
    def extract_gtfs_data(self, zip_path: str) -> str:
        """
        Extrai dados GTFS do arquivo ZIP
        
        Args:
            zip_path: Caminho do arquivo ZIP
            
        Returns:
            Caminho do diretório extraído
        """
        try:
            extract_dir = self.data_dir / "extracted"
            extract_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            logger.info(f"Dados GTFS extraídos para: {extract_dir}")
            return str(extract_dir)
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados GTFS: {str(e)}")
            raise
    
    def process_local_gtfs_directory(self, gtfs_dir: str):
        """
        Processa arquivos GTFS de um diretório local (já extraídos)
        
        Args:
            gtfs_dir: Caminho do diretório com arquivos GTFS
        """
        try:
            gtfs_path = Path(gtfs_dir)
            if not gtfs_path.exists():
                raise FileNotFoundError(f"Diretório GTFS não encontrado: {gtfs_dir}")
            
            logger.info(f"Processando arquivos GTFS do diretório: {gtfs_dir}")
            
            # Carregar todos os arquivos GTFS
            self.load_stops(str(gtfs_path))
            self.load_routes(str(gtfs_path))
            self.load_trips(str(gtfs_path))
            self.load_stop_times(str(gtfs_path))
            
            logger.info(f"✅ Arquivos GTFS processados: {len(self.stops)} paradas, {len(self.routes)} rotas, {len(self.trips)} viagens")
            
        except Exception as e:
            logger.error(f"Erro ao processar diretório GTFS local: {str(e)}")
            raise
    
    def load_stops(self, extract_dir: str):
        """Carrega paradas do arquivo stops.txt"""
        try:
            stops_file = Path(extract_dir) / "stops.txt"
            if not stops_file.exists():
                logger.warning("Arquivo stops.txt não encontrado")
                return
            
            with open(stops_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    stop = GTFSStop(
                        stop_id=row['stop_id'],
                        stop_name=row['stop_name'],
                        stop_lat=float(row['stop_lat']),
                        stop_lon=float(row['stop_lon']),
                        stop_type=self._determine_stop_type(row),
                        wheelchair_accessible=row.get('wheelchair_boarding', '0') == '1',
                        zone_id=row.get('zone_id')
                    )
                    self.stops[stop.stop_id] = stop
            
            logger.info(f"Carregadas {len(self.stops)} paradas")
            
        except Exception as e:
            logger.error(f"Erro ao carregar paradas: {str(e)}")
            raise
    
    def load_routes(self, extract_dir: str):
        """Carrega rotas do arquivo routes.txt"""
        try:
            routes_file = Path(extract_dir) / "routes.txt"
            if not routes_file.exists():
                logger.warning("Arquivo routes.txt não encontrado")
                return
            
            with open(routes_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    route = GTFSRoute(
                        route_id=row['route_id'],
                        route_short_name=row.get('route_short_name', ''),
                        route_long_name=row.get('route_long_name', ''),
                        route_type=int(row['route_type']),
                        route_color=row.get('route_color'),
                        route_text_color=row.get('route_text_color')
                    )
                    self.routes[route.route_id] = route
            
            logger.info(f"Carregadas {len(self.routes)} rotas")
            
        except Exception as e:
            logger.error(f"Erro ao carregar rotas: {str(e)}")
            raise
    
    def load_trips(self, extract_dir: str):
        """Carrega viagens do arquivo trips.txt"""
        try:
            trips_file = Path(extract_dir) / "trips.txt"
            if not trips_file.exists():
                logger.warning("Arquivo trips.txt não encontrado")
                return
            
            with open(trips_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    trip = GTFSTrip(
                        trip_id=row['trip_id'],
                        route_id=row['route_id'],
                        service_id=row['service_id'],
                        trip_headsign=row.get('trip_headsign'),
                        direction_id=int(row['direction_id']) if row.get('direction_id') else None,
                        wheelchair_accessible=row.get('wheelchair_accessible', '0') == '1'
                    )
                    self.trips[trip.trip_id] = trip
            
            logger.info(f"Carregadas {len(self.trips)} viagens")
            
        except Exception as e:
            logger.error(f"Erro ao carregar viagens: {str(e)}")
            raise
    
    def load_stop_times(self, extract_dir: str, limit: int = 10000):
        """Carrega horários de parada do arquivo stop_times.txt"""
        try:
            stop_times_file = Path(extract_dir) / "stop_times.txt"
            if not stop_times_file.exists():
                logger.warning("Arquivo stop_times.txt não encontrado")
                return
            
            with open(stop_times_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    if count >= limit:
                        break
                    
                    stop_time = GTFSStopTime(
                        trip_id=row['trip_id'],
                        stop_id=row['stop_id'],
                        arrival_time=row['arrival_time'],
                        departure_time=row['departure_time'],
                        stop_sequence=int(row['stop_sequence']),
                        pickup_type=int(row.get('pickup_type', '0')),
                        drop_off_type=int(row.get('drop_off_type', '0'))
                    )
                    self.stop_times.append(stop_time)
                    count += 1
            
            logger.info(f"Carregados {len(self.stop_times)} horários de parada")
            
        except Exception as e:
            logger.error(f"Erro ao carregar horários: {str(e)}")
            raise
    
    def _determine_stop_type(self, row: Dict[str, str]) -> str:
        """Determina o tipo de parada baseado nos dados"""
        location_type = row.get('location_type', '0')
        if location_type == '1':
            return 'station'
        elif location_type == '2':
            return 'entrance'
        else:
            return 'stop'
    
    def convert_to_conneccity_format(self) -> Tuple[List[Dict], List[Dict]]:
        """
        Converte dados GTFS para formato Conneccity
        
        Returns:
            Tupla com (nós, arestas) no formato Conneccity
        """
        nodes = []
        edges = []
        
        # Converter paradas para nós
        for stop in self.stops.values():
            node = {
                'id': stop.stop_id,
                'name': stop.stop_name,
                'lat': stop.stop_lat,
                'lon': stop.stop_lon,
                'tipo': self._map_stop_type(stop.stop_type)
            }
            nodes.append(node)
        
        # Criar arestas baseadas em rotas e horários
        route_connections = self._build_route_connections()
        
        for connection in route_connections:
            edge = {
                'from': connection['from_stop'],
                'to': connection['to_stop'],
                'tempo_min': connection['travel_time'],
                'transferencia': 1 if connection['is_transfer'] else 0,
                'escada': 0,  # Será preenchido com dados OSM
                'calcada_ruim': 0,  # Será preenchido com dados OSM
                'risco_alag': 0,  # Será preenchido com dados OSM
                'modo': connection['mode']
            }
            edges.append(edge)
        
        logger.info(f"Convertidos {len(nodes)} nós e {len(edges)} arestas")
        return nodes, edges
    
    def _map_stop_type(self, stop_type: str) -> str:
        """Mapeia tipo de parada GTFS para tipo Conneccity"""
        mapping = {
            'stop': 'onibus',
            'station': 'metro',
            'entrance': 'acesso'
        }
        return mapping.get(stop_type, 'onibus')
    
    def _build_route_connections(self) -> List[Dict]:
        """Constrói conexões entre paradas baseadas nas rotas"""
        connections = []
        
        # Agrupar horários por viagem
        trips_stops = {}
        for stop_time in self.stop_times:
            if stop_time.trip_id not in trips_stops:
                trips_stops[stop_time.trip_id] = []
            trips_stops[stop_time.trip_id].append(stop_time)
        
        # Criar conexões sequenciais
        for trip_id, stops in trips_stops.items():
            stops.sort(key=lambda x: x.stop_sequence)
            
            for i in range(len(stops) - 1):
                current = stops[i]
                next_stop = stops[i + 1]
                
                # Calcular tempo de viagem
                travel_time = self._calculate_travel_time(
                    current.departure_time, 
                    next_stop.arrival_time
                )
                
                # Determinar modo de transporte
                trip = self.trips.get(trip_id)
                mode = self._get_transport_mode(trip)
                
                connection = {
                    'from_stop': current.stop_id,
                    'to_stop': next_stop.stop_id,
                    'travel_time': travel_time,
                    'is_transfer': False,
                    'mode': mode
                }
                connections.append(connection)
        
        return connections
    
    def _calculate_travel_time(self, departure: str, arrival: str) -> float:
        """Calcula tempo de viagem entre duas paradas"""
        try:
            # Converter horários para minutos desde meia-noite
            dep_minutes = self._time_to_minutes(departure)
            arr_minutes = self._time_to_minutes(arrival)
            
            if arr_minutes < dep_minutes:  # Viagem que cruza meia-noite
                arr_minutes += 24 * 60
            
            return max(1.0, arr_minutes - dep_minutes)  # Mínimo 1 minuto
            
        except:
            return 5.0  # Tempo padrão se houver erro
    
    def _time_to_minutes(self, time_str: str) -> int:
        """Converte string de tempo (HH:MM:SS) para minutos"""
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        return hours * 60 + minutes
    
    def _get_transport_mode(self, trip: Optional[GTFSTrip]) -> str:
        """Determina modo de transporte baseado na viagem"""
        if not trip:
            return 'onibus'
        
        route = self.routes.get(trip.route_id)
        if not route:
            return 'onibus'
        
        # Mapear tipos de rota GTFS
        mode_mapping = {
            0: 'tram',      # Tram, Streetcar, Light rail
            1: 'metro',     # Subway, Metro
            2: 'trem',      # Rail
            3: 'onibus',    # Bus
            4: 'ferry',     # Ferry
            5: 'cable_tram', # Cable tram
            6: 'aerial_lift', # Aerial lift
            7: 'funicular', # Funicular
            11: 'trolleybus', # Trolleybus
            12: 'monorail'   # Monorail
        }
        
        return mode_mapping.get(route.route_type, 'onibus')
    
    def get_accessible_stops(self) -> List[GTFSStop]:
        """Retorna paradas acessíveis para PcD"""
        return [stop for stop in self.stops.values() if stop.wheelchair_accessible]
    
    def get_routes_by_type(self, route_type: int) -> List[GTFSRoute]:
        """Retorna rotas por tipo"""
        return [route for route in self.routes.values() if route.route_type == route_type]
    
    def export_to_csv(self, output_dir: str):
        """Exporta dados processados para CSV"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Converter para formato Conneccity
            nodes, edges = self.convert_to_conneccity_format()
            
            # Salvar nós
            nodes_file = output_path / "nodes_gtfs.csv"
            with open(nodes_file, 'w', newline='', encoding='utf-8') as f:
                if nodes:
                    writer = csv.DictWriter(f, fieldnames=nodes[0].keys())
                    writer.writeheader()
                    writer.writerows(nodes)
            
            # Salvar arestas
            edges_file = output_path / "edges_gtfs.csv"
            with open(edges_file, 'w', newline='', encoding='utf-8') as f:
                if edges:
                    writer = csv.DictWriter(f, fieldnames=edges[0].keys())
                    writer.writeheader()
                    writer.writerows(edges)
            
            logger.info(f"Dados exportados para: {output_path}")
            
        except Exception as e:
            logger.error(f"Erro ao exportar dados: {str(e)}")
            raise

# URLs de dados GTFS reais (exemplos)
GTFS_SOURCES = {
    "belo_horizonte": "https://ckan.pbh.gov.br/dataset/gtfs",
    "sao_paulo": "https://www.sptrans.com.br/gtfs/",
    "rio_de_janeiro": "https://www.riocard.com/gtfs/",
    "porto_alegre": "https://www.poa.leg.br/gtfs/",
    "curitiba": "https://www.urbs.curitiba.pr.gov.br/gtfs/"
}
