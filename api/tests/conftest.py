import pytest
import os
import sys
from pathlib import Path

# Adicionar o diretório pai ao path para importar a aplicação
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture(scope="session")
def test_data_dir():
    """Fixture para o diretório de dados de teste"""
    return Path(__file__).parent.parent.parent / "data"

@pytest.fixture(scope="session")
def sample_nodes():
    """Fixture com dados de nós de exemplo"""
    return [
        {"id": "A", "name": "Estacao Hig-Mack", "lat": -23.55, "lon": -46.64, "tipo": "metro"},
        {"id": "B", "name": "Ponto R Consolacao", "lat": -23.5495, "lon": -46.642, "tipo": "onibus"},
        {"id": "C", "name": "Rampa Paulista", "lat": -23.5512, "lon": -46.641, "tipo": "acesso"},
        {"id": "D", "name": "Terminal Pacaembu", "lat": -23.552, "lon": -46.6425, "tipo": "onibus"},
        {"id": "E", "name": "Entrada Hospital", "lat": -23.553, "lon": -46.639, "tipo": "polo"}
    ]

@pytest.fixture(scope="session")
def sample_edges():
    """Fixture com dados de arestas de exemplo"""
    return [
        {"from": "A", "to": "B", "tempo_min": 3, "transferencia": 1, "escada": 0, "calcada_ruim": 0, "risco_alag": 0, "modo": "pe"},
        {"from": "B", "to": "E", "tempo_min": 6, "transferencia": 0, "escada": 0, "calcada_ruim": 1, "risco_alag": 0, "modo": "pe"},
        {"from": "A", "to": "C", "tempo_min": 4, "transferencia": 1, "escada": 0, "calcada_ruim": 0, "risco_alag": 0, "modo": "pe"},
        {"from": "C", "to": "D", "tempo_min": 5, "transferencia": 0, "escada": 0, "calcada_ruim": 0, "risco_alag": 1, "modo": "onibus"},
        {"from": "D", "to": "E", "tempo_min": 6, "transferencia": 0, "escada": 0, "calcada_ruim": 0, "risco_alag": 1, "modo": "onibus"},
        {"from": "C", "to": "E", "tempo_min": 7, "transferencia": 0, "escada": 0, "calcada_ruim": 0, "risco_alag": 0, "modo": "pe"},
        {"from": "A", "to": "D", "tempo_min": 9, "transferencia": 1, "escada": 0, "calcada_ruim": 0, "risco_alag": 0, "modo": "onibus"}
    ]

@pytest.fixture(scope="session")
def expected_profiles():
    """Fixture com perfis esperados"""
    return {
        "padrao": {"alpha": 6, "beta": 2, "gamma": 1, "delta": 4},
        "pcd": {"alpha": 6, "beta": 12, "gamma": 6, "delta": 4}
    }

@pytest.fixture(scope="function")
def clean_environment():
    """Fixture para limpar ambiente entre testes"""
    # Limpar variáveis de ambiente se necessário
    yield
    # Cleanup após o teste
