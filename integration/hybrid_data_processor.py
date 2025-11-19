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

logger = logging.getLogger(__name__)

class HybridDataProcessor:
    """
    Processador híbrido que combina:
    - API Olho Vivo (prioridade): dados em tempo real
    - GTFS Local (fallback): dados estáticos estruturais
    """
    
    def __init__(self, olho_vivo_token: str, gtfs_dir: Optional[str] = None):
        """
        Inicializa o processador híbrido
        
        Args:
            olho_vivo_token: Token da API Olho Vivo
            gtfs_dir: Diretório com arquivos GTFS locais (opcional)
        """
        self.olho_vivo_client = OlhoVivoClient(olho_vivo_token)
        self.gtfs_processor = GTFSProcessor() if gtfs_dir else None
        self.gtfs_dir = gtfs_dir
        
        self.olho_vivo_available = False
        self.gtfs_available = False
        
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
            'gtfs_local': False
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
                gtfs_nodes, gtfs_edges = self.gtfs_processor.convert_to_conneccity_format()
                
                # GTFS fornece estrutura completa
                nodes = gtfs_nodes
                edges = gtfs_edges
                
                logger.info(f"✅ {len(nodes)} nós carregados do GTFS local")
                logger.info(f"✅ {len(edges)} arestas carregadas do GTFS local")
                
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

