from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ValidationError
from typing import List
import os, json, time, uuid, logging, traceback
from .ffi import Engine
from .models import RouteRequest, AlternativesResponse, Alt
from .exceptions import (
    ConneccityException, GraphLoadException, NodeNotFoundException, 
    RouteNotFoundException, InvalidProfileException, ValidationException,
    CoreLibraryException, handle_conneccity_exception, create_error_response
)
from .validators import validate_route_request, validate_edge_to_fix_request
from .cache import route_cache, alternatives_cache, edge_analysis_cache, cached_route, get_cache_stats, clear_all_caches
from .performance import metrics, measure_performance, get_performance_recommendations
from .real_data_api import real_data_router

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
NODES = os.path.join(DATA_DIR, "nodes.csv")
EDGES = os.path.join(DATA_DIR, "edges.csv")

DEFAULT_WEIGHTS = {
    "padrao": {"alpha":6, "beta":2, "gamma":1, "delta":4},
    "pcd":    {"alpha":6, "beta":12, "gamma":6, "delta":4}
}

app = FastAPI(title="Conneccity API", version="v1", description="API para rotas acessíveis e resilientes")

# Incluir router de dados reais
app.include_router(real_data_router)

# Configurar logging estruturado
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("conneccity")

# Inicializar engine com tratamento de erro
try:
    engine = Engine(NODES, EDGES, DEFAULT_WEIGHTS)
    if not engine.g:
        raise GraphLoadException("Falha ao carregar grafo dos arquivos CSV")
except Exception as e:
    logger.error(f"Erro ao inicializar engine: {str(e)}")
    raise GraphLoadException(f"Erro ao inicializar sistema: {str(e)}")

# Middleware de logs
@app.middleware("http")
async def log_middleware(request: Request, call_next):
    t0 = time.time()
    rid = str(uuid.uuid4())
    
    # Extrair parâmetros da requisição para logs
    request_data = {}
    if request.method == "POST" and request.url.path in ["/route", "/alternatives"]:
        try:
            body = await request.body()
            request_data = json.loads(body)
        except:
            pass
    
    response = await call_next(request)
    
    dt = int((time.time() - t0) * 1000)
    
    log_entry = {
        "rid": rid,
        "path": request.url.path,
        "method": request.method,
        "status": response.status_code,
        "dur_ms": dt
    }
    
    # Adicionar parâmetros específicos para rotas
    if request_data:
        log_entry.update({
            "from": request_data.get("from"),
            "to": request_data.get("to"),
            "perfil": request_data.get("perfil"),
            "chuva": request_data.get("chuva"),
            "k": request_data.get("k")
        })
    
    logger.info(json.dumps(log_entry))
    return response

# Exception handlers
@app.exception_handler(ConneccityException)
async def conneccity_exception_handler(request: Request, exc: ConneccityException):
    """Handler para exceções Conneccity"""
    logger.error(f"ConneccityException: {exc.error_code} - {exc.message}")
    http_exc = handle_conneccity_exception(exc)
    return http_exc

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handler para erros de validação Pydantic"""
    logger.error(f"ValidationError: {exc}")
    return HTTPException(
        status_code=422,
        detail={
            "error_code": "VALIDATION_ERROR",
            "message": "Erro de validação nos dados de entrada",
            "details": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler para exceções gerais"""
    logger.error(f"Exception não tratada: {str(exc)}\n{traceback.format_exc()}")
    return HTTPException(
        status_code=500,
        detail={
            "error_code": "INTERNAL_ERROR",
            "message": "Erro interno do servidor",
            "details": {"exception": str(exc)}
        }
    )

@app.get("/health")
def health():
    return {"status":"ok", "version":"v1"}

