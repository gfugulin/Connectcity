#!/usr/bin/env python3
"""
Script para testar o sistema completo de validação
"""
import asyncio
import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Adicionar diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from integration.sp_data_validator import SPDataValidator, ValidationLevel
from integration.integration_tests import SPIntegrationTests

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_validator_initialization():
    """Testa inicialização do validador"""
    try:
        logger.info("🔧 Testando inicialização do validador...")
        
        validator = SPDataValidator()
        
        # Verificar configurações
        stats = validator.get_validation_stats()
        rules = validator.get_validation_rules()
        
        logger.info(f"✅ Validador inicializado - {len(rules)} regras ativas")
        return validator
        
    except Exception as e:
        logger.error(f"❌ Erro na inicialização do validador: {e}")
        return None

async def test_gtfs_validation(validator):
    """Testa validação de dados GTFS"""
    try:
        logger.info("🔍 Testando validação GTFS...")
        
        # Dados de teste GTFS
        test_gtfs_data = {
            'stops': [
                {
                    'stop_id': '1',
                    'stop_name': 'Estação Sé',
                    'stop_lat': -23.5505,
                    'stop_lon': -46.6333
                },
                {
                    'stop_id': '2',
                    'stop_name': 'Estação Paulista',
                    'stop_lat': -23.5614,
                    'stop_lon': -46.6565
                },
                {
                    'stop_id': '3',
                    'stop_name': 'Terminal Bandeira',
                    'stop_lat': -23.5500,
                    'stop_lon': -46.6300
                }
            ],
            'routes': [
                {
                    'route_id': '1',
                    'route_short_name': '107P',
                    'route_long_name': 'Terminal Bandeira - Estação Sé'
                },
                {
                    'route_id': '2',
                    'route_short_name': '175P',
                    'route_long_name': 'Terminal Bandeira - Estação Paulista'
                }
            ],
            'trips': [
                {
                    'trip_id': '1',
                    'route_id': '1',
                    'service_id': '1'
                }
            ],
            'stop_times': [
                {
                    'trip_id': '1',
                    'stop_id': '1',
                    'arrival_time': '06:00:00',
                    'departure_time': '06:00:00'
                }
            ]
        }
        
        # Validar dados
        result = await validator.validate_gtfs_data(test_gtfs_data)
        
        logger.info(f"📊 Resultado da validação GTFS:")
        logger.info(f"  - Válido: {result.valid}")
        logger.info(f"  - Score: {result.score:.2f}")
        logger.info(f"  - Erros: {len(result.errors)}")
        logger.info(f"  - Warnings: {len(result.warnings)}")
        logger.info(f"  - Info: {len(result.info)}")
        
        if result.errors:
            for error in result.errors:
                logger.warning(f"  ❌ {error}")
        
        if result.warnings:
            for warning in result.warnings:
                logger.warning(f"  ⚠️ {warning}")
        
        if result.info:
            for info in result.info:
                logger.info(f"  ℹ️ {info}")
        
        return result.valid and result.score >= 0.7
        
    except Exception as e:
        logger.error(f"❌ Erro na validação GTFS: {e}")
        return False

async def test_osm_validation(validator):
    """Testa validação de dados OSM"""
    try:
        logger.info("🔍 Testando validação OSM...")
        
        # Dados de teste OSM
        test_osm_data = {
            'nodes': [
                {
                    'id': '1',
                    'lat': -23.5505,
                    'lon': -46.6333,
                    'tags': {'highway': 'bus_stop', 'name': 'Estação Sé'}
                },
                {
                    'id': '2',
                    'lat': -23.5614,
                    'lon': -46.6565,
                    'tags': {'highway': 'bus_stop', 'name': 'Estação Paulista'}
                }
            ],
            'ways': [
                {
                    'id': '1',
                    'nodes': ['1', '2'],
                    'tags': {
                        'highway': 'primary',
                        'name': 'Avenida Paulista',
                        'wheelchair': 'yes',
                        'tactile_paving': 'yes'
                    }
                },
                {
                    'id': '2',
                    'nodes': ['2'],
                    'tags': {
                        'highway': 'secondary',
                        'name': 'Rua da Consolação',
                        'wheelchair': 'no'
                    }
                }
            ],
            'relations': []
        }
        
        # Validar dados
        result = await validator.validate_osm_data(test_osm_data)
        
        logger.info(f"📊 Resultado da validação OSM:")
        logger.info(f"  - Válido: {result.valid}")
        logger.info(f"  - Score: {result.score:.2f}")
        logger.info(f"  - Erros: {len(result.errors)}")
        logger.info(f"  - Warnings: {len(result.warnings)}")
        logger.info(f"  - Info: {len(result.info)}")
        
        if result.errors:
            for error in result.errors:
                logger.warning(f"  ❌ {error}")
        
        if result.warnings:
            for warning in result.warnings:
                logger.warning(f"  ⚠️ {warning}")
        
        if result.info:
            for info in result.info:
                logger.info(f"  ℹ️ {info}")
        
        return result.valid and result.score >= 0.7
        
    except Exception as e:
        logger.error(f"❌ Erro na validação OSM: {e}")
        return False

