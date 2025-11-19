from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, ValidationError
from typing import List, Optional
import os, json, time, uuid, logging, traceback
import pandas as pd
from .ffi import Engine
from .models import RouteRequest, AlternativesResponse, Alt, RouteDetailsRequest
from .exceptions import (
    ConneccityException, GraphLoadException, NodeNotFoundException, 
    RouteNotFoundException, InvalidProfileException, ValidationException,
    CoreLibraryException, handle_conneccity_exception, create_error_response
)
from .validators import validate_route_request, validate_edge_to_fix_request
from .cache import route_cache, alternatives_cache, edge_analysis_cache, cached_route, get_cache_stats, clear_all_caches
from .performance import metrics, measure_performance, get_performance_recommendations
from .route_utils import (
    load_graph_data, calculate_transfers, get_path_segments,
    identify_avoided_barriers, get_route_details, get_edge_info
)
from .real_data_api import real_data_router
from .sp_data_api import sp_data_router
from .pipeline_api import pipeline_router
from .validation_api import validation_router
from .graph_analysis_api import graph_analysis_router
from .olho_vivo_api import olho_vivo_router

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
    "idoso":  {"alpha":6, "beta":4, "gamma":2, "delta":4},
    "pcd":    {"alpha":6, "beta":12, "gamma":6, "delta":4}
}

app = FastAPI(title="Conneccity API", version="v1", description="API para rotas acessíveis e resilientes")

# Configurar CORS para permitir requisições do frontend
# IMPORTANTE: CORS deve ser adicionado ANTES de incluir routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default
        "http://localhost:3000",  # Next.js default
        "http://localhost:5174",  # Vite alternativo
        "http://localhost:8000",  # Python http.server
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

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

# Token da API Olho Vivo
OLHO_VIVO_TOKEN = os.getenv(
    "OLHO_VIVO_TOKEN",
    "1abf7ba19b22829e9d95648f8affe9afaf8c64b9cbb8c8042e6b50cb5d63be81"
)

# Diretório GTFS local (fallback)
# Tentar múltiplos caminhos possíveis
GTFS_LOCAL_DIR_ENV = os.getenv("GTFS_LOCAL_DIR", "GTFS")
# Verificar se existe (pode estar na raiz do projeto ou relativo)
_gtfs_paths = [
    GTFS_LOCAL_DIR_ENV,
    os.path.abspath(GTFS_LOCAL_DIR_ENV),
    os.path.join(os.path.dirname(__file__), "..", "..", GTFS_LOCAL_DIR_ENV),
    os.path.join(os.path.dirname(__file__), "..", "..", "..", GTFS_LOCAL_DIR_ENV)
]
GTFS_LOCAL_DIR = None
for path in _gtfs_paths:
    if os.path.isdir(path):
        GTFS_LOCAL_DIR = path
        print(f"[BOOT] 📁 Diretório GTFS encontrado: {GTFS_LOCAL_DIR}")
        break
if not GTFS_LOCAL_DIR:
    print(f"[BOOT] ⚠️ Diretório GTFS não encontrado. Caminhos testados: {_gtfs_paths}")

