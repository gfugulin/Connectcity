#!/bin/bash
# Script de configuração do ambiente de desenvolvimento

set -e

echo "🚀 Configurando ambiente de desenvolvimento Conneccity..."

# Verificar dependências
echo "📋 Verificando dependências..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale Python 3.11+"
    exit 1
fi

if ! command -v gcc &> /dev/null; then
    echo "❌ GCC não encontrado. Instale build-essential"
    exit 1
fi

echo "✅ Dependências verificadas"

# Compilar biblioteca C
echo "🔨 Compilando biblioteca C..."
cd core-c
if [ -f Makefile ]; then
    make clean
    make
else
    mkdir -p build
    gcc -O3 -march=native -flto -DNDEBUG -fPIC -Wall -Wextra -I./src -shared -o build/libconneccity.so src/graph.c src/dijkstra.c src/yen.c
fi
cd ..

# Configurar ambiente Python
echo "🐍 Configurando ambiente Python..."
cd api
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt
cd ..

# Criar diretórios necessários
echo "📁 Criando diretórios..."
mkdir -p logs
mkdir -p data

echo "✅ Ambiente configurado com sucesso!"
echo ""
echo "Para iniciar o desenvolvimento:"
echo "1. cd api && source venv/bin/activate"
echo "2. uvicorn app.main:app --reload --port 8080"
echo ""
echo "Para usar Docker:"
echo "docker-compose up --build"