@cached_route(route_cache)
def _calculate_route(from_id: str, to_id: str, perfil: str, chuva: bool):
    """Função interna para cálculo de rota (com cache)"""
    s = engine.idx(from_id)
    t = engine.idx(to_id)
    p = engine._params(perfil, chuva)
    path_idx, custo = engine.best(s, t, p)
    
    # Mapear índices para IDs
    import csv
    ids = []
    with open(NODES) as f:
        r = csv.DictReader(f)
        for row in r: 
            ids.append(row["id"])
    
    path = [ids[i] for i in path_idx]
    return {
        "tempo_total_min": round(custo, 1), 
        "path": path, 
        "transferencias": 0, 
        "barreiras_evitas": []
    }

@app.post("/route")
@measure_performance("/route")
def route(req: RouteRequest):
    try:
        # Validar entrada
        validation_errors = validate_route_request(req.from_id, req.to_id, req.perfil, req.chuva, req.k)
        if validation_errors:
            raise ValidationException("Erro de validação", {"validation_errors": validation_errors})
        
        # Verificar se os nós existem
        s = engine.idx(req.from_id)
        t = engine.idx(req.to_id)
        
        if s < 0:
            raise NodeNotFoundException(req.from_id)
        if t < 0:
            raise NodeNotFoundException(req.to_id)
        
        # Calcular rota (com cache)
        result = _calculate_route(req.from_id, req.to_id, req.perfil, req.chuva)
        
        if not result["path"]:
            raise RouteNotFoundException(req.from_id, req.to_id)
        
        return {"best": result}
        
    except ConneccityException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado em /route: {str(e)}")
        raise CoreLibraryException(f"Erro ao calcular rota: {str(e)}")

@app.post("/alternatives", response_model=AlternativesResponse)
def alternatives(req: RouteRequest):
    try:
        # Validar entrada
        validation_errors = validate_route_request(req.from_id, req.to_id, req.perfil, req.chuva, req.k)
        if validation_errors:
            raise ValidationException("Erro de validação", {"validation_errors": validation_errors})
        
        # Verificar se os nós existem
        s = engine.idx(req.from_id)
        t = engine.idx(req.to_id)
        
        if s < 0:
            raise NodeNotFoundException(req.from_id)
        if t < 0:
            raise NodeNotFoundException(req.to_id)
        
        # Calcular alternativas
        p = engine._params(req.perfil, req.chuva)
        k = max(1, min(req.k, 3))
        routes = engine.k_alternatives(s, t, p, k)
        
        if not routes:
            raise RouteNotFoundException(req.from_id, req.to_id)
        
        # Mapear índices para IDs
        import csv
        ids = []
        with open(NODES) as f:
            r = csv.DictReader(f)
            for row in r: 
                ids.append(row["id"])
        
        out: List[Alt] = []
        for i, (path_idx, custo) in enumerate(routes, start=1):
            out.append(Alt(
                id=i, 
                tempo_total_min=round(custo, 1), 
                transferencias=0, 
                path=[ids[x] for x in path_idx]
            ))
        
        return {"alternatives": out}
        
    except ConneccityException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado em /alternatives: {str(e)}")
        raise CoreLibraryException(f"Erro ao calcular alternativas: {str(e)}")

@app.get("/profiles")
def get_profiles():
    """Retorna os perfis disponíveis e seus pesos"""
    return {
        "profiles": DEFAULT_WEIGHTS,
        "description": {
            "padrao": "Perfil padrão para usuários sem restrições de mobilidade",
            "pcd": "Perfil para pessoas com deficiência (PcD) - evita escadas e calçadas ruins"
        }
    }

@app.get("/nodes")
def get_nodes():
    """Retorna todos os nós do grafo"""
    import csv
    nodes = []
    with open(NODES) as f:
        reader = csv.DictReader(f)
        for row in reader:
            nodes.append({
                "id": row["id"],
                "name": row["name"],
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
                "tipo": row["tipo"]
            })
    return {"nodes": nodes}

