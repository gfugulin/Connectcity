from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, ValidationError
from typing import List, Optional
from datetime import datetime
import os, json, time, uuid, logging, traceback
import pandas as pd
from .ffi import Engine
from .models import (
    RouteRequest,
    AlternativesResponse,
    Alt,
    RouteDetailsRequest,
    BarrierReport,
    BarrierReportResponse,
    Notification,
    NotificationsResponse,
)
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
    identify_avoided_barriers, get_route_details as build_route_details, get_edge_info
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
# Arquivo simples para armazenar relatos de barreiras
BARRIERS_FILE = os.path.join(DATA_DIR, "barriers_reports.jsonl")

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
            gtfs_dir=GTFS_LOCAL_DIR,  # Já validado acima
            enable_walking_connections=True,  # Habilitar conexões de caminhada
            walking_max_distance_m=1000  # 1000m (1km) máximo para caminhada - aumentado para melhor conectividade
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
    
    # Tentativa 1: Dados integrados de SP (prioridade - dados reais do mapa)
    sp_integrated_nodes = os.path.join(DATA_DIR, "sp", "integrated", "integrated_nodes.csv")
    sp_integrated_edges = os.path.join(DATA_DIR, "sp", "integrated", "integrated_edges.csv")
    
    if os.path.isfile(sp_integrated_nodes) and os.path.isfile(sp_integrated_edges):
        # Verificar se os arquivos não estão vazios
        if os.path.getsize(sp_integrated_nodes) > 100 and os.path.getsize(sp_integrated_edges) > 100:
            try:
                eng = Engine(sp_integrated_nodes, sp_integrated_edges, DEFAULT_WEIGHTS)
                if eng.g and eng.g.contents.n > 0:
                    logger.info(f"✅ Engine inicializado com dados integrados de SP (OSM+GTFS): {sp_integrated_nodes}")
                    logger.info(f"   📊 Nós carregados: {eng.g.contents.n}")
                    return eng
            except Exception as e:
                logger.warning(f"Falha ao carregar dados integrados de SP: {e}")
    
    # Tentativa 1b: Dados integrados genéricos (fallback)
    integrated_nodes = os.path.join(DATA_DIR, "integrated", "integrated_nodes.csv")
    integrated_edges = os.path.join(DATA_DIR, "integrated", "integrated_edges.csv")
    
    if os.path.isfile(integrated_nodes) and os.path.isfile(integrated_edges):
        # Verificar se os arquivos não estão vazios
        if os.path.getsize(integrated_nodes) > 100 and os.path.getsize(integrated_edges) > 100:
            try:
                eng = Engine(integrated_nodes, integrated_edges, DEFAULT_WEIGHTS)
                if eng.g and eng.g.contents.n > 0:
                    logger.info(f"✅ Engine inicializado com dados integrados (OSM+GTFS): {integrated_nodes}")
                    logger.info(f"   📊 Nós carregados: {eng.g.contents.n}")
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
        
        # Prioridade 2: Dados integrados de SP (se híbrido não disponível)
        if not hybrid_valid:
            sp_integrated_nodes = os.path.join(DATA_DIR, "sp", "integrated", "integrated_nodes.csv")
            sp_integrated_edges = os.path.join(DATA_DIR, "sp", "integrated", "integrated_edges.csv")
            
            sp_integrated_valid = (
                os.path.isfile(sp_integrated_nodes) and 
                os.path.isfile(sp_integrated_edges) and
                os.path.getsize(sp_integrated_nodes) > 100 and
                os.path.getsize(sp_integrated_edges) > 100
            )
            
            if sp_integrated_valid:
                try:
                    nodes_df, edges_df = load_graph_data(sp_integrated_nodes, sp_integrated_edges)
                    logger.info("✅ Dados do grafo carregados para utilitários (dados integrados de SP)")
                except Exception as e:
                    logger.warning(f"⚠️ Falha ao carregar dados integrados de SP, tentando dados integrados genéricos: {e}")
                    sp_integrated_valid = False
            
            # Prioridade 2b: Dados integrados genéricos (fallback)
            if not sp_integrated_valid:
                integrated_valid = (
                    os.path.isfile(integrated_nodes) and 
                    os.path.isfile(integrated_edges) and
                    os.path.getsize(integrated_nodes) > 100 and
                    os.path.getsize(integrated_edges) > 100
                )
                
                if integrated_valid:
                    try:
                        nodes_df, edges_df = load_graph_data(integrated_nodes, integrated_edges)
                        logger.info("✅ Dados do grafo carregados para utilitários (dados integrados)")
                    except Exception as e:
                        logger.warning(f"⚠️ Falha ao carregar dados integrados, tentando arquivos primários: {e}")
                        integrated_valid = False
                else:
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


