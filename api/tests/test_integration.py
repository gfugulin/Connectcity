import pytest
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestIntegrationScenarios:
    """Testes de integração com cenários reais"""
    
    def test_complete_workflow_pcd_user(self):
        """Testa workflow completo para usuário PcD"""
        # 1. Verificar saúde da API
        health_response = client.get('/health')
        assert health_response.status_code == 200
        
        # 2. Obter perfis disponíveis
        profiles_response = client.get('/profiles')
        assert profiles_response.status_code == 200
        profiles = profiles_response.json()
        assert 'pcd' in profiles['profiles']
        
        # 3. Obter nós disponíveis
        nodes_response = client.get('/nodes')
        assert nodes_response.status_code == 200
        nodes = nodes_response.json()
        assert len(nodes['nodes']) > 0
        
        # 4. Calcular rota para PcD
        route_payload = {
            "from": "A",
            "to": "E",
            "perfil": "pcd",
            "chuva": False
        }
        route_response = client.post('/route', json=route_payload)
        assert route_response.status_code == 200
        route_data = route_response.json()
        
        # 5. Obter alternativas
        alt_payload = {
            "from": "A",
            "to": "E",
            "perfil": "pcd",
            "chuva": False,
            "k": 3
        }
        alt_response = client.post('/alternatives', json=alt_payload)
        assert alt_response.status_code == 200
        alt_data = alt_response.json()
        
        # 6. Verificar se há alternativas
        assert len(alt_data['alternatives']) > 0
        
        # 7. Analisar melhorias para PcD
        metrics_response = client.get('/metrics/edge-to-fix?perfil=pcd&top=5')
        assert metrics_response.status_code == 200
        metrics_data = metrics_response.json()
        
        # Verificar se a análise foi feita para o perfil correto
        assert metrics_data['analysis_params']['perfil'] == 'pcd'
        
    def test_rain_impact_analysis(self):
        """Testa impacto da chuva nas rotas"""
        # Rota sem chuva
        route_normal = {
            "from": "A",
            "to": "E",
            "perfil": "padrao",
            "chuva": False
        }
        response_normal = client.post('/route', json=route_normal)
        assert response_normal.status_code == 200
        data_normal = response_normal.json()
        
        # Rota com chuva
        route_rain = {
            "from": "A",
            "to": "E",
            "perfil": "padrao",
            "chuva": True
        }
        response_rain = client.post('/route', json=route_rain)
        assert response_rain.status_code == 200
        data_rain = response_rain.json()
        
        # As rotas podem ser diferentes ou iguais dependendo dos dados
        # O importante é que ambas retornem sucesso
        
    def test_profile_comparison(self):
        """Testa comparação entre perfis"""
        # Obter rotas para ambos os perfis
        payload_padrao = {
            "from": "A",
            "to": "E",
            "perfil": "padrao",
            "chuva": False
        }
        
        payload_pcd = {
            "from": "A",
            "to": "E",
            "perfil": "pcd",
            "chuva": False
        }
        
        response_padrao = client.post('/route', json=payload_padrao)
        response_pcd = client.post('/route', json=payload_pcd)
        
        assert response_padrao.status_code == 200
        assert response_pcd.status_code == 200
        
        data_padrao = response_padrao.json()
        data_pcd = response_pcd.json()
        
        # Verificar se ambas retornam rotas válidas
        assert data_padrao['best']['tempo_total_min'] > 0
        assert data_pcd['best']['tempo_total_min'] > 0
        
    def test_multiple_alternatives_consistency(self):
        """Testa consistência entre múltiplas alternativas"""
        payload = {
            "from": "A",
            "to": "E",
            "perfil": "pcd",
            "chuva": True,
            "k": 3
        }
        
        response = client.post('/alternatives', json=payload)
        assert response.status_code == 200
        data = response.json()
        
        alternatives = data['alternatives']
        if len(alternatives) > 1:
            # Verificar se as rotas são diferentes
            paths = [alt['path'] for alt in alternatives]
            unique_paths = set(tuple(path) for path in paths)
            assert len(unique_paths) == len(paths), "Todas as rotas devem ser únicas"
            
            # Verificar se os tempos são consistentes
            for alt in alternatives:
                assert alt['tempo_total_min'] > 0
                assert alt['id'] > 0
                assert len(alt['path']) > 0
                
    def test_edge_to_fix_consistency(self):
        """Testa consistência da análise edge-to-fix"""
        # Testar com diferentes parâmetros
        test_cases = [
            {"top": 1, "perfil": "padrao", "chuva": False},
            {"top": 3, "perfil": "pcd", "chuva": True},
            {"top": 5, "perfil": "padrao", "chuva": True}
        ]
        
        for case in test_cases:
            params = "&".join([f"{k}={v}" for k, v in case.items()])
            response = client.get(f'/metrics/edge-to-fix?{params}')
            assert response.status_code == 200
            
            data = response.json()
            assert data['analysis_params']['perfil'] == case['perfil']
            assert data['analysis_params']['chuva'] == case['chuva']
            assert data['analysis_params']['top'] == case['top']
            
            # Verificar se o número de melhorias não excede o solicitado
            assert len(data['suggested_improvements']) <= case['top']
            
    def test_data_consistency(self):
        """Testa consistência dos dados entre endpoints"""
        # Obter nós e arestas
        nodes_response = client.get('/nodes')
        edges_response = client.get('/edges')
        
        assert nodes_response.status_code == 200
        assert edges_response.status_code == 200
        
        nodes_data = nodes_response.json()
        edges_data = edges_response.json()
        
        # Verificar se todos os nós referenciados nas arestas existem
        node_ids = {node['id'] for node in nodes_data['nodes']}
        
        for edge in edges_data['edges']:
            assert edge['from'] in node_ids, f"Nó {edge['from']} não encontrado"
            assert edge['to'] in node_ids, f"Nó {edge['to']} não encontrado"
            
    def test_error_recovery(self):
        """Testa recuperação de erros"""
        # Testar com dados inválidos e depois com dados válidos
        invalid_payload = {
            "from": "INVALID",
            "to": "E",
            "perfil": "padrao",
            "chuva": False
        }
        
        response_invalid = client.post('/route', json=invalid_payload)
        assert response_invalid.status_code == 404
        
        # Agora testar com dados válidos
        valid_payload = {
            "from": "A",
            "to": "E",
            "perfil": "padrao",
            "chuva": False
        }
        
        response_valid = client.post('/route', json=valid_payload)
        assert response_valid.status_code == 200
        
    def test_concurrent_requests(self):
        """Testa múltiplas requisições simultâneas"""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request():
            try:
                payload = {
                    "from": "A",
                    "to": "E",
                    "perfil": "padrao",
                    "chuva": False
                }
                response = client.post('/route', json=payload)
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        # Criar 5 threads para fazer requisições simultâneas
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Aguardar todas as threads terminarem
        for thread in threads:
            thread.join()
        
        # Verificar se todas as requisições foram bem-sucedidas
        assert len(errors) == 0, f"Erros encontrados: {errors}"
        assert len(results) == 5
        assert all(status == 200 for status in results)
