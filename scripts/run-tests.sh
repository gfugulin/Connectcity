#!/bin/bash
# Script para executar todos os testes do Conneccity

set -e

echo "🧪 Executando testes do Conneccity..."

# Verificar se estamos no diretório correto
if [ ! -f "api/requirements.txt" ]; then
    echo "❌ Execute este script a partir do diretório raiz do projeto"
    exit 1
fi

# Ativar ambiente virtual se existir
if [ -d "api/venv" ]; then
    echo "🐍 Ativando ambiente virtual..."
    source api/venv/bin/activate
fi

# Instalar dependências se necessário
echo "📦 Verificando dependências..."
cd api
pip install -r requirements.txt > /dev/null 2>&1

# Executar testes com cobertura
echo "🔍 Executando testes com cobertura..."
pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

# Verificar se todos os testes passaram
if [ $? -eq 0 ]; then
    echo "✅ Todos os testes passaram!"
    echo "📊 Relatório de cobertura gerado em htmlcov/index.html"
else
    echo "❌ Alguns testes falharam"
    exit 1
fi

# Executar testes de performance básicos
echo "⚡ Executando testes de performance..."
python -c "
import time
import requests
import json

# Aguardar API estar pronta
time.sleep(2)

# Teste de carga simples
start_time = time.time()
success_count = 0
total_requests = 50

for i in range(total_requests):
    try:
        response = requests.post('http://localhost:8080/route', 
                               json={'from': 'A', 'to': 'E', 'perfil': 'padrao', 'chuva': False},
                               timeout=5)
        if response.status_code == 200:
            success_count += 1
    except:
        pass

end_time = time.time()
total_time = end_time - start_time
rps = total_requests / total_time
success_rate = (success_count / total_requests) * 100

print(f'📈 Performance: {rps:.1f} req/s, {success_rate:.1f}% sucesso')
print(f'⏱️  Tempo total: {total_time:.2f}s')

if success_rate >= 95 and rps >= 10:
    print('✅ Performance OK')
else:
    print('⚠️  Performance abaixo do esperado')
"

echo "🎉 Testes concluídos!"
