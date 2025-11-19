"""
Utilitários para processamento de rotas
Funções para calcular transferências, barreiras, modo de transporte, etc.
"""
import pandas as pd
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Cache para dados do grafo
_nodes_df: Optional[pd.DataFrame] = None
_edges_df: Optional[pd.DataFrame] = None


def load_graph_data(nodes_file: str, edges_file: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Carrega dados do grafo e armazena em cache"""
    global _nodes_df, _edges_df
    
    if _nodes_df is None or _edges_df is None:
        import os
        
        # Verificar se os arquivos existem
        if not os.path.isfile(nodes_file):
            raise FileNotFoundError(f"Arquivo de nós não encontrado: {nodes_file}")
        if not os.path.isfile(edges_file):
            raise FileNotFoundError(f"Arquivo de arestas não encontrado: {edges_file}")
        
        # Verificar se os arquivos não estão vazios
        nodes_size = os.path.getsize(nodes_file)
        edges_size = os.path.getsize(edges_file)
        
        if nodes_size == 0:
            raise ValueError(f"Arquivo de nós está vazio: {nodes_file}")
        if edges_size == 0:
            raise ValueError(f"Arquivo de arestas está vazio: {edges_file}")
        
        try:
            # Tentar ler os arquivos CSV
            _nodes_df = pd.read_csv(nodes_file)
            _edges_df = pd.read_csv(edges_file)
            
            # Verificar se os DataFrames não estão vazios
            if _nodes_df.empty:
                raise ValueError(f"Arquivo de nós não contém dados: {nodes_file}")
            if _edges_df.empty:
                raise ValueError(f"Arquivo de arestas não contém dados: {edges_file}")
            
            logger.info(f"Dados do grafo carregados: {len(_nodes_df)} nós, {len(_edges_df)} arestas")
        except pd.errors.EmptyDataError as e:
            logger.error(f"Erro: arquivo CSV vazio ou sem colunas - {e}")
            raise ValueError(f"Arquivo CSV vazio ou mal formatado: {str(e)}")
        except pd.errors.ParserError as e:
            logger.error(f"Erro ao fazer parse do CSV: {e}")
            raise ValueError(f"Erro ao fazer parse do arquivo CSV: {str(e)}")
        except Exception as e:
            logger.error(f"Erro ao carregar dados do grafo: {e}")
            raise
    
    return _nodes_df, _edges_df


def get_edge_info(from_node: str, to_node: str, edges_df: pd.DataFrame) -> Optional[Dict]:
    """Obtém informações de uma aresta específica"""
    edge = edges_df[(edges_df['from'] == from_node) & (edges_df['to'] == to_node)]
    if len(edge) == 0:
        return None
    
    row = edge.iloc[0]
    return {
        'from': row['from'],
        'to': row['to'],
        'tempo_min': float(row['tempo_min']),
        'transferencia': int(row.get('transferencia', 0)),
        'escada': int(row.get('escada', 0)),
        'calcada_ruim': int(row.get('calcada_ruim', 0)),
        'risco_alag': int(row.get('risco_alag', 0)),
        'modo': str(row.get('modo', 'pe'))
    }


def calculate_transfers(path: List[str], edges_df: pd.DataFrame) -> int:
    """
    Calcula o número de transferências em um caminho.
    Transferência ocorre quando há mudança de modo de transporte.
    """
    if len(path) < 2:
        return 0
    
    transfers = 0
    previous_mode = None
    
    for i in range(len(path) - 1):
        from_node = path[i]
        to_node = path[i + 1]
        
        edge_info = get_edge_info(from_node, to_node, edges_df)
        if edge_info is None:
            continue
        
        current_mode = edge_info['modo']
        
        # Se há mudança de modo e não é caminhada (pe), conta como transferência
        if previous_mode is not None and current_mode != previous_mode:
            # Caminhada não conta como transferência, apenas mudanças entre transportes
            if previous_mode != 'pe' and current_mode != 'pe':
                transfers += 1
            # Se sai de transporte para caminhada e depois volta, conta como transferência
            elif previous_mode != 'pe' and current_mode == 'pe':
                # Verificar se próximo trecho volta para transporte
                if i + 2 < len(path):
                    next_edge = get_edge_info(path[i + 1], path[i + 2], edges_df)
                    if next_edge and next_edge['modo'] != 'pe':
                        transfers += 1
        
        previous_mode = current_mode
    
    return transfers


def get_path_segments(path: List[str], edges_df: pd.DataFrame) -> List[Dict]:
    """
    Retorna segmentos do caminho com informações detalhadas de cada trecho.
    """
    segments = []
    
    for i in range(len(path) - 1):
        from_node = path[i]
        to_node = path[i + 1]
        
        edge_info = get_edge_info(from_node, to_node, edges_df)
        if edge_info is None:
            continue
        
        segments.append({
            'from': from_node,
            'to': to_node,
            'tempo_min': edge_info['tempo_min'],
            'modo': edge_info['modo'],
            'transferencia': edge_info['transferencia'],
            'escada': edge_info['escada'],
            'calcada_ruim': edge_info['calcada_ruim'],
            'risco_alag': edge_info['risco_alag']
        })
    
    return segments


def identify_avoided_barriers(path: List[str], edges_df: pd.DataFrame, profile: str) -> List[str]:
    """
    Identifica barreiras que foram evitadas na rota.
    Para perfil PcD, identifica escadas e calçadas ruins que foram evitadas.
    Nota: Esta função identifica barreiras presentes no caminho.
    Para identificar barreiras realmente evitadas, seria necessário comparar
    com outras rotas possíveis. Por enquanto, retorna barreiras encontradas
    que são problemáticas para o perfil.
    """
    barriers = []
    
    segments = get_path_segments(path, edges_df)
    
    for segment in segments:
        # Para perfil PcD, escadas e calçadas ruins são barreiras
        if profile == 'pcd':
            if segment['escada'] == 1:
                barriers.append(f"escada@{segment['from']}->{segment['to']}")
            if segment['calcada_ruim'] == 1:
                barriers.append(f"calcada_ruim@{segment['from']}->{segment['to']}")
        
        # Risco de alagamento é barreira para todos os perfis
        if segment['risco_alag'] == 1:
            barriers.append(f"alagamento@{segment['from']}->{segment['to']}")
    
    return barriers


def get_route_details(path: List[str], cost: float, edges_df: pd.DataFrame, 
                     nodes_df: pd.DataFrame, profile: str) -> Dict:
    """
    Retorna detalhes completos de uma rota, incluindo passo a passo.
    """
    if len(path) == 0:
        return {
            'path': [],
            'total_time_min': 0.0,
            'transfers': 0,
            'barriers_avoided': [],
            'steps': [],
            'modes': []
        }
    
    segments = get_path_segments(path, edges_df)
    transfers = calculate_transfers(path, edges_df)
    barriers = identify_avoided_barriers(path, edges_df, profile)
    
    # Construir passo a passo
    steps = []
    current_mode = None
    current_segment_group = []
    
    for i, segment in enumerate(segments):
        from_node = segment['from']
        to_node = segment['to']
        modo = segment['modo']
        tempo = segment['tempo_min']
        
        # Obter informações dos nós
        from_node_rows = nodes_df[nodes_df['id'] == from_node]
        to_node_rows = nodes_df[nodes_df['id'] == to_node]
        
        from_node_info = from_node_rows.iloc[0] if len(from_node_rows) > 0 else None
        to_node_info = to_node_rows.iloc[0] if len(to_node_rows) > 0 else None
        
        # Se mudou o modo, finalizar grupo anterior e começar novo
        if current_mode is not None and modo != current_mode:
            if current_segment_group:
                steps.append({
                    'type': 'transport',
                    'mode': current_mode,
                    'from': current_segment_group[0]['from'],
                    'to': current_segment_group[-1]['to'],
                    'from_name': current_segment_group[0].get('from_name', current_segment_group[0]['from']),
                    'to_name': current_segment_group[-1].get('to_name', current_segment_group[-1]['to']),
                    'time_min': sum(s['tempo_min'] for s in current_segment_group),
                    'segments': current_segment_group
                })
            
            current_segment_group = []
        
        # Adicionar segmento ao grupo atual
        segment_data = {
            'from': from_node,
            'to': to_node,
            'from_name': str(from_node_info['name']) if from_node_info is not None else from_node,
            'to_name': str(to_node_info['name']) if to_node_info is not None else to_node,
            'from_lat': float(from_node_info['lat']) if from_node_info is not None else 0.0,
            'from_lon': float(from_node_info['lon']) if from_node_info is not None else 0.0,
            'to_lat': float(to_node_info['lat']) if to_node_info is not None else 0.0,
            'to_lon': float(to_node_info['lon']) if to_node_info is not None else 0.0,
            'tempo_min': tempo,
            'modo': modo
        }
        current_segment_group.append(segment_data)
        
        current_mode = modo
    
    # Adicionar último grupo
    if current_segment_group:
        steps.append({
            'type': 'transport',
            'mode': current_mode,
            'from': current_segment_group[0]['from'],
            'to': current_segment_group[-1]['to'],
            'from_name': current_segment_group[0].get('from_name', current_segment_group[0]['from']),
            'to_name': current_segment_group[-1].get('to_name', current_segment_group[-1]['to']),
            'time_min': sum(s['tempo_min'] for s in current_segment_group),
            'segments': current_segment_group
        })
    
    # Adicionar passo inicial (caminhada até primeiro ponto, se necessário)
    if steps and path:
        first_node_rows = nodes_df[nodes_df['id'] == path[0]]
        if len(first_node_rows) > 0:
            first_node_info = first_node_rows.iloc[0]
            steps.insert(0, {
                'type': 'walk',
                'mode': 'pe',
                'from': path[0],
                'to': path[0],
                'from_name': str(first_node_info['name']),
                'to_name': str(first_node_info['name']),
                'time_min': 0.0,
                'instruction': 'Iniciar viagem'
            })
    
    return {
        'path': path,
        'total_time_min': cost,
        'transfers': transfers,
        'barriers_avoided': barriers,
        'steps': steps,
        'modes': list(set(s['modo'] for s in segments)) if segments else []
    }