@app.get("/edges")
def get_edges():
    """Retorna todas as arestas do grafo"""
    import csv
    edges = []
    with open(EDGES) as f:
        reader = csv.DictReader(f)
        for row in reader:
            edges.append({
                "from": row["from"],
                "to": row["to"],
                "tempo_min": float(row["tempo_min"]),
                "transferencia": int(row["transferencia"]),
                "escada": int(row["escada"]),
                "calcada_ruim": int(row["calcada_ruim"]),
                "risco_alag": int(row["risco_alag"]),
                "modo": row["modo"]
            })
    return {"edges": edges}

@app.get("/metrics/edge-to-fix")
def get_edge_to_fix(top: int = 3, perfil: str = "padrao", chuva: bool = False):
    """
    Retorna ranking de trechos que mais impactariam na redução de custo/tempo
    se fossem melhorados
    """
    try:
        # Validar parâmetros
        validation_errors = validate_edge_to_fix_request(top, perfil, chuva)
        if validation_errors:
            raise ValidationException("Erro de validação", {"validation_errors": validation_errors})
        
        # Obter parâmetros de custo
        p = engine._params(perfil, chuva)
        
        # Analisar melhorias
        improvements = engine.analyze_edge_improvements(p, top)
        
        # Mapear índices para IDs dos nós
        import csv
        node_ids = []
        with open(NODES) as f:
            reader = csv.DictReader(f)
            for row in reader:
                node_ids.append(row["id"])
        
        # Formatar resultado
        suggested_improvements = []
        for imp in improvements:
            from_id = node_ids[imp["from"]] if imp["from"] < len(node_ids) else f"Node{imp['from']}"
            to_id = node_ids[imp["to"]] if imp["to"] < len(node_ids) else f"Node{imp['to']}"
            
            # Determinar nível de impacto
            impact_level = "Baixo"
            if imp["impact_score"] > 10:
                impact_level = "Alto"
            elif imp["impact_score"] > 5:
                impact_level = "Médio"
            
            suggested_improvements.append({
                "edge": f"{from_id}->{to_id}",
                "issue": imp["issue_type"],
                "current_cost": round(imp["current_cost"], 2),
                "potential_savings": round(imp["potential_savings"], 2),
                "affected_routes": imp["affected_routes"],
                "impact_score": round(imp["impact_score"], 2),
                "impact_level": impact_level,
                "priority": imp["priority"],
                "description": f"Melhoria de {imp['issue_type']} pode economizar {imp['potential_savings']:.1f}min em {imp['affected_routes']} rotas"
            })
        
        return {
            "analysis_params": {
                "perfil": perfil,
                "chuva": chuva,
                "top": top
            },
            "total_improvements_found": len(improvements),
            "suggested_improvements": suggested_improvements
        }
        
    except ConneccityException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado em /metrics/edge-to-fix: {str(e)}")
        raise CoreLibraryException(f"Erro na análise: {str(e)}")

@app.get("/metrics/performance")
def get_performance_metrics():
    """Retorna métricas de performance da API"""
    try:
        stats = metrics.get_stats()
        cache_stats = get_cache_stats()
        recommendations = get_performance_recommendations()
        
        return {
            "performance_stats": stats,
            "cache_stats": cache_stats,
            "recommendations": recommendations,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Erro ao obter métricas: {str(e)}")
        raise CoreLibraryException(f"Erro ao obter métricas: {str(e)}")

@app.post("/admin/clear-cache")
def clear_cache():
    """Limpa todos os caches (endpoint administrativo)"""
    try:
        clear_all_caches()
        return {
            "message": "Cache limpo com sucesso",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {str(e)}")
        raise CoreLibraryException(f"Erro ao limpar cache: {str(e)}")

@app.get("/admin/cache-stats")
def get_cache_statistics():
    """Retorna estatísticas dos caches"""
    try:
        return {
            "cache_stats": get_cache_stats(),
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de cache: {str(e)}")
        raise CoreLibraryException(f"Erro ao obter estatísticas: {str(e)}")