# Inicializar engine com fallback automático
def _init_engine_with_fallback() -> Engine:
    # Tentativa 0: Dados híbridos (API Olho Vivo + GTFS Local) - NOVA PRIORIDADE
    try:
        from integration.hybrid_data_processor import HybridDataProcessor
        
        hybrid_processor = HybridDataProcessor(
            olho_vivo_token=OLHO_VIVO_TOKEN,
            gtfs_dir=GTFS_LOCAL_DIR  # Já validado acima
        )
        
        status = hybrid_processor.initialize()
        logger.info(f"📊 Status das fontes de dados: {status}")
        
        if status['olho_vivo'] or status['gtfs_local']:
            # Carregar dados híbridos
            nodes, edges = hybrid_processor.load_data()
            
            # Salvar temporariamente para o Engine
            hybrid_output_dir = os.path.join(DATA_DIR, "hybrid")
            os.makedirs(hybrid_output_dir, exist_ok=True)
            
            hybrid_nodes_file = os.path.join(hybrid_output_dir, "nodes.csv")
            hybrid_edges_file = os.path.join(hybrid_output_dir, "edges.csv")
            
            # Exportar para CSV
            hybrid_processor.export_to_csv(hybrid_output_dir)
            
            # Carregar no Engine
            eng = Engine(hybrid_nodes_file, hybrid_edges_file, DEFAULT_WEIGHTS)
            if eng.g and eng.g.contents.n > 0:
                strategy = hybrid_processor.get_data_source_info()['strategy']
                logger.info(f"✅ Engine inicializado com dados híbridos (estratégia: {strategy})")
                logger.info(f"   - API Olho Vivo: {'✅' if status['olho_vivo'] else '❌'}")
                logger.info(f"   - GTFS Local: {'✅' if status['gtfs_local'] else '❌'}")
                return eng
    except Exception as e:
        logger.warning(f"⚠️ Falha ao carregar dados híbridos: {e}")
        logger.info("🔄 Tentando outras fontes de dados...")
    
    # Tentativa 1: Dados integrados (prioridade - dados reais do mapa)
    integrated_nodes = os.path.join(DATA_DIR, "integrated", "integrated_nodes.csv")
    integrated_edges = os.path.join(DATA_DIR, "integrated", "integrated_edges.csv")
    
    if os.path.isfile(integrated_nodes) and os.path.isfile(integrated_edges):
        try:
            eng = Engine(integrated_nodes, integrated_edges, DEFAULT_WEIGHTS)
            if eng.g and eng.g.contents.n > 0:
                logger.info(f"✅ Engine inicializado com dados integrados (OSM+GTFS): {integrated_nodes}")
                return eng
        except Exception as e:
            logger.warning(f"Falha ao carregar dados integrados: {e}")
    
    # Tentativa 2: arquivos primários
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
    
    # Carregar dados do grafo para utilitários (usar mesmo arquivo que o engine)
    try:
        # Verificar qual arquivo foi usado pelo engine (prioridade: híbrido > integrado > primário)
        hybrid_nodes = os.path.join(DATA_DIR, "hybrid", "nodes.csv")
        hybrid_edges = os.path.join(DATA_DIR, "hybrid", "edges.csv")
        integrated_nodes = os.path.join(DATA_DIR, "integrated", "integrated_nodes.csv")
        integrated_edges = os.path.join(DATA_DIR, "integrated", "integrated_edges.csv")
        
        # Prioridade 1: Dados híbridos (API Olho Vivo + GTFS)
        hybrid_valid = (
            os.path.isfile(hybrid_nodes) and 
            os.path.isfile(hybrid_edges) and
            os.path.getsize(hybrid_nodes) > 0 and
            os.path.getsize(hybrid_edges) > 0
        )
        
        if hybrid_valid:
            try:
                nodes_df, edges_df = load_graph_data(hybrid_nodes, hybrid_edges)
                logger.info("✅ Dados do grafo carregados para utilitários (dados híbridos - API Olho Vivo + GTFS)")
            except Exception as e:
                logger.warning(f"⚠️ Falha ao carregar dados híbridos, tentando dados integrados: {e}")
                hybrid_valid = False
        
        # Prioridade 2: Dados integrados (se híbrido não disponível)
        if not hybrid_valid:
            integrated_valid = (
                os.path.isfile(integrated_nodes) and 
                os.path.isfile(integrated_edges) and
                os.path.getsize(integrated_nodes) > 0 and
                os.path.getsize(integrated_edges) > 0
            )
            
            if integrated_valid:
                try:
                    nodes_df, edges_df = load_graph_data(integrated_nodes, integrated_edges)
                    logger.info("✅ Dados do grafo carregados para utilitários (dados integrados)")
                except Exception as e:
                    logger.warning(f"⚠️ Falha ao carregar dados integrados, tentando arquivos primários: {e}")
                    integrated_valid = False
            
            # Prioridade 3: Arquivos primários
            if not integrated_valid:
                if os.path.isfile(NODES) and os.path.isfile(EDGES) and os.path.getsize(NODES) > 0 and os.path.getsize(EDGES) > 0:
                    nodes_df, edges_df = load_graph_data(NODES, EDGES)
                    logger.info("✅ Dados do grafo carregados para utilitários (arquivos primários)")
                else:
                    raise FileNotFoundError("Nenhum arquivo CSV válido encontrado para carregar dados do grafo")
    except Exception as e:
        logger.warning(f"⚠️ Não foi possível carregar dados do grafo: {e}")
        logger.warning("⚠️ Funcionalidades que dependem dos dados do grafo podem não funcionar corretamente")
        nodes_df, edges_df = None, None
