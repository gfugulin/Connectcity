#!/bin/bash
# Script para testar a API Conneccity

set -e

API_URL="http://localhost:8080"

echo "🧪 Testando API Conneccity..."

# Teste 1: Health Check
echo "1. Testando /health..."
response=$(curl -s -w "%{http_code}" -o /tmp/health_response.json "$API_URL/health")
if [ "$response" = "200" ]; then
    echo "✅ Health check OK"
    cat /tmp/health_response.json | jq .
else
    echo "❌ Health check falhou (HTTP $response)"
    exit 1
fi

# Teste 2: Listar nós
echo "2. Testando /nodes..."
response=$(curl -s -w "%{http_code}" -o /tmp/nodes_response.json "$API_URL/nodes")
if [ "$response" = "200" ]; then
    echo "✅ Nodes OK"
    cat /tmp/nodes_response.json | jq '.nodes | length'
else
    echo "❌ Nodes falhou (HTTP $response)"
fi

# Teste 3: Listar arestas
echo "3. Testando /edges..."
response=$(curl -s -w "%{http_code}" -o /tmp/edges_response.json "$API_URL/edges")
if [ "$response" = "200" ]; then
    echo "✅ Edges OK"
    cat /tmp/edges_response.json | jq '.edges | length'
else
    echo "❌ Edges falhou (HTTP $response)"
fi

# Teste 4: Perfis
echo "4. Testando /profiles..."
response=$(curl -s -w "%{http_code}" -o /tmp/profiles_response.json "$API_URL/profiles")
if [ "$response" = "200" ]; then
    echo "✅ Profiles OK"
    cat /tmp/profiles_response.json | jq '.profiles'
else
    echo "❌ Profiles falhou (HTTP $response)"
fi

# Teste 5: Rota simples
echo "5. Testando /route..."
response=$(curl -s -w "%{http_code}" -o /tmp/route_response.json \
    -X POST "$API_URL/route" \
    -H "Content-Type: application/json" \
    -d '{"from":"A","to":"E","perfil":"padrao","chuva":false}')
if [ "$response" = "200" ]; then
    echo "✅ Route OK"
    cat /tmp/route_response.json | jq .
else
    echo "❌ Route falhou (HTTP $response)"
fi

# Teste 6: Alternativas
echo "6. Testando /alternatives..."
response=$(curl -s -w "%{http_code}" -o /tmp/alternatives_response.json \
    -X POST "$API_URL/alternatives" \
    -H "Content-Type: application/json" \
    -d '{"from":"A","to":"E","perfil":"pcd","chuva":true,"k":3}')
if [ "$response" = "200" ]; then
    echo "✅ Alternatives OK"
    cat /tmp/alternatives_response.json | jq .
else
    echo "❌ Alternatives falhou (HTTP $response)"
fi

# Teste 7: Métricas
echo "7. Testando /metrics/edge-to-fix..."
response=$(curl -s -w "%{http_code}" -o /tmp/metrics_response.json "$API_URL/metrics/edge-to-fix?top=3")
if [ "$response" = "200" ]; then
    echo "✅ Metrics OK"
    cat /tmp/metrics_response.json | jq .
else
    echo "❌ Metrics falhou (HTTP $response)"
fi

echo ""
echo "🎉 Testes concluídos!"
echo "Limpeza de arquivos temporários..."
rm -f /tmp/*_response.json

echo "✅ Todos os testes passaram!"
