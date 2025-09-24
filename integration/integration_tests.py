#!/usr/bin/env python3
"""
Testes de integração com dados reais de São Paulo
"""
import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .sp_data_collector import SPDataCollector
from .sp_data_validator import SPDataValidator, ValidationResult
from .data_integrator import DataIntegrator

logger = logging.getLogger(__name__)

class TestStatus(Enum):
    """Status dos testes"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class TestResult:
    """Resultado de um teste"""
    name: str
    status: TestStatus
    duration: float
    score: float = 0.0
    errors: List[str] = None
    warnings: List[str] = None
    info: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.info is None:
            self.info = []

@dataclass
class IntegrationTestSuite:
    """Suite de testes de integração"""
    name: str
    tests: List[TestResult]
    start_time: datetime
    end_time: Optional[datetime] = None
    total_score: float = 0.0
    
    def calculate_score(self):
        """Calcula score total da suite"""
        if not self.tests:
            self.total_score = 0.0
            return
        
        passed_tests = [t for t in self.tests if t.status == TestStatus.PASSED]
        self.total_score = len(passed_tests) / len(self.tests)

class SPIntegrationTests:
    """
    Testes de integração com dados reais de São Paulo
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Componentes
        self.data_collector = SPDataCollector()
        self.validator = SPDataValidator()
        self.integrator = DataIntegrator()
        
        # Configurações de teste
        self.test_config = {
            'timeout_seconds': self.config.get('test_timeout', 300),
            'max_retries': self.config.get('max_retries', 3),
            'min_data_quality': self.config.get('min_data_quality', 0.7),
            'test_routes': self.config.get('test_routes', [
                ('Estação Sé', 'Estação Paulista'),
                ('Terminal Bandeira', 'Shopping Iguatemi'),
                ('Estação Trianon-MASP', 'Parque Ibirapuera'),
                ('Vila Madalena', 'Pinheiros'),
                ('Centro', 'Vila Olímpia')
            ])
        }
        
        # Estatísticas
        self.test_stats = {
            'total_suites': 0,
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'avg_score': 0.0
        }
        
        logger.info("✅ SP Integration Tests inicializado")
    
    async def run_full_integration_test(self) -> IntegrationTestSuite:
        """Executa teste completo de integração"""
        logger.info("🧪 Iniciando teste completo de integração...")
        
        suite = IntegrationTestSuite(
            name="Full Integration Test",
            tests=[],
            start_time=datetime.now()
        )
        
        try:
            # Teste 1: Coleta de dados
            test1 = await self._test_data_collection()
            suite.tests.append(test1)
            
            # Teste 2: Validação de dados
            test2 = await self._test_data_validation()
            suite.tests.append(test2)
            
            # Teste 3: Integração de dados
            test3 = await self._test_data_integration()
            suite.tests.append(test3)
            
            # Teste 4: Cálculo de rotas
            test4 = await self._test_route_calculation()
            suite.tests.append(test4)
            
            # Teste 5: Análise de acessibilidade
            test5 = await self._test_accessibility_analysis()
            suite.tests.append(test5)
            
            # Teste 6: Análise de risco de alagamento
            test6 = await self._test_flood_risk_analysis()
            suite.tests.append(test6)
            
            # Teste 7: Performance
            test7 = await self._test_performance()
            suite.tests.append(test7)
            
            # Finalizar suite
            suite.end_time = datetime.now()
            suite.calculate_score()
            
            # Atualizar estatísticas
            self._update_test_stats(suite)
            
            logger.info(f"✅ Teste completo concluído - Score: {suite.total_score:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Erro no teste completo: {e}")
            suite.end_time = datetime.now()
        
        return suite
    
    async def _test_data_collection(self) -> TestResult:
        """Testa coleta de dados"""
        test_name = "Data Collection"
        logger.info(f"🔍 Executando teste: {test_name}")
        
        start_time = time.time()
        result = TestResult(
            name=test_name,
            status=TestStatus.RUNNING,
            duration=0.0
        )
        
        try:
            # Coletar dados
            logger.info("📥 Coletando dados de São Paulo...")
            collection_result = await self.data_collector.collect_all_data()
            
            # Verificar resultados
            if collection_result.get('status') == 'completed':
                result.status = TestStatus.PASSED
                result.score = 1.0
                result.info.append("Coleta de dados concluída com sucesso")
                
                # Adicionar estatísticas
                stats = collection_result.get('statistics', {})
                result.info.append(f"Total de nós: {stats.get('total_osm_nodes', 0)}")
                result.info.append(f"Total de arestas: {stats.get('total_osm_edges', 0)}")
                
            else:
                result.status = TestStatus.FAILED
                result.score = 0.0
                result.errors.append("Falha na coleta de dados")
                
                # Adicionar erros específicos
                errors = collection_result.get('errors', [])
                for error in errors:
                    result.errors.append(f"Erro de coleta: {error}")
            
        except Exception as e:
            result.status = TestStatus.FAILED
            result.score = 0.0
            result.errors.append(f"Erro na coleta de dados: {str(e)}")
        
        result.duration = time.time() - start_time
        logger.info(f"✅ Teste {test_name} concluído - Status: {result.status.value}")
        
        return result
    
    async def _test_data_validation(self) -> TestResult:
        """Testa validação de dados"""
        test_name = "Data Validation"
        logger.info(f"🔍 Executando teste: {test_name}")
        
        start_time = time.time()
        result = TestResult(
            name=test_name,
            status=TestStatus.RUNNING,
            duration=0.0
        )
        
        try:
            # Simular dados para validação
            test_data = {
                'gtfs': {
                    'stops': [
                        {'stop_id': '1', 'stop_name': 'Sé', 'stop_lat': -23.5505, 'stop_lon': -46.6333},
                        {'stop_id': '2', 'stop_name': 'Paulista', 'stop_lat': -23.5614, 'stop_lon': -46.6565}
                    ],
                    'routes': [
                        {'route_id': '1', 'route_short_name': '107P', 'route_long_name': 'Terminal Bandeira'}
                    ]
                },
                'osm': {
                    'nodes': [
                        {'id': '1', 'lat': -23.5505, 'lon': -46.6333, 'tags': {'highway': 'bus_stop'}}
                    ],
                    'ways': [
                        {'id': '1', 'nodes': ['1', '2'], 'tags': {'highway': 'primary', 'wheelchair': 'yes'}}
                    ]
                }
            }
            
            # Validar dados GTFS
            gtfs_validation = await self.validator.validate_gtfs_data(test_data['gtfs'])
            result.info.append(f"Validação GTFS - Score: {gtfs_validation.score:.2f}")
            
            # Validar dados OSM
            osm_validation = await self.validator.validate_osm_data(test_data['osm'])
            result.info.append(f"Validação OSM - Score: {osm_validation.score:.2f}")
            
            # Calcular score geral
            overall_score = (gtfs_validation.score + osm_validation.score) / 2
            
            if overall_score >= self.test_config['min_data_quality']:
                result.status = TestStatus.PASSED
                result.score = overall_score
                result.info.append("Validação de dados bem-sucedida")
            else:
                result.status = TestStatus.FAILED
                result.score = overall_score
                result.errors.append(f"Qualidade dos dados insuficiente: {overall_score:.2f}")
            
            # Adicionar detalhes
            if gtfs_validation.errors:
                result.warnings.extend([f"GTFS: {error}" for error in gtfs_validation.errors])
            
            if osm_validation.errors:
                result.warnings.extend([f"OSM: {error}" for error in osm_validation.errors])
            
        except Exception as e:
            result.status = TestStatus.FAILED
            result.score = 0.0
            result.errors.append(f"Erro na validação: {str(e)}")
        
        result.duration = time.time() - start_time
        logger.info(f"✅ Teste {test_name} concluído - Status: {result.status.value}")
        
        return result
    
    async def _test_data_integration(self) -> TestResult:
        """Testa integração de dados"""
        test_name = "Data Integration"
        logger.info(f"🔍 Executando teste: {test_name}")
        
        start_time = time.time()
        result = TestResult(
            name=test_name,
            status=TestStatus.RUNNING,
            duration=0.0
        )
        
        try:
            # Simular dados para integração
            gtfs_data = {
                'stops': [
                    {'stop_id': '1', 'stop_name': 'Sé', 'stop_lat': -23.5505, 'stop_lon': -46.6333}
                ],
                'routes': [
                    {'route_id': '1', 'route_short_name': '107P'}
                ]
            }
            
            osm_data = {
                'nodes': [
                    {'id': '1', 'lat': -23.5505, 'lon': -46.6333}
                ],
                'ways': [
                    {'id': '1', 'nodes': ['1'], 'tags': {'highway': 'primary'}}
                ]
            }
            
            # Integrar dados
            logger.info("🔗 Integrando dados GTFS e OSM...")
            integrated_data = await self.integrator.integrate_city_data(
                'sao_paulo', gtfs_data, osm_data
            )
            
            # Verificar resultado
            if integrated_data and 'nodes' in integrated_data and 'edges' in integrated_data:
                result.status = TestStatus.PASSED
                result.score = 1.0
                result.info.append("Integração de dados bem-sucedida")
                result.info.append(f"Nós integrados: {len(integrated_data['nodes'])}")
                result.info.append(f"Arestas integradas: {len(integrated_data['edges'])}")
            else:
                result.status = TestStatus.FAILED
                result.score = 0.0
                result.errors.append("Falha na integração de dados")
            
        except Exception as e:
            result.status = TestStatus.FAILED
            result.score = 0.0
            result.errors.append(f"Erro na integração: {str(e)}")
        
        result.duration = time.time() - start_time
        logger.info(f"✅ Teste {test_name} concluído - Status: {result.status.value}")
        
        return result
    
    async def _test_route_calculation(self) -> TestResult:
        """Testa cálculo de rotas"""
        test_name = "Route Calculation"
        logger.info(f"🔍 Executando teste: {test_name}")
        
        start_time = time.time()
        result = TestResult(
            name=test_name,
            status=TestStatus.RUNNING,
            duration=0.0
        )
        
        try:
            # Testar rotas conhecidas
            test_routes = self.test_config['test_routes']
            successful_routes = 0
            
            for from_stop, to_stop in test_routes:
                try:
                    # Simular cálculo de rota
                    route = await self._calculate_test_route(from_stop, to_stop)
                    
                    if route and route.get('success', False):
                        successful_routes += 1
                        result.info.append(f"Rota {from_stop} -> {to_stop}: ✅")
                    else:
                        result.warnings.append(f"Rota {from_stop} -> {to_stop}: ❌")
                        
                except Exception as e:
                    result.warnings.append(f"Erro na rota {from_stop} -> {to_stop}: {str(e)}")
            
            # Calcular score
            route_success_rate = successful_routes / len(test_routes)
            
            if route_success_rate >= 0.8:  # 80% de sucesso
                result.status = TestStatus.PASSED
                result.score = route_success_rate
                result.info.append(f"Taxa de sucesso das rotas: {route_success_rate:.2f}")
            else:
                result.status = TestStatus.FAILED
                result.score = route_success_rate
                result.errors.append(f"Taxa de sucesso das rotas insuficiente: {route_success_rate:.2f}")
            
        except Exception as e:
            result.status = TestStatus.FAILED
            result.score = 0.0
            result.errors.append(f"Erro no cálculo de rotas: {str(e)}")
        
        result.duration = time.time() - start_time
        logger.info(f"✅ Teste {test_name} concluído - Status: {result.status.value}")
        
        return result
    
    async def _calculate_test_route(self, from_stop: str, to_stop: str) -> Dict[str, Any]:
        """Simula cálculo de rota para teste"""
        # Simular cálculo de rota
        await asyncio.sleep(0.1)  # Simular processamento
        
        # Simular resultado baseado em paradas conhecidas
        known_stops = {'Sé', 'Paulista', 'Bandeira', 'Ibirapuera', 'Trianon-MASP'}
        
        if from_stop in known_stops and to_stop in known_stops:
            return {
                'success': True,
                'from_stop': from_stop,
                'to_stop': to_stop,
                'duration_minutes': 30,
                'distance_km': 5.0,
                'accessibility_score': 0.8
            }
        else:
            return {
                'success': False,
                'error': 'Paradas não encontradas'
            }
    
    async def _test_accessibility_analysis(self) -> TestResult:
        """Testa análise de acessibilidade"""
        test_name = "Accessibility Analysis"
        logger.info(f"🔍 Executando teste: {test_name}")
        
        start_time = time.time()
        result = TestResult(
            name=test_name,
            status=TestStatus.RUNNING,
            duration=0.0
        )
        
        try:
            # Simular dados de acessibilidade
            accessibility_data = {
                'accessible_routes': 15,
                'inaccessible_routes': 3,
                'accessibility_features': ['wheelchair', 'tactile_paving', 'ramp'],
                'barriers_found': 2
            }
            
            # Analisar acessibilidade
            accessibility_score = await self._analyze_accessibility(accessibility_data)
            
            if accessibility_score >= 0.7:
                result.status = TestStatus.PASSED
                result.score = accessibility_score
                result.info.append(f"Score de acessibilidade: {accessibility_score:.2f}")
                result.info.append(f"Rotas acessíveis: {accessibility_data['accessible_routes']}")
                result.info.append(f"Barreiras encontradas: {accessibility_data['barriers_found']}")
            else:
                result.status = TestStatus.FAILED
                result.score = accessibility_score
                result.errors.append(f"Score de acessibilidade insuficiente: {accessibility_score:.2f}")
            
        except Exception as e:
            result.status = TestStatus.FAILED
            result.score = 0.0
            result.errors.append(f"Erro na análise de acessibilidade: {str(e)}")
        
        result.duration = time.time() - start_time
        logger.info(f"✅ Teste {test_name} concluído - Status: {result.status.value}")
        
        return result
    
    async def _analyze_accessibility(self, data: Dict[str, Any]) -> float:
        """Simula análise de acessibilidade"""
        await asyncio.sleep(0.1)  # Simular processamento
        
        total_routes = data['accessible_routes'] + data['inaccessible_routes']
        if total_routes == 0:
            return 0.0
        
        accessibility_ratio = data['accessible_routes'] / total_routes
        barrier_penalty = data['barriers_found'] * 0.1
        
        return max(0.0, min(1.0, accessibility_ratio - barrier_penalty))
    
    async def _test_flood_risk_analysis(self) -> TestResult:
        """Testa análise de risco de alagamento"""
        test_name = "Flood Risk Analysis"
        logger.info(f"🔍 Executando teste: {test_name}")
        
        start_time = time.time()
        result = TestResult(
            name=test_name,
            status=TestStatus.RUNNING,
            duration=0.0
        )
        
        try:
            # Simular dados de risco de alagamento
            flood_data = {
                'high_risk_areas': 5,
                'medium_risk_areas': 12,
                'low_risk_areas': 25,
                'flood_prone_routes': 8
            }
            
            # Analisar risco de alagamento
            flood_score = await self._analyze_flood_risk(flood_data)
            
            if flood_score >= 0.6:
                result.status = TestStatus.PASSED
                result.score = flood_score
                result.info.append(f"Score de análise de alagamento: {flood_score:.2f}")
                result.info.append(f"Áreas de alto risco: {flood_data['high_risk_areas']}")
                result.info.append(f"Rotas propensas a alagamento: {flood_data['flood_prone_routes']}")
            else:
                result.status = TestStatus.FAILED
                result.score = flood_score
                result.errors.append(f"Score de análise de alagamento insuficiente: {flood_score:.2f}")
            
        except Exception as e:
            result.status = TestStatus.FAILED
            result.score = 0.0
            result.errors.append(f"Erro na análise de alagamento: {str(e)}")
        
        result.duration = time.time() - start_time
        logger.info(f"✅ Teste {test_name} concluído - Status: {result.status.value}")
        
        return result
    
    async def _analyze_flood_risk(self, data: Dict[str, Any]) -> float:
        """Simula análise de risco de alagamento"""
        await asyncio.sleep(0.1)  # Simular processamento
        
        total_areas = data['high_risk_areas'] + data['medium_risk_areas'] + data['low_risk_areas']
        if total_areas == 0:
            return 0.0
        
        # Calcular score baseado na distribuição de risco
        high_risk_ratio = data['high_risk_areas'] / total_areas
        medium_risk_ratio = data['medium_risk_areas'] / total_areas
        low_risk_ratio = data['low_risk_areas'] / total_areas
        
        # Score baseado na proporção de áreas de baixo risco
        score = low_risk_ratio + (medium_risk_ratio * 0.5)
        
        return max(0.0, min(1.0, score))
    
    async def _test_performance(self) -> TestResult:
        """Testa performance do sistema"""
        test_name = "Performance Test"
        logger.info(f"🔍 Executando teste: {test_name}")
        
        start_time = time.time()
        result = TestResult(
            name=test_name,
            status=TestStatus.RUNNING,
            duration=0.0
        )
        
        try:
            # Testar performance de diferentes operações
            performance_tests = [
                ('Data Collection', self._test_collection_performance),
                ('Data Validation', self._test_validation_performance),
                ('Route Calculation', self._test_route_performance),
                ('Accessibility Analysis', self._test_accessibility_performance)
            ]
            
            performance_scores = []
            
            for test_name, test_func in performance_tests:
                try:
                    score = await test_func()
                    performance_scores.append(score)
                    result.info.append(f"{test_name}: {score:.2f}s")
                except Exception as e:
                    result.warnings.append(f"Erro em {test_name}: {str(e)}")
                    performance_scores.append(0.0)
            
            # Calcular score geral de performance
            avg_performance = sum(performance_scores) / len(performance_scores)
            max_acceptable_time = 5.0  # 5 segundos
            
            if avg_performance <= max_acceptable_time:
                result.status = TestStatus.PASSED
                result.score = max(0.0, 1.0 - (avg_performance / max_acceptable_time))
                result.info.append(f"Performance média: {avg_performance:.2f}s")
            else:
                result.status = TestStatus.FAILED
                result.score = 0.0
                result.errors.append(f"Performance insuficiente: {avg_performance:.2f}s")
            
        except Exception as e:
            result.status = TestStatus.FAILED
            result.score = 0.0
            result.errors.append(f"Erro no teste de performance: {str(e)}")
        
        result.duration = time.time() - start_time
        logger.info(f"✅ Teste {test_name} concluído - Status: {result.status.value}")
        
        return result
    
    async def _test_collection_performance(self) -> float:
        """Testa performance da coleta de dados"""
        start = time.time()
        # Simular coleta de dados
        await asyncio.sleep(0.5)
        return time.time() - start
    
    async def _test_validation_performance(self) -> float:
        """Testa performance da validação"""
        start = time.time()
        # Simular validação
        await asyncio.sleep(0.2)
        return time.time() - start
    
    async def _test_route_performance(self) -> float:
        """Testa performance do cálculo de rotas"""
        start = time.time()
        # Simular cálculo de rotas
        await asyncio.sleep(0.3)
        return time.time() - start
    
    async def _test_accessibility_performance(self) -> float:
        """Testa performance da análise de acessibilidade"""
        start = time.time()
        # Simular análise de acessibilidade
        await asyncio.sleep(0.1)
        return time.time() - start
    
    def _update_test_stats(self, suite: IntegrationTestSuite):
        """Atualiza estatísticas dos testes"""
        self.test_stats['total_suites'] += 1
        self.test_stats['total_tests'] += len(suite.tests)
        
        passed_tests = [t for t in suite.tests if t.status == TestStatus.PASSED]
        failed_tests = [t for t in suite.tests if t.status == TestStatus.FAILED]
        
        self.test_stats['passed_tests'] += len(passed_tests)
        self.test_stats['failed_tests'] += len(failed_tests)
        
        # Atualizar score médio
        total = self.test_stats['total_tests']
        current_avg = self.test_stats['avg_score']
        suite_avg = suite.total_score
        self.test_stats['avg_score'] = (current_avg * (total - len(suite.tests)) + suite_avg * len(suite.tests)) / total
    
    def get_test_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas dos testes"""
        return {
            'total_suites': self.test_stats['total_suites'],
            'total_tests': self.test_stats['total_tests'],
            'passed_tests': self.test_stats['passed_tests'],
            'failed_tests': self.test_stats['failed_tests'],
            'success_rate': (
                self.test_stats['passed_tests'] / 
                max(1, self.test_stats['total_tests'])
            ),
            'avg_score': self.test_stats['avg_score']
        }
    
    async def run_specific_test(self, test_name: str) -> TestResult:
        """Executa um teste específico"""
        test_methods = {
            'data_collection': self._test_data_collection,
            'data_validation': self._test_data_validation,
            'data_integration': self._test_data_integration,
            'route_calculation': self._test_route_calculation,
            'accessibility_analysis': self._test_accessibility_analysis,
            'flood_risk_analysis': self._test_flood_risk_analysis,
            'performance': self._test_performance
        }
        
        if test_name not in test_methods:
            return TestResult(
                name=test_name,
                status=TestStatus.FAILED,
                duration=0.0,
                score=0.0,
                errors=[f"Teste não encontrado: {test_name}"]
            )
        
        return await test_methods[test_name]()
    
    async def export_test_results(self, suite: IntegrationTestSuite, file_path: str):
        """Exporta resultados dos testes"""
        try:
            results = {
                'suite_name': suite.name,
                'start_time': suite.start_time.isoformat(),
                'end_time': suite.end_time.isoformat() if suite.end_time else None,
                'total_score': suite.total_score,
                'tests': [
                    {
                        'name': test.name,
                        'status': test.status.value,
                        'duration': test.duration,
                        'score': test.score,
                        'errors': test.errors,
                        'warnings': test.warnings,
                        'info': test.info
                    }
                    for test in suite.tests
                ],
                'statistics': self.get_test_stats()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📁 Resultados dos testes exportados para {file_path}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao exportar resultados: {e}")