except Exception as e:
    logger.error(f"❌ Erro ao inicializar engine: {str(e)}")
    # Para debug: criar um engine mock
    logger.info("🔧 Criando engine mock para debug...")
    engine = None
    nodes_df, edges_df = None, None

# Handler para requisições OPTIONS (CORS preflight)
# O CORS middleware já trata isso, mas este handler garante compatibilidade
@app.options("/{full_path:path}")
async def options_handler(request: Request, full_path: str):
    """Handler para requisições OPTIONS (CORS preflight)"""
    origin = request.headers.get("origin", "*")
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": origin if origin in [
                "http://localhost:5173", "http://localhost:3000", 
                "http://localhost:5174", "http://localhost:8000",
                "http://127.0.0.1:5173", "http://127.0.0.1:3000", "http://127.0.0.1:8000"
            ] else "http://localhost:5173",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "3600",
        }
    )

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
            "route_details": "/route/details",
            "profiles": "/profiles",
            "nodes": "/nodes",
            "nodes_search": "/nodes/search",
            "real_data": "/real-data",
            "sp_data": "/sp-data",
            "pipeline": "/pipeline",
            "validation": "/validation",
            "graph_analysis": "/graph"
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
            raise RouteNotFoundException(request.from_id, request.to_id)
        
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
            raise RouteNotFoundException(request.from_id, request.to_id)
        
        # Carregar dados do grafo se necessário (usar variáveis globais)
        global nodes_df, edges_df
        if nodes_df is None or edges_df is None:
            try:
                nodes_df, edges_df = load_graph_data(NODES, EDGES)
            except Exception as e:
                logger.warning(f"Não foi possível carregar dados do grafo: {e}")
                nodes_df, edges_df = None, None
        
        # Construir alternativas com dados completos
        alt_list = []
        for i, (path, cost) in enumerate(alternatives):
            # Converter índices para IDs de nós
            path_ids = [engine.node_id(idx) for idx in path]
            
            # Calcular transferências e barreiras se dados disponíveis
            transfers = 0
            barriers = []
            if edges_df is not None:
                transfers = calculate_transfers(path_ids, edges_df)
                barriers = identify_avoided_barriers(path_ids, edges_df, request.perfil)
            
            alt = Alt(
                id=i,
                tempo_total_min=cost,
                transferencias=transfers,
                path=path_ids,
                barreiras_evitas=barriers
            )
            alt_list.append(alt)
        
        return AlternativesResponse(
            alternatives=alt_list,
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

# Endpoint para listar todos os nós
@app.get("/nodes")
async def get_nodes():
    """Lista todos os nós do grafo"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine não inicializado")
    
    try:
        # Carregar dados se necessário (usar variáveis globais)
        global nodes_df, edges_df
        if nodes_df is None:
            try:
                nodes_df, edges_df = load_graph_data(NODES, EDGES)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Erro ao carregar nós: {str(e)}")
        
        # Converter DataFrame para lista de dicionários
        nodes_list = []
        for _, row in nodes_df.iterrows():
            nodes_list.append({
                "id": str(row['id']),
                "name": str(row['name']),
                "lat": float(row['lat']),
                "lon": float(row['lon']),
                "tipo": str(row['tipo'])
            })
        
        return {
            "nodes": nodes_list,
            "total": len(nodes_list)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar nós: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# Endpoint para buscar nós (autocomplete)
@app.get("/nodes/search", tags=["Nodes"])
async def search_nodes(q: str = Query(..., min_length=1, description="Termo de busca")):
    """Busca nós por nome ou ID (para autocomplete)"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine não inicializado")
    
    try:
        # Carregar dados se necessário (usar variáveis globais)
        global nodes_df, edges_df
        if nodes_df is None:
            try:
                nodes_df, edges_df = load_graph_data(NODES, EDGES)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Erro ao carregar nós: {str(e)}")
        
        # Buscar nós que correspondem à query (case-insensitive)
        query_lower = q.lower()
        matches = nodes_df[
            nodes_df['name'].str.lower().str.contains(query_lower, na=False) |
            nodes_df['id'].str.lower().str.contains(query_lower, na=False)
        ]
        
        # Limitar a 20 resultados
        matches = matches.head(20)
        
        # Converter para lista
        nodes_list = []
        for _, row in matches.iterrows():
            nodes_list.append({
                "id": str(row['id']),
                "name": str(row['name']),
                "lat": float(row['lat']),
                "lon": float(row['lon']),
                "tipo": str(row['tipo'])
            })
        
        return {
            "nodes": nodes_list,
            "query": q,
            "total": len(nodes_list)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar nós: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# Endpoint para detalhes da rota
@app.post("/route/details")
async def get_route_details(request: RouteDetailsRequest):
    """Retorna detalhes completos de uma rota, incluindo passo a passo"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine não inicializado")
    
    try:
        # Validar perfil
        if request.perfil not in DEFAULT_WEIGHTS:
            raise InvalidProfileException(f"Perfil inválido: {request.perfil}")
        
        # Carregar dados se necessário (usar variáveis globais)
        global nodes_df, edges_df
        if nodes_df is None or edges_df is None:
            try:
                nodes_df, edges_df = load_graph_data(NODES, EDGES)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Erro ao carregar dados: {str(e)}")
        
        # Se path não foi fornecido, calcular rota primeiro
        if not request.path:
            s = engine.idx(request.from_id)
            t = engine.idx(request.to_id)
            
            if s == -1:
                raise NodeNotFoundException(f"Nó origem não encontrado: {request.from_id}")
            if t == -1:
                raise NodeNotFoundException(f"Nó destino não encontrado: {request.to_id}")
            
            params = engine._params(request.perfil, request.chuva)
            path_indices, cost = engine.best(s, t, params)
            
            if not path_indices:
                raise RouteNotFoundException(request.from_id, request.to_id)
            
            # Converter índices para IDs
            path = [engine.node_id(idx) for idx in path_indices]
        else:
            path = request.path
            # Calcular custo aproximado (soma dos tempos dos segmentos)
            cost = 0.0
            for i in range(len(path) - 1):
                edge_info = get_edge_info(path[i], path[i + 1], edges_df)
                if edge_info:
                    cost += edge_info['tempo_min']
        
        # Obter detalhes completos
        details = get_route_details(path, cost, edges_df, nodes_df, request.perfil)
        
        return {
            "path": path,
            "from": request.from_id if not request.path else path[0],
            "to": request.to_id if not request.path else path[-1],
            "profile": request.perfil,
            "rain": request.chuva,
            "total_time_min": details['total_time_min'],
            "transfers": details['transfers'],
            "barriers_avoided": details['barriers_avoided'],
            "modes": details['modes'],
            "steps": details['steps']
        }
    except ConneccityException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter detalhes da rota: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# Tratamento de exceções
@app.exception_handler(ConneccityException)
async def conneccity_exception_handler(request: Request, exc: ConneccityException):
    http_exc = handle_conneccity_exception(exc)
    raise http_exc

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler para HTTPException - garante que CORS headers sejam adicionados"""
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail} if isinstance(exc.detail, str) else exc.detail,
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "http://localhost:5173"),
            "Access-Control-Allow-Credentials": "true",
        }
    )

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=400,
        content=create_error_response(400, "Validation Error", str(exc)),
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "http://localhost:5173"),
            "Access-Control-Allow-Credentials": "true",
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Erro não tratado: {str(exc)}")
    logger.error(traceback.format_exc())
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content=create_error_response(500, "Internal Server Error", "Erro interno do servidor"),
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "http://localhost:5173"),
            "Access-Control-Allow-Credentials": "true",
        }
    )

# Incluir routers (DEPOIS dos endpoints principais para evitar conflitos)
app.include_router(real_data_router)
app.include_router(sp_data_router)
app.include_router(pipeline_router)
app.include_router(validation_router)
app.include_router(graph_analysis_router)
app.include_router(olho_vivo_router)
