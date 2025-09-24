# Conneccity API Documentation

## Visão Geral

A API Conneccity fornece endpoints para calcular rotas urbanas acessíveis e resilientes, considerando diferentes perfis de usuário e condições ambientais.

**Base URL**: `http://localhost:8080`

## Endpoints

### 1. Health Check

**GET** `/health`

Verifica o status da API.

**Resposta:**
```json
{
  "status": "ok",
  "version": "v1"
}
```

### 2. Obter Perfis

**GET** `/profiles`

Retorna os perfis disponíveis e seus pesos de custo.

**Resposta:**
```json
{
  "profiles": {
    "padrao": {
      "alpha": 6,
      "beta": 2,
      "gamma": 1,
      "delta": 4
    },
    "pcd": {
      "alpha": 6,
      "beta": 12,
      "gamma": 6,
      "delta": 4
    }
  },
  "description": {
    "padrao": "Perfil padrão para usuários sem restrições de mobilidade",
    "pcd": "Perfil para pessoas com deficiência (PcD) - evita escadas e calçadas ruins"
  }
}
```

### 3. Listar Nós

**GET** `/nodes`

Retorna todos os nós (pontos) do grafo.

**Resposta:**
```json
{
  "nodes": [
    {
      "id": "A",
      "name": "Estacao Hig-Mack",
      "lat": -23.55,
      "lon": -46.64,
      "tipo": "metro"
    }
  ]
}
```

### 4. Listar Arestas

**GET** `/edges`

Retorna todas as arestas (conexões) do grafo.

**Resposta:**
```json
{
  "edges": [
    {
      "from": "A",
      "to": "B",
      "tempo_min": 3.0,
      "transferencia": 1,
      "escada": 0,
      "calcada_ruim": 0,
      "risco_alag": 0,
      "modo": "pe"
    }
  ]
}
```

### 5. Calcular Melhor Rota

**POST** `/route`

Calcula a melhor rota entre dois pontos usando o algoritmo de Dijkstra.

**Corpo da Requisição:**
```json
{
  "from": "A",
  "to": "E",
  "perfil": "pcd",
  "chuva": true
}
```

**Parâmetros:**
- `from` (string): ID do nó de origem
- `to` (string): ID do nó de destino
- `perfil` (string): Perfil do usuário (`"padrao"` ou `"pcd"`)
- `chuva` (boolean): Se deve considerar risco de alagamento

**Resposta:**
```json
{
  "best": {
    "tempo_total_min": 18.5,
    "path": ["A", "B", "E"],
    "transferencias": 1,
    "barreiras_evitas": []
  }
}
```

### 6. Calcular Rotas Alternativas

**POST** `/alternatives`

Calcula k rotas alternativas entre dois pontos usando o algoritmo de Yen.

**Corpo da Requisição:**
```json
{
  "from": "A",
  "to": "E",
  "perfil": "pcd",
  "chuva": true,
  "k": 3
}
```

**Parâmetros:**
- `from` (string): ID do nó de origem
- `to` (string): ID do nó de destino
- `perfil` (string): Perfil do usuário (`"padrao"` ou `"pcd"`)
- `chuva` (boolean): Se deve considerar risco de alagamento
- `k` (integer): Número de rotas alternativas (1-3)

**Resposta:**
```json
{
  "alternatives": [
    {
      "id": 1,
      "tempo_total_min": 18.5,
      "transferencias": 1,
      "path": ["A", "B", "E"],
      "barreiras_evitas": []
    },
    {
      "id": 2,
      "tempo_total_min": 21.2,
      "transferencias": 0,
      "path": ["A", "C", "E"],
      "barreiras_evitas": ["alagamento@C->D"]
    }
  ]
}
```

### 7. Métricas de Melhoria

**GET** `/metrics/edge-to-fix?top=3`

Retorna ranking de trechos que mais impactariam na redução de custo/tempo se fossem melhorados.

**Parâmetros de Query:**
- `top` (integer): Número de sugestões a retornar (padrão: 3)

**Resposta:**
```json
{
  "message": "Funcionalidade em desenvolvimento",
  "suggested_improvements": [
    {
      "edge": "B->E",
      "issue": "calcada_ruim",
      "impact": "Alto - rota principal para hospital",
      "priority": 1
    }
  ]
}
```

## Códigos de Erro

- `200`: Sucesso
- `404`: Nó não encontrado
- `422`: Grafo desconectado ou sem caminho
- `500`: Erro interno do servidor

## Logs

A API gera logs estruturados em JSON para cada requisição:

```json
{
  "rid": "uuid-request-id",
  "path": "/alternatives",
  "method": "POST",
  "status": 200,
  "dur_ms": 45,
  "from": "A",
  "to": "E",
  "perfil": "pcd",
  "chuva": true,
  "k": 3
}
```

## Exemplos de Uso

### Exemplo 1: Rota para PcD sem chuva
```bash
curl -X POST http://localhost:8080/route \
  -H "Content-Type: application/json" \
  -d '{"from":"A","to":"E","perfil":"pcd","chuva":false}'
```

### Exemplo 2: 3 alternativas com chuva
```bash
curl -X POST http://localhost:8080/alternatives \
  -H "Content-Type: application/json" \
  -d '{"from":"A","to":"E","perfil":"pcd","chuva":true,"k":3}'
```

### Exemplo 3: Verificar status
```bash
curl http://localhost:8080/health
```
