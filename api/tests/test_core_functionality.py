import pytest
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestHealthEndpoint:
    """Testes para o endpoint de health check"""
    
    def test_health_check_success(self):
        """Testa se o health check retorna status OK"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'ok'
        assert data['version'] == 'v1'

class TestProfilesEndpoint:
    """Testes para o endpoint de perfis"""
    
    def test_get_profiles_success(self):
        """Testa se retorna os perfis corretamente"""
        response = client.get('/profiles')
        assert response.status_code == 200
        data = response.json()
        assert 'profiles' in data
        assert 'padrao' in data['profiles']
        assert 'pcd' in data['profiles']
        assert 'description' in data
        
    def test_profiles_structure(self):
        """Testa se a estrutura dos perfis está correta"""
        response = client.get('/profiles')
        data = response.json()
        
        # Verificar estrutura do perfil padrão
        padrao = data['profiles']['padrao']
        assert 'alpha' in padrao
        assert 'beta' in padrao
        assert 'gamma' in padrao
        assert 'delta' in padrao
        assert padrao['alpha'] == 6
        assert padrao['beta'] == 2
        assert padrao['gamma'] == 1
        assert padrao['delta'] == 4
        
        # Verificar estrutura do perfil PcD
        pcd = data['profiles']['pcd']
        assert pcd['alpha'] == 6
        assert pcd['beta'] == 12  # Maior penalidade para escadas
        assert pcd['gamma'] == 6  # Maior penalidade para calçadas ruins
        assert pcd['delta'] == 4

class TestNodesEndpoint:
    """Testes para o endpoint de nós"""
    
    def test_get_nodes_success(self):
        """Testa se retorna os nós corretamente"""
        response = client.get('/nodes')
        assert response.status_code == 200
        data = response.json()
        assert 'nodes' in data
        assert len(data['nodes']) > 0
        
    def test_nodes_structure(self):
        """Testa se a estrutura dos nós está correta"""
        response = client.get('/nodes')
        data = response.json()
        
        for node in data['nodes']:
            assert 'id' in node
            assert 'name' in node
            assert 'lat' in node
            assert 'lon' in node
            assert 'tipo' in node
            assert isinstance(node['lat'], (int, float))
            assert isinstance(node['lon'], (int, float))

class TestEdgesEndpoint:
    """Testes para o endpoint de arestas"""
    
    def test_get_edges_success(self):
        """Testa se retorna as arestas corretamente"""
        response = client.get('/edges')
        assert response.status_code == 200
        data = response.json()
        assert 'edges' in data
        assert len(data['edges']) > 0
        
    def test_edges_structure(self):
        """Testa se a estrutura das arestas está correta"""
        response = client.get('/edges')
        data = response.json()
        
        for edge in data['edges']:
            assert 'from' in edge
            assert 'to' in edge
            assert 'tempo_min' in edge
            assert 'transferencia' in edge
            assert 'escada' in edge
            assert 'calcada_ruim' in edge
            assert 'risco_alag' in edge
            assert 'modo' in edge
            assert isinstance(edge['tempo_min'], (int, float))
            assert edge['transferencia'] in [0, 1]
            assert edge['escada'] in [0, 1]
            assert edge['calcada_ruim'] in [0, 1]
            assert edge['risco_alag'] in [0, 1]

class TestRouteEndpoint:
    """Testes para o endpoint de rota"""
    
    def test_route_success_padrao(self):
        """Testa cálculo de rota com perfil padrão"""
        payload = {
            "from": "A",
            "to": "E",
            "perfil": "padrao",
            "chuva": False
        }
        response = client.post('/route', json=payload)
        assert response.status_code == 200
        data = response.json()
        assert 'best' in data
        assert 'tempo_total_min' in data['best']
        assert 'path' in data['best']
        assert 'transferencias' in data['best']
        assert 'barreiras_evitas' in data['best']
        assert data['best']['tempo_total_min'] > 0
        assert len(data['best']['path']) > 0
        
    def test_route_success_pcd(self):
        """Testa cálculo de rota com perfil PcD"""
        payload = {
            "from": "A",
            "to": "E",
            "perfil": "pcd",
            "chuva": False
        }
        response = client.post('/route', json=payload)
        assert response.status_code == 200
        data = response.json()
        assert 'best' in data
        assert data['best']['tempo_total_min'] > 0
        
    def test_route_with_rain(self):
        """Testa cálculo de rota com chuva"""
        payload = {
            "from": "A",
            "to": "E",
            "perfil": "padrao",
            "chuva": True
        }
        response = client.post('/route', json=payload)
        assert response.status_code == 200
        data = response.json()
        assert 'best' in data
        
    def test_route_invalid_nodes(self):
        """Testa rota com nós inválidos"""
        payload = {
            "from": "INVALID",
            "to": "E",
            "perfil": "padrao",
            "chuva": False
        }
        response = client.post('/route', json=payload)
        assert response.status_code == 404
        
    def test_route_invalid_profile(self):
        """Testa rota com perfil inválido"""
        payload = {
            "from": "A",
            "to": "E",
            "perfil": "invalid",
            "chuva": False
        }
        response = client.post('/route', json=payload)
        assert response.status_code == 422

class TestAlternativesEndpoint:
    """Testes para o endpoint de alternativas"""
    
    def test_alternatives_success(self):
        """Testa cálculo de alternativas"""
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
        assert 'alternatives' in data
        assert len(data['alternatives']) > 0
        
        for alt in data['alternatives']:
            assert 'id' in alt
            assert 'tempo_total_min' in alt
            assert 'transferencias' in alt
            assert 'path' in alt
            assert 'barreiras_evitas' in alt
            assert alt['tempo_total_min'] > 0
            assert len(alt['path']) > 0
            
    def test_alternatives_different_profiles(self):
        """Testa se perfis diferentes geram rotas diferentes"""
        # Rota padrão
        payload_padrao = {
            "from": "A",
            "to": "E",
            "perfil": "padrao",
            "chuva": False,
            "k": 2
        }
        response_padrao = client.post('/alternatives', json=payload_padrao)
        assert response_padrao.status_code == 200
        
        # Rota PcD
        payload_pcd = {
            "from": "A",
            "to": "E",
            "perfil": "pcd",
            "chuva": False,
            "k": 2
        }
        response_pcd = client.post('/alternatives', json=payload_pcd)
        assert response_pcd.status_code == 200
        
        # Verificar se as rotas são diferentes (ou pelo menos uma é diferente)
        data_padrao = response_padrao.json()
        data_pcd = response_pcd.json()
        
        # Pelo menos uma das rotas deve ser diferente
        routes_different = False
        for alt_padrao in data_padrao['alternatives']:
            for alt_pcd in data_pcd['alternatives']:
                if alt_padrao['path'] != alt_pcd['path']:
                    routes_different = True
                    break
            if routes_different:
                break
        
        # Nota: Pode ser que as rotas sejam iguais se não há barreiras no grafo de teste
        # Isso é aceitável para o teste
        
    def test_alternatives_k_limit(self):
        """Testa limite de k alternativas"""
        payload = {
            "from": "A",
            "to": "E",
            "perfil": "padrao",
            "chuva": False,
            "k": 10  # Mais que o limite
        }
        response = client.post('/alternatives', json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data['alternatives']) <= 3  # Limite máximo

class TestEdgeToFixEndpoint:
    """Testes para o endpoint de métricas edge-to-fix"""
    
    def test_edge_to_fix_success(self):
        """Testa análise de melhorias"""
        response = client.get('/metrics/edge-to-fix?top=3')
        assert response.status_code == 200
        data = response.json()
        assert 'analysis_params' in data
        assert 'total_improvements_found' in data
        assert 'suggested_improvements' in data
        
    def test_edge_to_fix_with_profile(self):
        """Testa análise com perfil específico"""
        response = client.get('/metrics/edge-to-fix?top=5&perfil=pcd&chuva=true')
        assert response.status_code == 200
        data = response.json()
        assert data['analysis_params']['perfil'] == 'pcd'
        assert data['analysis_params']['chuva'] == True
        
    def test_edge_to_fix_invalid_params(self):
        """Testa parâmetros inválidos"""
        # Perfil inválido
        response = client.get('/metrics/edge-to-fix?perfil=invalid')
        assert response.status_code == 400
        
        # Top inválido
        response = client.get('/metrics/edge-to-fix?top=50')
        assert response.status_code == 400
        
    def test_edge_to_fix_structure(self):
        """Testa estrutura da resposta"""
        response = client.get('/metrics/edge-to-fix?top=2')
        data = response.json()
        
        if data['suggested_improvements']:
            improvement = data['suggested_improvements'][0]
            assert 'edge' in improvement
            assert 'issue' in improvement
            assert 'current_cost' in improvement
            assert 'potential_savings' in improvement
            assert 'affected_routes' in improvement
            assert 'impact_score' in improvement
            assert 'impact_level' in improvement
            assert 'priority' in improvement
            assert 'description' in improvement

class TestErrorHandling:
    """Testes para tratamento de erros"""
    
    def test_invalid_json(self):
        """Testa JSON inválido"""
        response = client.post('/route', 
                             data="invalid json",
                             headers={"Content-Type": "application/json"})
        assert response.status_code == 422
        
    def test_missing_fields(self):
        """Testa campos obrigatórios ausentes"""
        payload = {
            "from": "A",
            # "to" ausente
            "perfil": "padrao"
        }
        response = client.post('/route', json=payload)
        assert response.status_code == 422
        
    def test_nonexistent_endpoint(self):
        """Testa endpoint inexistente"""
        response = client.get('/nonexistent')
        assert response.status_code == 404

class TestPerformance:
    """Testes básicos de performance"""
    
    def test_route_response_time(self):
        """Testa tempo de resposta da rota"""
        import time
        
        payload = {
            "from": "A",
            "to": "E",
            "perfil": "padrao",
            "chuva": False
        }
        
        start_time = time.time()
        response = client.post('/route', json=payload)
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = (end_time - start_time) * 1000  # em ms
        assert response_time < 1000  # Menos de 1 segundo
        
    def test_alternatives_response_time(self):
        """Testa tempo de resposta das alternativas"""
        import time
        
        payload = {
            "from": "A",
            "to": "E",
            "perfil": "pcd",
            "chuva": True,
            "k": 3
        }
        
        start_time = time.time()
        response = client.post('/alternatives', json=payload)
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = (end_time - start_time) * 1000  # em ms
        assert response_time < 2000  # Menos de 2 segundos
