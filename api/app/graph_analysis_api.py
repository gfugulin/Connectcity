"""
API para análise de conectividade e estrutura do grafo
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Tuple
import logging
import pandas as pd
import networkx as nx
from pathlib import Path
import json

logger = logging.getLogger(__name__)

# Router para análise de grafos
graph_analysis_router = APIRouter(prefix="/graph", tags=["Graph Analysis"])

def load_graph_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Carrega dados do grafo dos arquivos CSV"""
    try:
        data_dir = Path(__file__).parent.parent.parent / "data"
        nodes_file = data_dir / "nodes.csv"
        edges_file = data_dir / "edges.csv"
        
        nodes = pd.read_csv(nodes_file)
        edges = pd.read_csv(edges_file)
        
        return nodes, edges
    except Exception as e:
        logger.error(f"Erro ao carregar dados do grafo: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao carregar dados: {str(e)}")

def create_networkx_graph(nodes: pd.DataFrame, edges: pd.DataFrame) -> nx.Graph:
    """Cria grafo NetworkX a partir dos dados CSV"""
    G = nx.Graph()
    
    # Adicionar nós
    for _, node in nodes.iterrows():
        G.add_node(
            node['id'], 
            name=node['name'],
            lat=node['lat'],
            lon=node['lon'],
            tipo=node['tipo']
        )
    
    # Adicionar arestas
    for _, edge in edges.iterrows():
        G.add_edge(
            edge['from'], 
            edge['to'],
            tempo_min=edge['tempo_min'],
            transferencia=edge['transferencia'],
            escada=edge['escada'],
            calcada_ruim=edge['calcada_ruim'],
            risco_alag=edge['risco_alag'],
            modo=edge['modo']
        )
    
    return G

