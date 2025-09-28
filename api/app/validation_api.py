#!/usr/bin/env python3
"""
API endpoints para validação de dados de São Paulo
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from integration.sp_data_validator import SPDataValidator, ValidationLevel
from integration.integration_tests import SPIntegrationTests

logger = logging.getLogger(__name__)

# Router para validação
validation_router = APIRouter(prefix="/validation", tags=["Data Validation"])

# Instâncias globais
validator: Optional[SPDataValidator] = None
integration_tests: Optional[SPIntegrationTests] = None

def get_validator() -> SPDataValidator:
    """Dependency para obter o validador"""
    global validator
    if validator is None:
        validator = SPDataValidator()
    return validator

def get_integration_tests() -> SPIntegrationTests:
    """Dependency para obter os testes de integração"""
    global integration_tests
    if integration_tests is None:
        integration_tests = SPIntegrationTests()
    return integration_tests

@validation_router.post("/gtfs")
async def validate_gtfs_data(
    gtfs_data: Dict[str, Any],
    validator: SPDataValidator = Depends(get_validator)
) -> Dict[str, Any]:
    """
    Valida dados GTFS de São Paulo
    """
    try:
        logger.info("🔍 Validando dados GTFS...")
        
        result = await validator.validate_gtfs_data(gtfs_data)
        
        return {
            "validation_result": {
                "valid": result.valid,
                "score": result.score,
                "errors": result.errors,
                "warnings": result.warnings,
                "info": result.info
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro na validação GTFS: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na validação GTFS: {str(e)}")

@validation_router.post("/osm")
async def validate_osm_data(
    osm_data: Dict[str, Any],
    validator: SPDataValidator = Depends(get_validator)
) -> Dict[str, Any]:
    """
    Valida dados OSM de São Paulo
    """
    try:
        logger.info("🔍 Validando dados OSM...")
        
        result = await validator.validate_osm_data(osm_data)
        
        return {
            "validation_result": {
                "valid": result.valid,
                "score": result.score,
                "errors": result.errors,
                "warnings": result.warnings,
                "info": result.info
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro na validação OSM: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na validação OSM: {str(e)}")

@validation_router.post("/integrated")
async def validate_integrated_data(
    integrated_data: Dict[str, Any],
    validator: SPDataValidator = Depends(get_validator)
) -> Dict[str, Any]:
    """
    Valida dados integrados
    """
    try:
        logger.info("🔍 Validando dados integrados...")
        
        result = await validator.validate_integrated_data(integrated_data)
        
        return {
            "validation_result": {
                "valid": result.valid,
                "score": result.score,
                "errors": result.errors,
                "warnings": result.warnings,
                "info": result.info
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro na validação integrada: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na validação integrada: {str(e)}")

@validation_router.get("/rules")
async def get_validation_rules(
    validator: SPDataValidator = Depends(get_validator)
) -> Dict[str, Any]:
    """
    Retorna regras de validação disponíveis
    """
    try:
        rules = validator.get_validation_rules()
        
        return {
            "validation_rules": rules,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter regras de validação: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter regras: {str(e)}")

@validation_router.post("/rules/{rule_name}/enable")
async def enable_validation_rule(
    rule_name: str,
    validator: SPDataValidator = Depends(get_validator)
) -> Dict[str, Any]:
    """
    Habilita uma regra de validação
    """
    try:
        validator.enable_validation_rule(rule_name)
        
        return {
            "message": f"Regra de validação {rule_name} habilitada",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao habilitar regra: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao habilitar regra: {str(e)}")

@validation_router.post("/rules/{rule_name}/disable")
async def disable_validation_rule(
    rule_name: str,
    validator: SPDataValidator = Depends(get_validator)
) -> Dict[str, Any]:
    """
    Desabilita uma regra de validação
    """
    try:
        validator.disable_validation_rule(rule_name)
        
        return {
            "message": f"Regra de validação {rule_name} desabilitada",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao desabilitar regra: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao desabilitar regra: {str(e)}")

@validation_router.get("/stats")
async def get_validation_stats(
    validator: SPDataValidator = Depends(get_validator)
) -> Dict[str, Any]:
    """
    Retorna estatísticas de validação
    """
    try:
        stats = validator.get_validation_stats()
        
        return {
            "validation_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")

# Endpoints para testes de integração

@validation_router.post("/tests/run-full")
async def run_full_integration_test(
    background_tasks: BackgroundTasks,
    integration_tests: SPIntegrationTests = Depends(get_integration_tests)
) -> Dict[str, Any]:
    """
    Executa teste completo de integração
    """
    try:
        logger.info("🧪 Iniciando teste completo de integração...")
        
        # Executar em background
        background_tasks.add_task(integration_tests.run_full_integration_test)
        
        return {
            "message": "Teste completo de integração iniciado em background",
            "status": "running",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar teste completo: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar teste: {str(e)}")

@validation_router.post("/tests/run/{test_name}")
async def run_specific_test(
    test_name: str,
    background_tasks: BackgroundTasks,
    integration_tests: SPIntegrationTests = Depends(get_integration_tests)
) -> Dict[str, Any]:
    """
    Executa um teste específico
    """
    try:
        logger.info(f"🧪 Iniciando teste específico: {test_name}")
        
        # Executar em background
        background_tasks.add_task(integration_tests.run_specific_test, test_name)
        
        return {
            "message": f"Teste {test_name} iniciado em background",
            "status": "running",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar teste específico: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar teste: {str(e)}")

@validation_router.get("/tests/stats")
async def get_test_stats(
    integration_tests: SPIntegrationTests = Depends(get_integration_tests)
) -> Dict[str, Any]:
    """
    Retorna estatísticas dos testes
    """
    try:
        stats = integration_tests.get_test_stats()
        
        return {
            "test_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas dos testes: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")

@validation_router.post("/tests/export")
async def export_test_results(
    file_path: str = "test_results.json",
    integration_tests: SPIntegrationTests = Depends(get_integration_tests)
) -> Dict[str, Any]:
    """
    Exporta resultados dos testes
    """
    try:
        # Executar teste completo e exportar
        suite = await integration_tests.run_full_integration_test()
        await integration_tests.export_test_results(suite, file_path)
        
        return {
            "message": f"Resultados dos testes exportados para {file_path}",
            "suite_score": suite.total_score,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao exportar resultados: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao exportar resultados: {str(e)}")

# Endpoints para validação de rotas específicas

@validation_router.post("/routes/validate")
async def validate_route(
    from_stop: str,
    to_stop: str,
    integration_tests: SPIntegrationTests = Depends(get_integration_tests)
) -> Dict[str, Any]:
    """
    Valida uma rota específica
    """
    try:
        logger.info(f"🔍 Validando rota: {from_stop} -> {to_stop}")
        
        # Simular validação de rota
        route_result = await integration_tests._calculate_test_route(from_stop, to_stop)
        
        return {
            "route_validation": {
                "from_stop": from_stop,
                "to_stop": to_stop,
                "success": route_result.get('success', False),
                "duration_minutes": route_result.get('duration_minutes', 0),
                "distance_km": route_result.get('distance_km', 0),
                "accessibility_score": route_result.get('accessibility_score', 0),
                "error": route_result.get('error')
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro na validação de rota: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na validação de rota: {str(e)}")

@validation_router.get("/routes/test-routes")
async def get_test_routes(
    integration_tests: SPIntegrationTests = Depends(get_integration_tests)
) -> Dict[str, Any]:
    """
    Retorna rotas de teste disponíveis
    """
    try:
        test_routes = integration_tests.test_config['test_routes']
        
        return {
            "test_routes": [
                {
                    "from_stop": route[0],
                    "to_stop": route[1],
                    "description": f"Rota de {route[0]} para {route[1]}"
                }
                for route in test_routes
            ],
            "total_routes": len(test_routes),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter rotas de teste: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter rotas: {str(e)}")

# Endpoints para validação de acessibilidade

@validation_router.post("/accessibility/validate")
async def validate_accessibility(
    accessibility_data: Dict[str, Any],
    integration_tests: SPIntegrationTests = Depends(get_integration_tests)
) -> Dict[str, Any]:
    """
    Valida dados de acessibilidade
    """
    try:
        logger.info("🔍 Validando dados de acessibilidade...")
        
        # Analisar acessibilidade
        accessibility_score = await integration_tests._analyze_accessibility(accessibility_data)
        
        return {
            "accessibility_validation": {
                "score": accessibility_score,
                "accessible_routes": accessibility_data.get('accessible_routes', 0),
                "inaccessible_routes": accessibility_data.get('inaccessible_routes', 0),
                "accessibility_features": accessibility_data.get('accessibility_features', []),
                "barriers_found": accessibility_data.get('barriers_found', 0),
                "recommendations": [
                    "Verificar rampas de acesso",
                    "Implementar piso tátil",
                    "Melhorar sinalização"
                ] if accessibility_score < 0.8 else []
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro na validação de acessibilidade: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na validação de acessibilidade: {str(e)}")

# Endpoints para validação de risco de alagamento

@validation_router.post("/flood-risk/validate")
async def validate_flood_risk(
    flood_data: Dict[str, Any],
    integration_tests: SPIntegrationTests = Depends(get_integration_tests)
) -> Dict[str, Any]:
    """
    Valida dados de risco de alagamento
    """
    try:
        logger.info("🔍 Validando dados de risco de alagamento...")
        
        # Analisar risco de alagamento
        flood_score = await integration_tests._analyze_flood_risk(flood_data)
        
        return {
            "flood_risk_validation": {
                "score": flood_score,
                "high_risk_areas": flood_data.get('high_risk_areas', 0),
                "medium_risk_areas": flood_data.get('medium_risk_areas', 0),
                "low_risk_areas": flood_data.get('low_risk_areas', 0),
                "flood_prone_routes": flood_data.get('flood_prone_routes', 0),
                "risk_level": "HIGH" if flood_score < 0.3 else "MEDIUM" if flood_score < 0.7 else "LOW",
                "recommendations": [
                    "Evitar rotas em áreas de alto risco",
                    "Implementar sistema de alerta",
                    "Melhorar drenagem urbana"
                ] if flood_score < 0.7 else []
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro na validação de risco de alagamento: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na validação de risco: {str(e)}")

# Endpoints para configuração

@validation_router.get("/config")
async def get_validation_config(
    validator: SPDataValidator = Depends(get_validator),
    integration_tests: SPIntegrationTests = Depends(get_integration_tests)
) -> Dict[str, Any]:
    """
    Retorna configuração de validação
    """
    try:
        config = {
            "validator_config": {
                "validation_level": validator.validation_level.value,
                "gtfs_config": validator.gtfs_validation_config,
                "osm_config": validator.osm_validation_config
            },
            "test_config": integration_tests.test_config,
            "timestamp": datetime.now().isoformat()
        }
        
        return config
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter configuração: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter configuração: {str(e)}")

@validation_router.post("/config/validation-level")
async def update_validation_level(
    level: str,
    validator: SPDataValidator = Depends(get_validator)
) -> Dict[str, Any]:
    """
    Atualiza nível de validação
    """
    try:
        validation_level = ValidationLevel(level)
        validator.update_validation_level(validation_level)
        
        return {
            "message": f"Nível de validação atualizado para: {level}",
            "timestamp": datetime.now().isoformat()
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Nível de validação inválido: {level}")
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar nível de validação: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar nível: {str(e)}")


