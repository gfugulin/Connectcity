"""
Coletor de dados específicos de São Paulo
Integra dados reais de transporte público e infraestrutura urbana
"""
import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import time
from datetime import datetime, timedelta

from .gtfs_processor import GTFSProcessor
from .osm_processor import OSMProcessor
from .data_integrator import DataIntegrator, IntegratedNode, IntegratedEdge

logger = logging.getLogger(__name__)

@dataclass
class SPDataConfig:
    """Configuração de dados de São Paulo"""
    # URLs GTFS oficiais
    gtfs_sources: Dict[str, str]
    # Áreas OSM de interesse
    osm_areas: Dict[str, Tuple[float, float, float, float]]
    # Configurações de atualização
    update_intervals: Dict[str, int]  # em segundos
    # Configurações de cache
    cache_ttl: Dict[str, int]  # em segundos

class SPDataCollector:
    """Coletor de dados específicos de São Paulo"""
    
    def __init__(self, config_file: str = "config/sp_data_config.json"):
        self.config = self._load_config(config_file)
        self.gtfs_processor = GTFSProcessor("data/sp/gtfs")
        self.osm_processor = OSMProcessor("data/sp/osm")
        self.integrator = DataIntegrator("data/sp/integrated")
        
        # Cache de dados
        self.cache = {}
        self.last_update = {}
        
    def _load_config(self, config_file: str) -> SPDataConfig:
        """Carrega configuração de dados de São Paulo"""
        try:
            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            else:
                # Configuração padrão
                config_data = self._get_default_config()
                self._save_config(config_data, config_file)
            
            return SPDataConfig(**config_data)
            
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {str(e)}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Retorna configuração padrão para São Paulo"""
        return {
            "gtfs_sources": {
                "sptrans": "https://www.sptrans.com.br/gtfs/gtfs.zip",
                "metro": "https://www.metro.sp.gov.br/gtfs/gtfs.zip",
                "cptm": "https://www.cptm.sp.gov.br/gtfs/gtfs.zip"
            },
            "osm_areas": {
                "centro": (-46.65, -23.55, -46.60, -23.50),
                "zona_sul": (-46.75, -23.65, -46.60, -23.55),
                "zona_norte": (-46.70, -23.45, -46.50, -23.35),
                "zona_leste": (-46.60, -23.55, -46.40, -23.45),
                "zona_oeste": (-46.80, -23.55, -46.65, -23.45)
            },
            "update_intervals": {
                "gtfs": 3600,      # 1 hora
                "osm": 86400,       # 24 horas
                "integration": 1800  # 30 minutos
            },
            "cache_ttl": {
                "gtfs_data": 3600,      # 1 hora
                "osm_data": 86400,       # 24 horas
                "route_cache": 1800,     # 30 minutos
                "accessibility_data": 7200  # 2 horas
            }
        }
    
    def _save_config(self, config_data: Dict[str, Any], config_file: str):
        """Salva configuração em arquivo"""
        try:
            config_path = Path(config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Configuração salva em: {config_file}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {str(e)}")
    
    async def collect_all_data(self) -> Dict[str, Any]:
        """Coleta todos os dados de São Paulo"""
        try:
            logger.info("Iniciando coleta de dados de São Paulo...")
            
            start_time = time.time()
            results = {}
            
            # Coletar dados GTFS
            gtfs_results = await self._collect_gtfs_data()
            results['gtfs'] = gtfs_results
            
            # Coletar dados OSM
            osm_results = await self._collect_osm_data()
            results['osm'] = osm_results
            
            # Integrar dados
            integration_results = await self._integrate_data()
            results['integration'] = integration_results
            
            # Calcular estatísticas
            results['statistics'] = self._calculate_statistics(results)
            
            duration = time.time() - start_time
            results['duration_seconds'] = duration
            
            logger.info(f"Coleta concluída em {duration:.2f} segundos")
            return results
            
        except Exception as e:
            logger.error(f"Erro na coleta de dados: {str(e)}")
            raise
    
    async def _collect_gtfs_data(self) -> Dict[str, Any]:
        """Coleta dados GTFS de São Paulo"""
        try:
            logger.info("Coletando dados GTFS de São Paulo...")
            
            gtfs_results = {}
            
            for source_name, url in self.config.gtfs_sources.items():
                try:
                    logger.info(f"Processando {source_name}...")
                    
                    # Verificar se há cache válido
                    cache_key = f"gtfs_{source_name}"
                    if self._is_cache_valid(cache_key):
                        gtfs_results[source_name] = self.cache[cache_key]
                        continue
                    
                    # Baixar dados
                    zip_path = await self._download_gtfs_data(url, source_name)
                    
                    # Extrair dados
                    extract_dir = self.gtfs_processor.extract_gtfs_data(zip_path)
                    
                    # Carregar dados
                    self.gtfs_processor.load_stops(extract_dir)
                    self.gtfs_processor.load_routes(extract_dir)
                    self.gtfs_processor.load_trips(extract_dir)
                    self.gtfs_processor.load_stop_times(extract_dir)
                    
                    # Converter para formato Conneccity
                    nodes, edges = self.gtfs_processor.convert_to_conneccity_format()
                    
                    result = {
                        'source': source_name,
                        'url': url,
                        'nodes_count': len(nodes),
                        'edges_count': len(edges),
                        'stops_count': len(self.gtfs_processor.stops),
                        'routes_count': len(self.gtfs_processor.routes),
                        'trips_count': len(self.gtfs_processor.trips),
                        'nodes': nodes,
                        'edges': edges,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    gtfs_results[source_name] = result
                    
                    # Armazenar no cache
                    self._cache_data(cache_key, result)
                    
                    logger.info(f"{source_name}: {len(nodes)} nós, {len(edges)} arestas")
                    
                except Exception as e:
                    logger.error(f"Erro ao processar {source_name}: {str(e)}")
                    gtfs_results[source_name] = {
                        'source': source_name,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
            
            return gtfs_results
            
        except Exception as e:
            logger.error(f"Erro na coleta GTFS: {str(e)}")
            raise
    
    async def _collect_osm_data(self) -> Dict[str, Any]:
        """Coleta dados OSM de São Paulo"""
        try:
            logger.info("Coletando dados OSM de São Paulo...")
            
            osm_results = {}
            
            for area_name, bbox in self.config.osm_areas.items():
                try:
                    logger.info(f"Processando área {area_name}...")
                    
                    # Verificar se há cache válido
                    cache_key = f"osm_{area_name}"
                    if self._is_cache_valid(cache_key):
                        osm_results[area_name] = self.cache[cache_key]
                        continue
                    
                    # Obter dados OSM
                    xml_path = self.osm_processor.get_bbox_data(bbox)
                    
                    # Parse dados
                    self.osm_processor.parse_osm_xml(xml_path)
                    
                    # Análises
                    accessibility_analysis = self.osm_processor.analyze_accessibility()
                    surface_analysis = self.osm_processor.analyze_surface_quality()
                    flood_analysis = self.osm_processor.analyze_flood_risk()
                    
                    # Converter para formato Conneccity
                    edges = self.osm_processor.convert_to_conneccity_edges()
                    
                    result = {
                        'area': area_name,
                        'bbox': bbox,
                        'nodes_count': len(self.osm_processor.nodes),
                        'ways_count': len(self.osm_processor.ways),
                        'edges_count': len(edges),
                        'accessibility_analysis': accessibility_analysis,
                        'surface_analysis': surface_analysis,
                        'flood_analysis': flood_analysis,
                        'edges': edges,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    osm_results[area_name] = result
                    
                    # Armazenar no cache
                    self._cache_data(cache_key, result)
                    
                    logger.info(f"{area_name}: {len(self.osm_processor.nodes)} nós, {len(edges)} arestas")
                    
                except Exception as e:
                    logger.error(f"Erro ao processar área {area_name}: {str(e)}")
                    osm_results[area_name] = {
                        'area': area_name,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
            
            return osm_results
            
        except Exception as e:
            logger.error(f"Erro na coleta OSM: {str(e)}")
            raise
    
    async def _integrate_data(self) -> Dict[str, Any]:
        """Integra dados GTFS e OSM"""
        try:
            logger.info("Integrando dados GTFS e OSM...")
            
            # Verificar se há cache válido
            cache_key = "integrated_data"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]
            
            # Integrar dados
            integration_stats = self.integrator.integrate_city_data(
                'sao_paulo',
                self.config.gtfs_sources.get('sptrans'),
                self.config.osm_areas.get('centro')
            )
            
            # Obter resumo da integração
            summary = self.integrator.get_integration_summary()
            
            result = {
                'integration_stats': integration_stats,
                'summary': summary,
                'timestamp': datetime.now().isoformat()
            }
            
            # Armazenar no cache
            self._cache_data(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Erro na integração: {str(e)}")
            raise
    
    async def _download_gtfs_data(self, url: str, source_name: str) -> str:
        """Baixa dados GTFS de uma URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Salvar arquivo
                        file_path = Path(f"data/sp/gtfs/{source_name}_gtfs.zip")
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        with open(file_path, 'wb') as f:
                            f.write(content)
                        
                        logger.info(f"Dados GTFS baixados: {file_path}")
                        return str(file_path)
                    else:
                        raise Exception(f"Erro HTTP {response.status}: {url}")
                        
        except Exception as e:
            logger.error(f"Erro ao baixar dados GTFS: {str(e)}")
            raise
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Verifica se cache é válido"""
        if cache_key not in self.cache:
            return False
        
        if cache_key not in self.last_update:
            return False
        
        # Verificar TTL baseado no tipo de dados
        data_type = cache_key.split('_')[0]
        ttl = self.config.cache_ttl.get(data_type, 3600)
        
        return time.time() - self.last_update[cache_key] < ttl
    
    def _cache_data(self, cache_key: str, data: Any):
        """Armazena dados no cache"""
        self.cache[cache_key] = data
        self.last_update[cache_key] = time.time()
    
    def _calculate_statistics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula estatísticas dos dados coletados"""
        stats = {
            'total_gtfs_nodes': 0,
            'total_gtfs_edges': 0,
            'total_osm_nodes': 0,
            'total_osm_edges': 0,
            'gtfs_sources_processed': 0,
            'osm_areas_processed': 0,
            'errors': []
        }
        
        # Estatísticas GTFS
        for source_name, source_data in results.get('gtfs', {}).items():
            if 'error' not in source_data:
                stats['total_gtfs_nodes'] += source_data.get('nodes_count', 0)
                stats['total_gtfs_edges'] += source_data.get('edges_count', 0)
                stats['gtfs_sources_processed'] += 1
            else:
                stats['errors'].append(f"GTFS {source_name}: {source_data['error']}")
        
        # Estatísticas OSM
        for area_name, area_data in results.get('osm', {}).items():
            if 'error' not in area_data:
                stats['total_osm_nodes'] += area_data.get('nodes_count', 0)
                stats['total_osm_edges'] += area_data.get('edges_count', 0)
                stats['osm_areas_processed'] += 1
            else:
                stats['errors'].append(f"OSM {area_name}: {area_data['error']}")
        
        return stats
    
    async def get_data_summary(self) -> Dict[str, Any]:
        """Retorna resumo dos dados coletados"""
        try:
            summary = {
                'cache_status': {},
                'last_updates': {},
                'data_counts': {},
                'config': {
                    'gtfs_sources': list(self.config.gtfs_sources.keys()),
                    'osm_areas': list(self.config.osm_areas.keys()),
                    'update_intervals': self.config.update_intervals,
                    'cache_ttl': self.config.cache_ttl
                }
            }
            
            # Status do cache
            for cache_key in self.cache:
                summary['cache_status'][cache_key] = self._is_cache_valid(cache_key)
                summary['last_updates'][cache_key] = datetime.fromtimestamp(
                    self.last_update.get(cache_key, 0)
                ).isoformat()
            
            # Contadores de dados
            for cache_key, data in self.cache.items():
                if isinstance(data, dict):
                    if 'nodes_count' in data:
                        summary['data_counts'][f"{cache_key}_nodes"] = data['nodes_count']
                    if 'edges_count' in data:
                        summary['data_counts'][f"{cache_key}_edges"] = data['edges_count']
            
            return summary
            
        except Exception as e:
            logger.error(f"Erro ao obter resumo: {str(e)}")
            return {'error': str(e)}
    
    async def clear_cache(self):
        """Limpa cache de dados"""
        self.cache.clear()
        self.last_update.clear()
        logger.info("Cache limpo")
    
    async def update_config(self, new_config: Dict[str, Any]):
        """Atualiza configuração"""
        try:
            # Atualizar configuração
            for key, value in new_config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            
            # Salvar configuração
            config_data = {
                'gtfs_sources': self.config.gtfs_sources,
                'osm_areas': self.config.osm_areas,
                'update_intervals': self.config.update_intervals,
                'cache_ttl': self.config.cache_ttl
            }
            
            self._save_config(config_data, "config/sp_data_config.json")
            
            logger.info("Configuração atualizada")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar configuração: {str(e)}")
            raise