async def test_integrated_validation(validator):
    """Testa validação de dados integrados"""
    try:
        logger.info("🔍 Testando validação de dados integrados...")
        
        # Dados de teste integrados
        test_integrated_data = {
            'nodes': [
                {
                    'id': '1',
                    'type': 'gtfs_stop',
                    'lat': -23.5505,
                    'lon': -46.6333,
                    'name': 'Estação Sé',
                    'accessibility': 'accessible'
                },
                {
                    'id': '2',
                    'type': 'osm_node',
                    'lat': -23.5614,
                    'lon': -46.6565,
                    'name': 'Estação Paulista',
                    'accessibility': 'accessible'
                }
            ],
            'edges': [
                {
                    'id': '1',
                    'type': 'gtfs_route',
                    'from_node': '1',
                    'to_node': '2',
                    'duration': 30,
                    'accessibility': 'accessible'
                },
                {
                    'id': '2',
                    'type': 'osm_way',
                    'from_node': '1',
                    'to_node': '2',
                    'distance': 5.0,
                    'accessibility': 'accessible'
                }
            ]
        }
        
        # Validar dados
        result = await validator.validate_integrated_data(test_integrated_data)
        
        logger.info(f"📊 Resultado da validação integrada:")
        logger.info(f"  - Válido: {result.valid}")
        logger.info(f"  - Score: {result.score:.2f}")
        logger.info(f"  - Erros: {len(result.errors)}")
        logger.info(f"  - Warnings: {len(result.warnings)}")
        logger.info(f"  - Info: {len(result.info)}")
        
        if result.errors:
            for error in result.errors:
                logger.warning(f"  ❌ {error}")
        
        if result.warnings:
            for warning in result.warnings:
                logger.warning(f"  ⚠️ {warning}")
        
        if result.info:
            for info in result.info:
                logger.info(f"  ℹ️ {info}")
        
        return result.valid and result.score >= 0.7
        
    except Exception as e:
        logger.error(f"❌ Erro na validação integrada: {e}")
        return False

async def test_integration_tests():
    """Testa testes de integração"""
    try:
        logger.info("🧪 Testando testes de integração...")
        
        integration_tests = SPIntegrationTests()
        
        # Executar teste completo
        suite = await integration_tests.run_full_integration_test()
        
        logger.info(f"📊 Resultado dos testes de integração:")
        logger.info(f"  - Score total: {suite.total_score:.2f}")
        logger.info(f"  - Total de testes: {len(suite.tests)}")
        logger.info(f"  - Duração: {(suite.end_time - suite.start_time).total_seconds():.2f}s")
        
        # Mostrar resultados individuais
        for test in suite.tests:
            status_emoji = "✅" if test.status.value == "passed" else "❌"
            logger.info(f"  {status_emoji} {test.name}: {test.status.value} (Score: {test.score:.2f})")
            
            if test.errors:
                for error in test.errors:
                    logger.warning(f"    ❌ {error}")
            
            if test.warnings:
                for warning in test.warnings:
                    logger.warning(f"    ⚠️ {warning}")
            
            if test.info:
                for info in test.info:
                    logger.info(f"    ℹ️ {info}")
        
        # Exportar resultados
        export_file = "test_validation_results.json"
        await integration_tests.export_test_results(suite, export_file)
        logger.info(f"📁 Resultados exportados para: {export_file}")
        
        return suite.total_score >= 0.7
        
    except Exception as e:
        logger.error(f"❌ Erro nos testes de integração: {e}")
        return False

