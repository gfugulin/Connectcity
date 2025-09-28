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
from .sp_data_api import sp_data_router
from .pipeline_api import pipeline_router
from .validation_api import validation_router

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
NODES = os.path.join(DATA_DIR, "nodes.csv")
EDGES = os.path.join(DATA_DIR, "edges.csv")

# Logar os caminhos efetivos
print(f"[BOOT] CSV paths -> NODES={NODES} EDGES={EDGES}")
print(f"[BOOT] DATA_DIR={DATA_DIR}")
print(f"[BOOT] NODES existe: {os.path.isfile(NODES)}")
print(f"[BOOT] EDGES existe: {os.path.isfile(EDGES)}")

DEFAULT_WEIGHTS = {
    "padrao": {"alpha":6, "beta":2, "gamma":1, "delta":4},
    "pcd":    {"alpha":6, "beta":12, "gamma":6, "delta":4}
}

app = FastAPI(title="Conneccity API", version="v1", description="API para rotas acessíveis e resilientes")

# Incluir routers
app.include_router(real_data_router)
app.include_router(sp_data_router)
app.include_router(pipeline_router)
app.include_router(validation_router)

# Configurar logging estruturado
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("conneccity")

# Criar dataset mínimo se necessário
def _create_minimal_dataset():
    """Cria um dataset mínimo para garantir que a API funcione"""
    minimal_nodes = os.path.join(DATA_DIR, "minimal_nodes.csv")
    minimal_edges = os.path.join(DATA_DIR, "minimal_edges.csv")
    
    # Criar diretório se não existir
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Criar nodes.csv mínimo
    with open(minimal_nodes, 'w') as f:
        f.write("id,name,lat,lon,tipo\n")
        f.write("node1,Estação Central,-23.5505,-46.6333,metro\n")
        f.write("node2,Estação Paulista,-23.5615,-46.6565,metro\n")
        f.write("node3,Terminal Bandeira,-23.5505,-46.6333,onibus\n")
    
    # Criar edges.csv mínimo
    with open(minimal_edges, 'w') as f:
        f.write("from,to,tempo_min,transferencia,escada,calcada_ruim,risco_alag,modo\n")
        f.write("node1,node2,5.0,0,0,0,0,metro\n")
        f.write("node2,node3,3.0,1,0,1,0,pe\n")
    
    logger.info(f"Dataset mínimo criado: {minimal_nodes} e {minimal_edges}")
    return minimal_nodes, minimal_edges

# Inicializar engine com fallback automático
def _init_engine_with_fallback() -> Engine:
    # Tentativa 1: arquivos primários
    if os.path.isfile(NODES) and os.path.isfile(EDGES):
        try:
            eng = Engine(NODES, EDGES, DEFAULT_WEIGHTS)
            if eng.g and eng.g.contents.n > 0:
                logger.info(f"Engine inicializado com CSV primário: NODES={NODES} EDGES={EDGES}")
                return eng
        except Exception as e:
            logger.warning(f"Falha ao carregar CSV primário: {e}")
    
    # Tentativa 2: CSV de amostra
    sample_nodes = os.path.join(DATA_DIR, "sp", "sample", "nodes.csv")
    sample_edges = os.path.join(DATA_DIR, "sp", "sample", "edges.csv")
    
    logger.info(f"Tentando fallback para: {sample_nodes} e {sample_edges}")
    logger.info(f"sample_nodes existe: {os.path.isfile(sample_nodes)}")
    logger.info(f"sample_edges existe: {os.path.isfile(sample_edges)}")
    
    if os.path.isfile(sample_nodes) and os.path.isfile(sample_edges):
        try:
            eng = Engine(sample_nodes, sample_edges, DEFAULT_WEIGHTS)
            if eng.g and eng.g.contents.n > 0:
                logger.info(f"Engine inicializado com CSV de amostra: NODES={sample_nodes} EDGES={sample_edges}")
                return eng
        except Exception as e:
            logger.error(f"Falha ao carregar CSV de amostra: {e}")
    
    # Tentativa 3: Dataset mínimo
    logger.info("Criando dataset mínimo...")
    minimal_nodes, minimal_edges = _create_minimal_dataset()
    try:
        eng = Engine(minimal_nodes, minimal_edges, DEFAULT_WEIGHTS)
        if eng.g and eng.g.contents.n > 0:
            logger.info(f"Engine inicializado com dataset mínimo: NODES={minimal_nodes} EDGES={minimal_edges}")
            return eng
    except Exception as e:
        logger.error(f"Falha ao carregar dataset mínimo: {e}")
    
    raise GraphLoadException("Nenhum arquivo CSV válido encontrado (nem primário, nem amostra, nem mínimo)")

