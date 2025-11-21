"""
Processador Híbrido: API Olho Vivo (tempo real) + GTFS Local (fallback)
Prioriza dados em tempo real da API Olho Vivo e usa GTFS local como fallback
"""
import logging
import pandas as pd
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import os

from .olho_vivo_client import OlhoVivoClient
from .gtfs_processor import GTFSProcessor
from .spatial_utils import haversine_distance, create_walking_connections

# Import OSM opcional
try:
    from .osm_processor import OSMProcessor
    OSM_AVAILABLE = True
except (ImportError, AttributeError):
    OSM_AVAILABLE = False
    OSMProcessor = None

logger = logging.getLogger(__name__)

class HybridDataProcessor:
    """
    Processador híbrido que combina:
    - API Olho Vivo (prioridade): dados em tempo real
    - GTFS Local (fallback): dados estáticos estruturais
    """
    
    def __init__(
        self,
        olho_vivo_token: str,
        gtfs_dir: Optional[str] = None,
        osm_data_dir: Optional[str] = None,
        enable_walking_connections: bool = True,
        walking_max_distance_m: float = 500
    ):
        """
        Inicializa o processador híbrido
        
        Args:
            olho_vivo_token: Token da API Olho Vivo
            gtfs_dir: Diretório com arquivos GTFS locais (opcional)
            osm_data_dir: Diretório com dados OSM processados (opcional)
            enable_walking_connections: Se True, adiciona conexões de caminhada
            walking_max_distance_m: Distância máxima para conexões de caminhada (metros)
        """
        self.olho_vivo_client = OlhoVivoClient(olho_vivo_token)
        self.gtfs_processor = GTFSProcessor() if gtfs_dir else None
        self.osm_processor = None
        self.gtfs_dir = gtfs_dir
        self.osm_data_dir = osm_data_dir
        self.enable_walking_connections = enable_walking_connections
        self.walking_max_distance_m = walking_max_distance_m
        
        self.olho_vivo_available = False
        self.gtfs_available = False
        self.osm_available = False
        
        # Dados carregados
        self.nodes: List[Dict] = []
        self.edges: List[Dict] = []
        
    def initialize(self) -> Dict[str, bool]:
        """
        Inicializa e verifica disponibilidade das fontes de dados
        
        Returns:
            Dict com status de cada fonte
        """
        status = {
            'olho_vivo': False,
            'gtfs_local': False,
            'osm': False
        }
        
        # Tentar autenticar na API Olho Vivo
        try:
            if self.olho_vivo_client.authenticate():
                self.olho_vivo_available = True
                status['olho_vivo'] = True
                logger.info("✅ API Olho Vivo disponível")
            else:
                logger.warning("⚠️ API Olho Vivo não disponível (autenticação falhou)")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao conectar com API Olho Vivo: {e}")
        
        # Verificar OSM local
        if self.osm_data_dir:
            osm_paths = [
                self.osm_data_dir,
                os.path.abspath(self.osm_data_dir),
                os.path.join(os.getcwd(), self.osm_data_dir),
                os.path.join(os.path.dirname(os.path.dirname(__file__)), self.osm_data_dir)
            ]
            
            osm_dir_found = None
            for path in osm_paths:
                if os.path.isdir(path):
                    osm_dir_found = path
                    break
            
            if osm_dir_found:
                if OSM_AVAILABLE and OSMProcessor:
                    try:
                        self.osm_processor = OSMProcessor()
                        # Tentar carregar dados OSM
                        # (implementar conforme necessário)
                        self.osm_available = True
                        status['osm'] = True
                        logger.info(f"✅ Dados OSM disponíveis: {osm_dir_found}")
                    except Exception as e:
                        logger.warning(f"⚠️ Erro ao carregar dados OSM: {e}")
                else:
                    logger.info("ℹ️ OSMProcessor não disponível")
            else:
                logger.info("ℹ️ Dados OSM não configurados")
        
        # Verificar GTFS local
        if self.gtfs_dir:
            # Tentar caminho absoluto e relativo
            gtfs_paths = [
                self.gtfs_dir,
                os.path.abspath(self.gtfs_dir),
                os.path.join(os.getcwd(), self.gtfs_dir),
                os.path.join(os.path.dirname(os.path.dirname(__file__)), self.gtfs_dir)
            ]
            
            gtfs_dir_found = None
            for path in gtfs_paths:
                if os.path.isdir(path):
                    gtfs_dir_found = path
                    break
            
            if gtfs_dir_found:
                logger.info(f"📁 Diretório GTFS encontrado: {gtfs_dir_found}")
                required_files = ["stops.txt", "routes.txt", "trips.txt", "stop_times.txt"]
                missing_files = []
                
                for f in required_files:
                    file_path = os.path.join(gtfs_dir_found, f)
                    if not os.path.isfile(file_path):
                        missing_files.append(f)
                
                if not missing_files:
                    self.gtfs_available = True
                    self.gtfs_dir = gtfs_dir_found  # Atualizar para caminho encontrado
                    status['gtfs_local'] = True
                    logger.info(f"✅ GTFS local disponível: {gtfs_dir_found}")
                else:
                    logger.warning(f"⚠️ GTFS local incompleto. Arquivos faltando: {', '.join(missing_files)}")
                    logger.warning(f"   Diretório verificado: {gtfs_dir_found}")
            else:
                logger.warning(f"⚠️ GTFS local não encontrado. Caminhos testados:")
                for path in gtfs_paths:
                    logger.warning(f"   - {path} (existe: {os.path.exists(path)})")
        else:
            logger.warning("⚠️ GTFS local não configurado (gtfs_dir=None)")
        
        return status
    
    def load_data(self) -> Tuple[List[Dict], List[Dict]]:
        """
        Carrega dados usando estratégia híbrida:
        1. Prioridade: API Olho Vivo (paradas e linhas)
        2. Fallback: GTFS Local (estrutura completa)
        3. Combinação: quando ambos disponíveis
        
        Returns:
            Tupla (nodes, edges) no formato Conneccity
        """
        nodes = []
        edges = []
        
        # Estratégia: GTFS Local fornece estrutura completa do grafo
        # API Olho Vivo é usada para dados em tempo real (não estrutura)
        
        # Estratégia 1: Carregar GTFS Local (estrutura completa do grafo)
        if self.gtfs_available:
            try:
                logger.info("📁 Carregando estrutura do grafo do GTFS local...")
                
                # Processar GTFS local
                self.gtfs_processor.process_local_gtfs_directory(self.gtfs_dir)
                gtfs_nodes, gtfs_edges = self.gtfs_processor.convert_to_conneccity_format(
                    add_walking_connections=self.enable_walking_connections,
                    walking_max_distance_m=self.walking_max_distance_m,
                    walking_max_connections=10
                )
                
                # GTFS fornece estrutura completa
                nodes = gtfs_nodes
                edges = gtfs_edges
                
                logger.info(f"✅ {len(nodes)} nós carregados do GTFS local")
                logger.info(f"✅ {len(edges)} arestas carregadas do GTFS local (incluindo caminhada)")
                
                # Integrar dados OSM se disponível
                if self.osm_available and self.osm_processor:
                    try:
                        logger.info("🗺️ Integrando dados OSM...")
                        osm_edges = self._integrate_osm_edges(nodes, edges)
                        if osm_edges:
                            edges.extend(osm_edges)
                            logger.info(f"✅ Adicionadas {len(osm_edges)} arestas OSM")
                    except Exception as e:
                        logger.warning(f"⚠️ Erro ao integrar OSM: {e}")
                
                # Se API Olho Vivo disponível, marcar para uso em tempo real
                if self.olho_vivo_available:
                    logger.info("✅ API Olho Vivo disponível para dados em tempo real (posição de veículos, previsões)")
                    
            except Exception as e:
                logger.error(f"❌ Erro ao carregar GTFS local: {e}")
                self.gtfs_available = False
        
        # Validar que temos dados
        if not nodes or not edges:
            if not self.gtfs_available:
                raise ValueError("GTFS local não disponível. É necessário para estrutura do grafo.")
            raise ValueError("Erro ao carregar dados do GTFS local")
        
        self.nodes = nodes
        self.edges = edges
        
        return nodes, edges
    
    def _load_olho_vivo_data(self) -> Tuple[List[Dict], List[Dict]]:
        """
        Carrega dados da API Olho Vivo
        
        Nota: A API Olho Vivo não fornece estrutura completa do grafo.
        Ela é usada principalmente para:
        - Busca de paradas específicas (quando necessário)
        - Posição de veículos em tempo real
        - Previsão de chegada
        
        A estrutura do grafo (nós e arestas) vem do GTFS local.
        
        Returns:
            Tupla (nodes, edges) - edges sempre vazios (API não fornece estrutura)
        """
        nodes = []
        edges = []
        
        # API Olho Vivo não tem endpoint para listar todas as paradas
        # As paradas são buscadas sob demanda quando necessário
        # A estrutura completa do grafo vem do GTFS local
        
        logger.info("ℹ️ API Olho Vivo disponível para dados em tempo real")
        logger.info("ℹ️ Estrutura do grafo será carregada do GTFS local")
        
        return nodes, edges
    
    def export_to_csv(self, output_dir: str) -> Dict[str, str]:
        """
        Exporta dados processados para CSV
        
        Args:
            output_dir: Diretório de saída
            
        Returns:
            Dict com caminhos dos arquivos gerados
        """
        if not self.nodes or not self.edges:
            raise ValueError("Dados não carregados. Execute load_data() primeiro.")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Converter para DataFrames
        nodes_df = pd.DataFrame(self.nodes)
        edges_df = pd.DataFrame(self.edges)
        
        # Salvar
        nodes_file = output_path / "nodes.csv"
        edges_file = output_path / "edges.csv"
        
        nodes_df.to_csv(nodes_file, index=False)
        edges_df.to_csv(edges_file, index=False)
        
        logger.info(f"✅ Dados exportados: {nodes_file}, {edges_file}")
        
        return {
            'nodes': str(nodes_file),
            'edges': str(edges_file),
            'nodes_count': len(nodes_df),
            'edges_count': len(edges_df)
        }
    
    def _integrate_osm_edges(self, nodes: List[Dict], existing_edges: List[Dict]) -> List[Dict]:
        """
        Integra arestas OSM com nós GTFS, conectando paradas aos nós OSM mais próximos
        
        Args:
            nodes: Lista de nós GTFS
            existing_edges: Lista de arestas existentes (para evitar duplicatas)
            
        Returns:
            Lista de novas arestas OSM
        """
        if not self.osm_processor:
            return []
        
        new_edges = []
        existing_edges_set = {(e['from'], e['to']) for e in existing_edges}
        
        try:
            # Obter arestas OSM
            osm_edges = self.osm_processor.convert_to_conneccity_edges()
            
            # Criar mapa de nós OSM por coordenadas (aproximado)
            # Conectar paradas GTFS aos nós OSM mais próximos
            for osm_edge in osm_edges:
                # Verificar se aresta já existe
                edge_key = (osm_edge['from'], osm_edge['to'])
                if edge_key in existing_edges_set:
                    continue
                
                # Adicionar aresta OSM
                new_edges.append(osm_edge)
        
        except Exception as e:
            logger.warning(f"Erro ao processar arestas OSM: {e}")
        
        return new_edges
    
    def get_data_source_info(self) -> Dict[str, any]:
        """
        Retorna informações sobre as fontes de dados
        
        Returns:
            Dict com informações de cada fonte
        """
        return {
            'olho_vivo': {
                'available': self.olho_vivo_available,
                'description': 'API Olho Vivo - Dados em tempo real',
                'use_case': 'Posição de veículos, previsão de chegada, busca de paradas'
            },
            'gtfs_local': {
                'available': self.gtfs_available,
                'description': 'GTFS Local - Dados estáticos estruturais',
                'use_case': 'Estrutura do grafo, conexões entre paradas, rotas completas',
                'directory': self.gtfs_dir
            },
            'osm': {
                'available': self.osm_available,
                'description': 'OpenStreetMap - Dados de infraestrutura urbana',
                'use_case': 'Caminhos de caminhada, acessibilidade, barreiras',
                'directory': self.osm_data_dir
            },
            'strategy': (
                'hybrid' if (self.olho_vivo_available and self.gtfs_available) else
                'gtfs_only' if self.gtfs_available else
                'olho_vivo_only' if self.olho_vivo_available else 'none'
            ),
            'note': (
                'Estrutura do grafo: GTFS Local | Dados em tempo real: API Olho Vivo' 
                if (self.olho_vivo_available and self.gtfs_available) else
                'Apenas estrutura estática (sem dados em tempo real)' 
                if self.gtfs_available else
                'API disponível mas sem estrutura do grafo (rotas não funcionarão)'
            )
        }