async def test_validation_rules(validator):
    """Testa regras de validação"""
    try:
        logger.info("📋 Testando regras de validação...")
        
        # Obter regras
        rules = validator.get_validation_rules()
        
        logger.info(f"📊 Regras de validação disponíveis: {len(rules)}")
        
        for rule in rules:
            logger.info(f"  - {rule['name']}: {rule['description']}")
            logger.info(f"    Nível: {rule['level']}, Peso: {rule['weight']}, Ativa: {rule['enabled']}")
        
        # Testar habilitação/desabilitação de regras
        validator.disable_validation_rule('naming_conventions')
        validator.enable_validation_rule('naming_conventions')
        
        logger.info("✅ Regras de validação testadas")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de regras: {e}")
        return False

async def test_validation_levels(validator):
    """Testa diferentes níveis de validação"""
    try:
        logger.info("📊 Testando diferentes níveis de validação...")
        
        levels = [ValidationLevel.STRICT, ValidationLevel.MODERATE, ValidationLevel.LENIENT]
        
        for level in levels:
            logger.info(f"🔍 Testando nível: {level.value}")
            validator.update_validation_level(level)
            
            # Verificar se foi aplicado
            current_level = validator.validation_level
            logger.info(f"  Nível atual: {current_level.value}")
        
        # Voltar para moderado
        validator.update_validation_level(ValidationLevel.MODERATE)
        logger.info("✅ Níveis de validação testados")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de níveis: {e}")
        return False

async def test_validation_stats(validator):
    """Testa estatísticas de validação"""
    try:
        logger.info("📈 Testando estatísticas de validação...")
        
        # Obter estatísticas
        stats = validator.get_validation_stats()
        
        logger.info(f"📊 Estatísticas de validação:")
        logger.info(f"  - Total de validações: {stats['total_validations']}")
        logger.info(f"  - Validações bem-sucedidas: {stats['successful_validations']}")
        logger.info(f"  - Validações falharam: {stats['failed_validations']}")
        logger.info(f"  - Taxa de sucesso: {stats['success_rate']:.2f}")
        logger.info(f"  - Score médio: {stats['avg_score']:.2f}")
        logger.info(f"  - Nível de validação: {stats['validation_level']}")
        logger.info(f"  - Regras ativas: {stats['active_rules']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de estatísticas: {e}")
        return False

async def main():
    """Função principal de teste"""
    try:
        logger.info("🧪 === TESTE COMPLETO DE VALIDAÇÃO ===")
        
        # Teste 1: Inicialização do validador
        validator = await test_validator_initialization()
        if not validator:
            logger.error("❌ Falha na inicialização - abortando testes")
            return False
        
        # Teste 2: Validação GTFS
        success1 = await test_gtfs_validation(validator)
        
        # Teste 3: Validação OSM
        success2 = await test_osm_validation(validator)
        
        # Teste 4: Validação integrada
        success3 = await test_integrated_validation(validator)
        
        # Teste 5: Testes de integração
        success4 = await test_integration_tests()
        
        # Teste 6: Regras de validação
        success5 = await test_validation_rules(validator)
        
        # Teste 7: Níveis de validação
        success6 = await test_validation_levels(validator)
        
        # Teste 8: Estatísticas
        success7 = await test_validation_stats(validator)
        
        # Resumo dos testes
        tests = [
            ("Inicialização", True),
            ("Validação GTFS", success1),
            ("Validação OSM", success2),
            ("Validação Integrada", success3),
            ("Testes de Integração", success4),
            ("Regras de Validação", success5),
            ("Níveis de Validação", success6),
            ("Estatísticas", success7)
        ]
        
        logger.info("\n📊 === RESUMO DOS TESTES ===")
        passed = 0
        for test_name, success in tests:
            status = "✅ PASSOU" if success else "❌ FALHOU"
            logger.info(f"{test_name}: {status}")
            if success:
                passed += 1
        
        logger.info(f"\n🎯 Resultado: {passed}/{len(tests)} testes passaram")
        
        if passed == len(tests):
            logger.info("🎉 TODOS OS TESTES PASSARAM!")
            logger.info("✅ Sistema de validação funcionando corretamente")
            return True
        else:
            logger.warning(f"⚠️ {len(tests) - passed} testes falharam")
            return False
        
    except Exception as e:
        logger.error(f"❌ Erro nos testes: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