# Inicializar engine com fallback
try:
    engine = _init_engine_with_fallback()
    logger.info("✅ Engine inicializado com sucesso!")
except Exception as e:
    logger.error(f"❌ Erro ao inicializar engine: {str(e)}")
    # Para debug: criar um engine mock
    logger.info("🔧 Criando engine mock para debug...")
    engine = None

# Middleware de logs
@app.middleware("http")
async def log_middleware(request: Request, call_next):
    t0 = time.time()
    req_id = str(uuid.uuid4())[:8]
    
    # Log da requisição
    logger.info(f"[{req_id}] {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        dt = time.time() - t0
        logger.info(f"[{req_id}] {response.status_code} {dt:.3f}s")
        return response
    except Exception as e:
        dt = time.time() - t0
        logger.error(f"[{req_id}] ERROR {dt:.3f}s: {str(e)}")
        raise

# Endpoint raiz
@app.get("/")
async def root():
    """Endpoint raiz da API"""
    return {
        "message": "Conneccity API - Sistema de Rotas Acessíveis e Resilientes",
        "version": "v1",
        "status": "online",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "route": "/route",
            "alternatives": "/alternatives",
            "profiles": "/profiles",
            "real_data": "/real-data",
            "sp_data": "/sp-data",
            "pipeline": "/pipeline",
            "validation": "/validation"
        },
        "engine_loaded": engine is not None
    }

# Endpoint de health check
@app.get("/health")
async def health_check():
    """Endpoint de health check"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "engine_loaded": engine is not None,
        "version": "v1"
    }

# Endpoint de rota
@app.post("/route")
async def get_route(request: RouteRequest):
    """Calcular rota entre dois pontos"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine não inicializado")
    
    try:
        # Validar perfil
        if request.perfil not in DEFAULT_WEIGHTS:
            raise InvalidProfileException(f"Perfil inválido: {request.perfil}")
        
        # Obter índices dos nós
        s = engine.idx(request.from_id)
        t = engine.idx(request.to_id)
        
        if s == -1:
            raise NodeNotFoundException(f"Nó origem não encontrado: {request.from_id}")
        if t == -1:
            raise NodeNotFoundException(f"Nó destino não encontrado: {request.to_id}")
        
        # Calcular rota
        params = engine._params(request.perfil, request.chuva)
        path, cost = engine.best(s, t, params)
        
        if not path:
            raise RouteNotFoundException(f"Nenhuma rota encontrada entre {request.from_id} e {request.to_id}")
        
        return {
            "path": path,
            "cost": cost,
            "from": request.from_id,
            "to": request.to_id,
            "profile": request.perfil,
            "rain": request.chuva
        }
    except ConneccityException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# Endpoint de alternativas
@app.post("/alternatives")
async def get_alternatives(request: RouteRequest):
    """Calcular k rotas alternativas"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine não inicializado")
    
    try:
        # Validar perfil
        if request.perfil not in DEFAULT_WEIGHTS:
            raise InvalidProfileException(f"Perfil inválido: {request.perfil}")
        
        # Obter índices dos nós
        s = engine.idx(request.from_id)
        t = engine.idx(request.to_id)
        
        if s == -1:
            raise NodeNotFoundException(f"Nó origem não encontrado: {request.from_id}")
        if t == -1:
            raise NodeNotFoundException(f"Nó destino não encontrado: {request.to_id}")
        
        # Calcular alternativas
        params = engine._params(request.perfil, request.chuva)
        alternatives = engine.k_alternatives(s, t, params, request.k)
        
        if not alternatives:
            raise RouteNotFoundException(f"Nenhuma rota encontrada entre {request.from_id} e {request.to_id}")
        
        return AlternativesResponse(
            alternatives=[Alt(path=path, cost=cost) for path, cost in alternatives],
            from_id=request.from_id,
            to_id=request.to_id,
            profile=request.perfil,
            rain=request.chuva
        )
    except ConneccityException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# Endpoint de perfis
@app.get("/profiles")
async def get_profiles():
    """Listar perfis disponíveis"""
    return {
        "profiles": list(DEFAULT_WEIGHTS.keys()),
        "weights": DEFAULT_WEIGHTS
    }

# Tratamento de exceções
@app.exception_handler(ConneccityException)
async def conneccity_exception_handler(request: Request, exc: ConneccityException):
    return handle_conneccity_exception(request, exc)

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return create_error_response(400, "Validation Error", str(exc))

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Erro não tratado: {str(exc)}")
    logger.error(traceback.format_exc())
    return create_error_response(500, "Internal Server Error", "Erro interno do servidor")