@app.get("/notifications", response_model=NotificationsResponse)
async def get_notifications():
    """
    Retorna notificações importantes para o usuário.
    Inclui alertas sobre barreiras, manutenções, dicas e avisos do sistema.
    """
    try:
        notifications = []
        
        # Verificar relatos recentes de barreiras críticas
        if os.path.isfile(BARRIERS_FILE):
            try:
                recent_barriers = []
                with open(BARRIERS_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            try:
                                barrier = json.loads(line)
                                # Considerar apenas barreiras dos últimos 7 dias e com severidade >= 4
                                if barrier.get('severity', 0) >= 4:
                                    received_at = barrier.get('received_at', 0)
                                    if time.time() - received_at < 7 * 24 * 3600:  # 7 dias
                                        recent_barriers.append(barrier)
                            except:
                                continue
                
                if recent_barriers:
                    # Agrupar por tipo de barreira
                    barrier_types = {}
                    for b in recent_barriers:
                        b_type = b.get('type', 'outro')
                        if b_type not in barrier_types:
                            barrier_types[b_type] = 0
                        barrier_types[b_type] += 1
                    
                    # Criar notificação para cada tipo crítico
                    for b_type, count in barrier_types.items():
                        type_names = {
                            'escada': 'Escadas',
                            'calcada_ruim': 'Calçadas em mau estado',
                            'alagamento': 'Riscos de alagamento',
                            'obstaculo': 'Obstáculos',
                            'iluminacao_ruim': 'Iluminação inadequada',
                            'seguranca': 'Problemas de segurança',
                            'sinalizacao_ruim': 'Sinalização deficiente',
                            'outro': 'Outras barreiras'
                        }
                        notifications.append(Notification(
                            id=f"barrier_{b_type}_{int(time.time())}",
                            type="warning",
                            title=f"Alertas sobre {type_names.get(b_type, 'barreiras')}",
                            message=f"{count} relato(s) recente(s) de {type_names.get(b_type, 'barreiras')} na região. Verifique as rotas antes de sair.",
                            priority=4 if count >= 3 else 3,
                            created_at=datetime.now(),
                            expires_at=None,
                            action_url=None,
                            action_label=None
                        ))
            except Exception as e:
                logger.warning(f"Erro ao processar barreiras para notificações: {e}")
        
        # Notificação de dica (rotativa)
        tips = [
            {
                "title": "💡 Dica: Use o perfil correto",
                "message": "Selecione o perfil de mobilidade adequado (Padrão, Idoso ou PcD) para obter rotas mais adequadas às suas necessidades."
            },
            {
                "title": "💡 Dica: Reporte barreiras",
                "message": "Ajude outros usuários reportando barreiras que encontrar durante seu trajeto. Sua contribuição é valiosa!"
            },
            {
                "title": "💡 Dica: Salve rotas favoritas",
                "message": "Salve suas rotas mais usadas como favoritas para acesso rápido. Toque no ícone de favorito na tela de detalhes da rota."
            },
            {
                "title": "💡 Dica: Navegação em tempo real",
                "message": "Ative a navegação para receber instruções passo a passo baseadas na sua localização GPS."
            }
        ]
        
        # Selecionar dica baseada no dia da semana (para rotacionar)
        import calendar
        day_of_week = datetime.now().weekday()
        tip = tips[day_of_week % len(tips)]
        
        notifications.append(Notification(
            id=f"tip_{day_of_week}",
            type="tip",
            title=tip["title"],
            message=tip["message"],
            priority=1,
            created_at=datetime.now(),
            expires_at=None,
            action_url=None,
            action_label=None
        ))
        
        # Notificação sobre sistema (se houver atualizações)
        notifications.append(Notification(
            id="system_info",
            type="info",
            title="✅ Sistema operacional",
            message="Todos os sistemas estão funcionando normalmente. Dados de transporte atualizados.",
            priority=1,
            created_at=datetime.now(),
            expires_at=None,
            action_url=None,
            action_label=None
        ))
        
        # Ordenar por prioridade (maior primeiro) e data (mais recente primeiro)
        notifications.sort(key=lambda x: (-x.priority, -x.created_at.timestamp()))
        
        # Limitar a 10 notificações mais relevantes
        notifications = notifications[:10]
        
        return NotificationsResponse(
            notifications=notifications,
            unread_count=len([n for n in notifications if n.priority >= 3])
        )
    except Exception as e:
        logger.error(f"Erro ao buscar notificações: {e}")
        return NotificationsResponse(notifications=[], unread_count=0)


@app.post("/barriers/report", response_model=BarrierReportResponse)
async def report_barrier(report: BarrierReport, request: Request):
    """
    Recebe um relato de barreira feito pelo usuário.
    
    Contrato JSON esperado (exemplo):
    {
      "route_id": 0,
      "from_node": "18906",
      "to_node": "4406630",
      "step_index": 2,
      "node_id": "720011915",
      "profile": "pcd",
      "type": "escada",
      "severity": 4,
      "description": "Escada sem corrimão ao sair da estação",
      "lat": -23.56,
      "lon": -46.65,
      "app_version": "1.0.0",
      "platform": "web"
    }
    """
    try:
        logger.info(f"[BARRIER_REPORT] Recebido relato: type={report.type}, profile={report.profile}, step_index={report.step_index}")
        
        # Garantir que diretório de dados existe
        os.makedirs(DATA_DIR, exist_ok=True)
        
        barrier_id = str(uuid.uuid4())
        payload = report.dict()
        payload["id"] = barrier_id
        payload["received_at"] = time.time()
        payload["client_ip"] = request.client.host if request.client else None
        
        # Log do tipo de created_at antes da serialização
        if "created_at" in payload:
            logger.info(f"[BARRIER_REPORT] created_at type: {type(payload['created_at'])}, value: {payload['created_at']}")
        
        # Função auxiliar para converter datetime para string ISO
        def datetime_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Tipo {type(obj)} não é serializável")
        
        # Persistência simples em arquivo .jsonl (uma linha por relato)
        try:
            with open(BARRIERS_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False, default=datetime_serializer) + "\n")
            logger.info(f"✅ Relato de barreira '{barrier_id}' salvo com sucesso em {BARRIERS_FILE}")
        except Exception as e:
            logger.error(f"Erro ao salvar relato de barreira em arquivo: {e}")
            logger.error(traceback.format_exc())
            # Mesmo que falhe ao salvar, ainda respondemos algo amigável
            return BarrierReportResponse(
                id=barrier_id,
                message="Recebemos seu relato, mas houve um problema ao salvar. Tentaremos corrigir em breve.",
                stored=False,
                created_at=report.created_at,
            )
        
        return BarrierReportResponse(
            id=barrier_id,
            message="Obrigado! Seu relato de barreira foi registrado e ajudará outras pessoas.",
            stored=True,
            created_at=report.created_at,
        )
    except ValidationError as e:
        logger.error(f"[BARRIER_REPORT] Erro de validação: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=422, detail=f"Erro de validação: {str(e)}")
    except Exception as e:
        logger.error(f"[BARRIER_REPORT] Erro ao processar relato de barreira: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erro ao registrar barreira: {str(e)}")

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
    logger.info(f"[ALTERNATIVES] Requisição recebida: from={request.from_id}, to={request.to_id}, perfil={request.perfil}, k={request.k}")
    
    if not engine:
        logger.error("[ALTERNATIVES] Engine não inicializado")
        raise HTTPException(status_code=503, detail="Engine não inicializado")
    
    try:
        # Declarar variável global no início da função
        global nodes_df, edges_df
        
        # Validar perfil
        if request.perfil not in DEFAULT_WEIGHTS:
            raise InvalidProfileException(f"Perfil inválido: {request.perfil}")
        
        # Obter índices dos nós (tentar por ID primeiro, depois por nome)
        s = engine.idx(request.from_id)
        t = engine.idx(request.to_id)
        
        # Logging detalhado para diagnóstico
        logger.info(f"[ALTERNATIVES] Buscando nós: from_id='{request.from_id}' -> índice={s}, to_id='{request.to_id}' -> índice={t}")
        
        # Verificar se os índices correspondem aos IDs corretos
        if s >= 0:
            actual_from_id = engine.node_id(s)
            logger.info(f"[ALTERNATIVES] Índice {s} corresponde ao ID: '{actual_from_id}' (esperado: '{request.from_id}')")
            if actual_from_id != request.from_id:
                logger.warning(f"[ALTERNATIVES] ⚠️ ID não corresponde! Esperado '{request.from_id}', encontrado '{actual_from_id}'")
        
        if t >= 0:
            actual_to_id = engine.node_id(t)
            logger.info(f"[ALTERNATIVES] Índice {t} corresponde ao ID: '{actual_to_id}' (esperado: '{request.to_id}')")
            if actual_to_id != request.to_id:
                logger.warning(f"[ALTERNATIVES] ⚠️ ID não corresponde! Esperado '{request.to_id}', encontrado '{actual_to_id}'")
        
        # Se não encontrou por ID, tentar buscar por nome
        if s == -1:
            if nodes_df is None:
                try:
                    hybrid_nodes = os.path.join(DATA_DIR, "hybrid", "nodes.csv")
                    if os.path.isfile(hybrid_nodes):
                        nodes_df, _ = load_graph_data(hybrid_nodes, os.path.join(DATA_DIR, "hybrid", "edges.csv"))
                except:
                    pass
            
            if nodes_df is not None:
                # Buscar por nome
                nodes_df['name'] = nodes_df['name'].astype(str).fillna('')
                match = nodes_df[nodes_df['name'].str.lower() == request.from_id.lower()]
                if len(match) > 0:
                    node_id = str(match.iloc[0]['id'])
                    s = engine.idx(node_id)
                    logger.info(f"[ALTERNATIVES] Nó origem encontrado por nome '{request.from_id}' -> ID: {node_id}")
        
        if t == -1:
            if nodes_df is None:
                try:
                    hybrid_nodes = os.path.join(DATA_DIR, "hybrid", "nodes.csv")
                    if os.path.isfile(hybrid_nodes):
                        nodes_df, _ = load_graph_data(hybrid_nodes, os.path.join(DATA_DIR, "hybrid", "edges.csv"))
                except:
                    pass
            
            if nodes_df is not None:
                # Buscar por nome
                nodes_df['name'] = nodes_df['name'].astype(str).fillna('')
                match = nodes_df[nodes_df['name'].str.lower() == request.to_id.lower()]
                if len(match) > 0:
                    node_id = str(match.iloc[0]['id'])
                    t = engine.idx(node_id)
                    logger.info(f"[ALTERNATIVES] Nó destino encontrado por nome '{request.to_id}' -> ID: {node_id}")
        
        logger.info(f"[ALTERNATIVES] Índices encontrados: origem={s}, destino={t}")
        
        if s == -1:
            logger.error(f"[ALTERNATIVES] Nó origem '{request.from_id}' não encontrado no engine (nem por ID nem por nome)")
            raise NodeNotFoundException(f"Nó origem não encontrado: {request.from_id}")
        if t == -1:
            logger.error(f"[ALTERNATIVES] Nó destino '{request.to_id}' não encontrado no engine (nem por ID nem por nome)")
            raise NodeNotFoundException(f"Nó destino não encontrado: {request.to_id}")
        
        # Calcular alternativas
        params = engine._params(request.perfil, request.chuva)
        logger.info(f"[ALTERNATIVES] Calculando {request.k} rotas alternativas...")
        logger.info(f"[ALTERNATIVES] Parâmetros: alpha={params.alpha}, beta={params.beta}, gamma={params.gamma}, delta={params.delta}")
        
        import time
        start_time = time.time()
        alternatives = engine.k_alternatives(s, t, params, request.k)
        elapsed_time = time.time() - start_time
        
        logger.info(f"[ALTERNATIVES] Algoritmo executado em {elapsed_time:.3f}s")
        logger.info(f"[ALTERNATIVES] Algoritmo retornou {len(alternatives) if alternatives else 0} rotas")
        
        if not alternatives:
            # Tentar buscar apenas a primeira rota (Dijkstra simples) para diagnóstico
            logger.warning(f"[ALTERNATIVES] Tentando Dijkstra simples para diagnóstico...")
            try:
                path, cost = engine.best(s, t, params)
                if path:
                    logger.info(f"[ALTERNATIVES] ✅ Dijkstra simples encontrou rota com {len(path)} nós, custo: {cost:.2f}")
                    logger.info(f"[ALTERNATIVES] Caminho: {' -> '.join([engine.node_id(idx) for idx in path[:10]])}{'...' if len(path) > 10 else ''}")
                else:
                    logger.warning(f"[ALTERNATIVES] ❌ Dijkstra simples também não encontrou rota")
                    # Verificar conectividade básica
                    logger.info(f"[ALTERNATIVES] Verificando conectividade do nó origem (índice {s})...")
                    # Tentar encontrar qualquer caminho a partir do nó origem
                    test_paths = 0
                    test_nodes = []
                    for test_idx in range(min(20, engine.g.contents.n)):
                        if test_idx != s and test_idx != t:
                            try:
                                test_path, _ = engine.best(s, test_idx, params)
                                if test_path:
                                    test_paths += 1
                                    test_nodes.append(engine.node_id(test_idx))
                                    if len(test_nodes) >= 3:  # Limitar a 3 para não poluir log
                                        break
                            except:
                                pass
                    logger.info(f"[ALTERNATIVES] Nó origem consegue alcançar {test_paths}/20 nós de teste")
                    if test_nodes:
                        logger.info(f"[ALTERNATIVES] Exemplos de nós alcançáveis: {', '.join(test_nodes[:3])}")
                    else:
                        logger.error(f"[ALTERNATIVES] ❌ Nó origem NÃO consegue alcançar NENHUM outro nó! Grafo pode estar desconectado ou arestas não foram carregadas.")
            except Exception as e:
                logger.error(f"[ALTERNATIVES] Erro ao executar Dijkstra simples: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        if not alternatives:
            logger.warning(f"[ALTERNATIVES] Nenhuma rota encontrada entre nós {s} e {t} (IDs: {request.from_id} -> {request.to_id})")
            raise RouteNotFoundException(request.from_id, request.to_id)
        
        # Carregar dados do grafo se necessário (usar variáveis globais)
        # Nota: global já declarado no início da função (linha 450)
        if nodes_df is None or edges_df is None:
            try:
                # Tentar carregar dados híbridos primeiro
                hybrid_nodes = os.path.join(DATA_DIR, "hybrid", "nodes.csv")
                hybrid_edges = os.path.join(DATA_DIR, "hybrid", "edges.csv")
                
                if os.path.isfile(hybrid_nodes) and os.path.isfile(hybrid_edges):
                    nodes_df, edges_df = load_graph_data(hybrid_nodes, hybrid_edges)
                else:
                    # Fallback para dados integrados de SP
                    sp_integrated_nodes = os.path.join(DATA_DIR, "sp", "integrated", "integrated_nodes.csv")
                    sp_integrated_edges = os.path.join(DATA_DIR, "sp", "integrated", "integrated_edges.csv")
                    
                    if os.path.isfile(sp_integrated_nodes) and os.path.isfile(sp_integrated_edges):
                        nodes_df, edges_df = load_graph_data(sp_integrated_nodes, sp_integrated_edges)
                    else:
                        nodes_df, edges_df = load_graph_data(NODES, EDGES)
            except Exception as e:
                logger.warning(f"Não foi possível carregar dados do grafo: {e}")
                nodes_df, edges_df = None, None
        
        # Construir alternativas com dados completos
        alt_list = []
        for i, (path, cost) in enumerate(alternatives):
            # Converter índices para IDs de nós
            path_ids = [engine.node_id(idx) for idx in path]

            # Se tivermos dados do grafo carregados, usar utilitário completo para
            # calcular tempo em minutos, transferências, barreiras e modos.
            if edges_df is not None and nodes_df is not None:
                details = build_route_details(path_ids, cost, edges_df, nodes_df, request.perfil)

                alt = Alt(
                    id=i,
                    tempo_total_min=details.get("total_time_min", cost),
                    transferencias=details.get("transfers", 0),
                    path=path_ids,
                    barreiras_evitas=details.get("barriers_avoided", []),
                    modes=details.get("modes", [])
                )
            else:
                # Fallback: usar custo bruto como tempo e calcular apenas transferências/barreiras
                transfers = calculate_transfers(path_ids, edges_df) if edges_df is not None else 0
                barriers = identify_avoided_barriers(path_ids, edges_df, request.perfil) if edges_df is not None else []
                modes: list[str] = []
                if edges_df is not None:
                    segments = get_path_segments(path_ids, edges_df)
                    modes = list(set(seg["modo"] for seg in segments if seg.get("modo")))

                alt = Alt(
                    id=i,
                    tempo_total_min=cost,
                    transferencias=transfers,
                    path=path_ids,
                    barreiras_evitas=barriers,
                    modes=modes
                )

            alt_list.append(alt)
        
        logger.info(f"[ALTERNATIVES] {len(alt_list)} rotas alternativas calculadas")
        
        return AlternativesResponse(
            alternatives=alt_list,
            from_id=request.from_id,
            to_id=request.to_id,
            profile=request.perfil,
            rain=request.chuva
        )
    except ConneccityException as e:
        logger.error(f"[ALTERNATIVES] Erro Conneccity: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"[ALTERNATIVES] Erro interno: {str(e)}")
        logger.error(traceback.format_exc())
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
        
        # Garantir que as colunas 'name' e 'id' sejam strings
        # Converter NaN para string vazia antes de usar .str accessor
        nodes_df = nodes_df.copy()
        nodes_df['name'] = nodes_df['name'].astype(str).fillna('')
        nodes_df['id'] = nodes_df['id'].astype(str).fillna('')
        
        # Garantir que as colunas 'name' e 'id' sejam strings
        # Converter NaN para string vazia antes de usar .str accessor
        nodes_df = nodes_df.copy()
        nodes_df['name'] = nodes_df['name'].astype(str).fillna('')
        nodes_df['id'] = nodes_df['id'].astype(str).fillna('')
        
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
                "name": str(row['name']) if pd.notna(row['name']) else str(row['id']),
                "lat": float(row['lat']) if pd.notna(row['lat']) else 0.0,
                "lon": float(row['lon']) if pd.notna(row['lon']) else 0.0,
                "tipo": str(row['tipo']) if pd.notna(row['tipo']) else 'onibus'
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
        
        # Obter detalhes completos (usa utilitário de route_utils, não o próprio endpoint)
        details = build_route_details(path, cost, edges_df, nodes_df, request.perfil)
        
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
