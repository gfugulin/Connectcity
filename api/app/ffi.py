import ctypes as ct
from pathlib import Path
from typing import List, Tuple
import platform

# Detectar sistema operacional e usar biblioteca apropriada
if platform.system() == "Windows":
    LIB_PATH = Path(__file__).resolve().parents[2]/"core-c"/"build"/"libconneccity.dll"
else:
    LIB_PATH = Path(__file__).resolve().parents[2]/"core-c"/"build"/"libconneccity.so"

lib = ct.CDLL(str(LIB_PATH))

class CostParams(ct.Structure):
    _fields_ = [("alpha", ct.c_double), ("beta", ct.c_double), ("gamma", ct.c_double), ("delta", ct.c_double),
                ("chuva_on", ct.c_int), ("perfil_pcd", ct.c_int)]

class Edge(ct.Structure):
    pass

class Node(ct.Structure):
    _fields_ = [("id", ct.c_char*16), ("lat", ct.c_double), ("lon", ct.c_double), ("adj", ct.POINTER(Edge))]

class Graph(ct.Structure):
    _fields_ = [("nodes", ct.POINTER(Node)), ("n", ct.c_int)]

class Route(ct.Structure):
    _fields_ = [("path", ct.POINTER(ct.c_int)), ("len", ct.c_int), ("custo", ct.c_double)]

class EdgeImprovement(ct.Structure):
    _fields_ = [("from", ct.c_int), ("to", ct.c_int), ("issue_type", ct.c_char*32),
                ("current_cost", ct.c_double), ("potential_savings", ct.c_double),
                ("affected_routes", ct.c_int), ("impact_score", ct.c_double), ("priority", ct.c_int)]

class EdgeAnalysisResult(ct.Structure):
    _fields_ = [("improvements", ct.POINTER(EdgeImprovement)), ("count", ct.c_int), ("capacity", ct.c_int)]

lib.load_graph_from_csv.restype = ct.POINTER(Graph)
lib.load_graph_from_csv.argtypes = [ct.c_char_p, ct.c_char_p]
lib.free_graph.argtypes = [ct.POINTER(Graph)]
lib.node_index_by_id.argtypes = [ct.POINTER(Graph), ct.c_char_p]
lib.node_index_by_id.restype = ct.c_int
lib.dijkstra_shortest.argtypes = [ct.POINTER(Graph), ct.c_int, ct.c_int, CostParams]
lib.dijkstra_shortest.restype = Route
lib.k_shortest_yen.argtypes = [ct.POINTER(Graph), ct.c_int, ct.c_int, CostParams, ct.c_int, ct.POINTER(Route)]
lib.k_shortest_yen.restype = ct.c_int
lib.free_route.argtypes = [ct.POINTER(Route)]
lib.analyze_edge_improvements.argtypes = [ct.POINTER(Graph), CostParams, ct.c_int]
lib.analyze_edge_improvements.restype = ct.POINTER(EdgeAnalysisResult)
lib.free_edge_analysis.argtypes = [ct.POINTER(EdgeAnalysisResult)]

class Engine:
    def __init__(self, nodes_csv: str, edges_csv: str, profile_weights: dict):
        self.g = lib.load_graph_from_csv(nodes_csv.encode(), edges_csv.encode())
        self.weights = profile_weights

    def _params(self, perfil: str, chuva: bool) -> CostParams:
        w = self.weights[perfil]
        return CostParams(w["alpha"], w["beta"], w["gamma"], w["delta"], int(chuva), int(perfil=="pcd"))

    def idx(self, node_id: str) -> int:
        return lib.node_index_by_id(self.g, node_id.encode())
    
    def node_id(self, idx: int) -> str:
        """Obter ID do nó por índice"""
        if idx < 0 or idx >= self.g.contents.n:
            return ""
        return self.g.contents.nodes[idx].id.decode()

    def best(self, s: int, t: int, p: CostParams) -> Tuple[List[int], float]:
        r = lib.dijkstra_shortest(self.g, s, t, p)
        try:
            if r.len == 0:
                return [], 0.0
            return [r.path[i] for i in range(r.len)], r.custo
        finally:
            lib.free_route(ct.byref(r))

    def k_alternatives(self, s: int, t: int, p: CostParams, k: int) -> List[Tuple[List[int], float]]:
        routes = (Route * k)()
        n = lib.k_shortest_yen(self.g, s, t, p, k, routes)
        out = []
        for i in range(n):
            r = routes[i]
            out.append(([r.path[j] for j in range(r.len)], r.custo))
            lib.free_route(ct.byref(routes[i]))
        return out

    def analyze_edge_improvements(self, p: CostParams, max_results: int) -> List[dict]:
        result_ptr = lib.analyze_edge_improvements(self.g, p, max_results)
        if not result_ptr:
            return []
        
        result = result_ptr.contents
        improvements = []
        
        for i in range(result.count):
            imp = result.improvements[i]
            improvements.append({
                "from_node": getattr(imp, 'from'),
                "to_node": imp.to,
                "issue_type": imp.issue_type.decode('utf-8'),
                "current_cost": imp.current_cost,
                "potential_savings": imp.potential_savings,
                "affected_routes": imp.affected_routes,
                "impact_score": imp.impact_score,
                "priority": imp.priority
            })
        
        lib.free_edge_analysis(result_ptr)
        return improvements