@graph_analysis_router.get("/connectivity")
async def get_connectivity_analysis() -> Dict[str, Any]:
    """
    Análise completa de conectividade do grafo
    """
    try:
        nodes, edges = load_graph_data()
        G = create_networkx_graph(nodes, edges)
        
        # Análise de conectividade
        is_connected = nx.is_connected(G)
        num_components = nx.number_connected_components(G)
        
        # Componentes conectados
        components = list(nx.connected_components(G))
        components_info = []
        
        for i, component in enumerate(components):
            subgraph = G.subgraph(component)
            components_info.append({
                "id": i,
                "size": len(component),
                "nodes": list(component),
                "density": nx.density(subgraph),
                "is_tree": nx.is_tree(subgraph)
            })
        
        # Estatísticas gerais
        total_nodes = G.number_of_nodes()
        total_edges = G.number_of_edges()
        density = nx.density(G)
        
        # Análise de graus
        degrees = dict(G.degree())
        avg_degree = sum(degrees.values()) / len(degrees) if degrees else 0
        max_degree = max(degrees.values()) if degrees else 0
        min_degree = min(degrees.values()) if degrees else 0
        
        return {
            "connectivity": {
                "is_connected": is_connected,
                "num_components": num_components,
                "largest_component_size": len(max(components, key=len)) if components else 0
            },
            "structure": {
                "total_nodes": total_nodes,
                "total_edges": total_edges,
                "density": round(density, 4),
                "avg_degree": round(avg_degree, 2),
                "max_degree": max_degree,
                "min_degree": min_degree
            },
            "components": components_info,
            "timestamp": pd.Timestamp.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro na análise de conectividade: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")

@graph_analysis_router.get("/structure")
async def get_graph_structure() -> Dict[str, Any]:
    """
    Estrutura detalhada do grafo
    """
    try:
        nodes, edges = load_graph_data()
        G = create_networkx_graph(nodes, edges)
        
        # Análise por tipo de nó
        node_types = {}
        for node_id in G.nodes():
            node_data = G.nodes[node_id]
            node_type = node_data.get('tipo', 'unknown')
            if node_type not in node_types:
                node_types[node_type] = []
            node_types[node_type].append({
                "id": node_id,
                "name": node_data.get('name', ''),
                "lat": node_data.get('lat', 0),
                "lon": node_data.get('lon', 0)
            })
        
        # Análise por modo de transporte
        edge_modes = {}
        for edge in G.edges(data=True):
            mode = edge[2].get('modo', 'unknown')
            if mode not in edge_modes:
                edge_modes[mode] = 0
            edge_modes[mode] += 1
        
        # Análise de barreiras
        barriers = {
            "com_escada": sum(1 for _, _, data in G.edges(data=True) if data.get('escada', 0) == 1),
            "calcada_ruim": sum(1 for _, _, data in G.edges(data=True) if data.get('calcada_ruim', 0) == 1),
            "risco_alagamento": sum(1 for _, _, data in G.edges(data=True) if data.get('risco_alag', 0) == 1),
            "com_transferencia": sum(1 for _, _, data in G.edges(data=True) if data.get('transferencia', 0) == 1)
        }
        
        return {
            "nodes_by_type": node_types,
            "edges_by_mode": edge_modes,
            "barriers": barriers,
            "total_nodes": G.number_of_nodes(),
            "total_edges": G.number_of_edges(),
            "timestamp": pd.Timestamp.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro na análise de estrutura: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")

@graph_analysis_router.get("/components")
async def get_connected_components() -> Dict[str, Any]:
    """
    Componentes conectados do grafo
    """
    try:
        nodes, edges = load_graph_data()
        G = create_networkx_graph(nodes, edges)
        
        components = list(nx.connected_components(G))
        components_analysis = []
        
        for i, component in enumerate(components):
            subgraph = G.subgraph(component)
            
            # Análise do componente
            component_analysis = {
                "id": i,
                "size": len(component),
                "nodes": list(component),
                "edges": subgraph.number_of_edges(),
                "density": round(nx.density(subgraph), 4),
                "is_tree": nx.is_tree(subgraph),
                "diameter": nx.diameter(subgraph) if nx.is_connected(subgraph) else None
            }
            
            # Análise por tipo de nó no componente
            node_types = {}
            for node_id in component:
                node_data = G.nodes[node_id]
                node_type = node_data.get('tipo', 'unknown')
                node_types[node_type] = node_types.get(node_type, 0) + 1
            
            component_analysis["node_types"] = node_types
            components_analysis.append(component_analysis)
        
        # Ordenar por tamanho
        components_analysis.sort(key=lambda x: x['size'], reverse=True)
        
        return {
            "num_components": len(components),
            "largest_component_size": components_analysis[0]['size'] if components_analysis else 0,
            "components": components_analysis,
            "timestamp": pd.Timestamp.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro na análise de componentes: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")

@graph_analysis_router.get("/visualization")
async def get_graph_visualization() -> Dict[str, Any]:
    """
    Dados para visualização do grafo
    """
    try:
        nodes, edges = load_graph_data()
        G = create_networkx_graph(nodes, edges)
        
        # Dados dos nós para visualização
        nodes_data = []
        for node_id in G.nodes():
            node_data = G.nodes[node_id]
            nodes_data.append({
                "id": node_id,
                "name": node_data.get('name', ''),
                "lat": node_data.get('lat', 0),
                "lon": node_data.get('lon', 0),
                "tipo": node_data.get('tipo', 'unknown'),
                "degree": G.degree(node_id)
            })
        
        # Dados das arestas para visualização
        edges_data = []
        for edge in G.edges(data=True):
            edges_data.append({
                "from": edge[0],
                "to": edge[1],
                "tempo_min": edge[2].get('tempo_min', 0),
                "transferencia": edge[2].get('transferencia', 0),
                "escada": edge[2].get('escada', 0),
                "calcada_ruim": edge[2].get('calcada_ruim', 0),
                "risco_alag": edge[2].get('risco_alag', 0),
                "modo": edge[2].get('modo', 'unknown')
            })
        
        return {
            "nodes": nodes_data,
            "edges": edges_data,
            "metadata": {
                "total_nodes": len(nodes_data),
                "total_edges": len(edges_data),
                "is_connected": nx.is_connected(G),
                "num_components": nx.number_connected_components(G)
            },
            "timestamp": pd.Timestamp.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro na geração de visualização: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na visualização: {str(e)}")
