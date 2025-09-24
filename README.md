# Conneccity

> **Rotas urbanas acessíveis e resilientes**: 3 alternativas explicadas (tempo, transferências e barreiras evitadas) + indicadores de conectividade (ex.: *Minutos‑até‑o‑Essencial ≤45*), alinhado à **ODS 11**.

---

## 📌 TL;DR

* **Objetivo**: calcular rotas que **respeitam acessibilidade** (escadas, calçadas ruins, baldeações) e **contexto** (alagamentos), mostrando **três alternativas explicadas**.
* **Motivação/Justificativa**: Apps genéricos priorizam "o mais rápido" e ignoram barreiras, afetando PcD, idosos e bairros "isolados".
* **Problema central**: falta de **rotas e métricas** que reflitam **acessibilidade real** e **eficiência com poucas transferências**.
* **Tipo do grafo**: **dirigido, ponderado e multimodal** (metrô/trem/ônibus/trechos a pé).
* **Nós (vértices)**: estações, pontos de ônibus, rampas/acessos e entradas de polos (ex.: hospital/campus) agregados por distrito.
* **Arestas (arcos)**: conexões com peso `tempo + α·transferência + β·escada + γ·calçada_ruim + δ·risco_alagamento`.

---

## 🧭 Escopo do MVP

* **Área-piloto**: raio \~2 km em SP (ABC Paulista como expansão futura).
* **Entradas**: `nodes.csv`, `edges.csv` (eventos de chuva opcionais via CSV).
* **Saídas**: 3 rotas alternativas + explicações; relatório *edge‑to‑fix* (trechos cuja melhoria mais reduz custo/tempo).

---

## 🧱 Arquitetura

```
┌────────────────┐     FFI/subprocess     ┌──────────────┐
│  Web (React)   │  ───────────────────▶  │   API (Py)   │  REST JSON
│  App Cidadão & │  ◀───────────────────  │  FastAPI     │  /route, /alternatives…
│  Painel Gestor │                         └─────┬────────┘
└────────────────┘                               │ chama
                                                 ▼
                                          ┌──────────────┐
                                          │  Core (C)    │  Dijkstra + Yen(k)
                                          │  Grafos      │  custo parametrizável
                                          └──────────────┘
```

**Persistência**: CSV no MVP; Postgres/Redis na Fase 2.
**Observabilidade**: logs JSON + métricas (latência p50/p95, taxa de erro).

---

## 🧮 Modelagem de Grafos

* **Grafo**: dirigido, ponderado, multimodal.
* **Vértices**: nós operacionais (estações, pontos de ônibus, rampas/entradas de polos).
* **Arestas**: `{tempo_min, transferencia, escada, calcada_ruim, risco_alag, modo}`.
* **Função de custo**:

```text
custo = tempo_min
      + α·transferencia(0/1)
      + β·escada(0/1)
      + γ·calcada_ruim(0/1)
      + δ·risco_alag(0/1)   // aplicado quando "chuva" estiver ON
```

* **Pesos sugeridos (minutos)**:

  * Perfil **padrão**: α=6, β=2, γ=1, δ=4
  * Perfil **mobilidade reduzida**: α=6, β=12, γ=6, δ=4

---

## 🗃️ Estrutura de Pastas

```
conneccity/
├─ core-c/              # lib C (grafos, dijkstra, yen, custo)
│  ├─ src/
│  └─ tests/
├─ api/                 # FastAPI + OpenAPI + adapters FFI
│  ├─ app/
│  └─ tests/
├─ web/                 # React/Next (App Cidadão + Painel Gestor)
├─ data/                # nodes.csv, edges.csv (exemplos)
├─ docker/              # Dockerfiles, compose
└─ README.md
```

---

## ⚙️ Executando (MVP)

### 🐳 Com Docker Compose (recomendado)

```bash
# 1) Clonar e subir
docker compose up --build

# 2) Acessar API
# API em http://localhost:8080
# Documentação em http://localhost:8080/docs
```

### 🛠️ Desenvolvimento Local

```bash
# 1) Configurar ambiente
chmod +x scripts/dev-setup.sh
./scripts/dev-setup.sh

# 2) Iniciar API
cd api
source venv/bin/activate
uvicorn app.main:app --reload --port 8080

# 3) Testar API
chmod +x scripts/test-api.sh
./scripts/test-api.sh
```

### 🧪 Testes Rápidos

```bash
# Health check
curl http://localhost:8080/health

# Rota simples
curl -X POST http://localhost:8080/route \
  -H "Content-Type: application/json" \
  -d '{"from":"A","to":"E","perfil":"pcd","chuva":false}'

# Alternativas
curl -X POST http://localhost:8080/alternatives \
  -H "Content-Type: application/json" \
  -d '{"from":"A","to":"E","perfil":"pcd","chuva":true,"k":3}'
```

**Variáveis de ambiente** (`.env`):

```env
CONNECCITY_PORT=8080
PROFILE_WEIGHTS='{"padrao":{"alpha":6,"beta":2,"gamma":1,"delta":4},"pcd":{"alpha":6,"beta":12,"gamma":6,"delta":4}}'
OVERPASS_URL=https://overpass-api.de/api/interpreter  # opcional
NOMINATIM_URL=https://nominatim.openstreetmap.org     # opcional
```

---

## 📥 Dados (CSV)

**`data/nodes.csv`**

```csv
id,name,lat,lon,tipo
A,Estacao Hig-Mack,-23.55,-46.64,metro
B,Ponto R. Consolacao,-23.5495,-46.642,onibus
C,Rampa Paulista,-23.5512,-46.641,acesso
D,Terminal Pacaembu,-23.552,-46.6425,onibus
E,Entrada Hospital,-23.553,-46.639,polo
```

**`data/edges.csv`**

```csv
from,to,tempo_min,transferencia,escada,calcada_ruim,risco_alag,modo
A,B,3,1,0,0,0,pe
B,E,6,0,0,1,0,pe
A,C,4,1,0,0,0,pe
C,F,7,0,0,0,1,onibus
F,H,6,0,0,0,1,onibus
```

---

## 🧩 API (resumo)

```http
GET  /health
POST /graph/upload                # importa nodes/edges CSV
POST /route                        # melhor rota (Dijkstra)
POST /alternatives                 # k-rotas (Yen)
POST /simulate                     # fecha trechos / aplica eventos
GET  /metrics/edge-to-fix?top=3    # ranking de trechos a corrigir
GET  /profiles                     # pesos α,β,γ,δ por perfil
GET  /nodes | /edges               # consulta básica
```

**Exemplo**

```bash
curl -X POST http://localhost:8080/alternatives \
  -H 'Content-Type: application/json' \
  -d '{"from":"A","to":"E","perfil":"pcd","chuva":true,"k":3}'
```

**Resposta (exemplo)**

```json
{
  "alternatives": [
    {"id":1,"tempo_total_min":18.5,"transferencias":1,
     "barreiras_evitas":["escadas_longas@D","calcada_ruim@E"],
     "path":["A","B","G","H"]},
    {"id":2,"tempo_total_min":21.2,"transferencias":0,
     "barreiras_evitas":["alagamento@F"],
     "path":["A","C","F","H"]}
  ]
}
```

---

## ✅ Critérios de Aceite (derivados de personas)

* Perfil **PcD** retorna rota **sem escadas** quando existir alternativa.
* Pelo menos **uma alternativa com 0 transferências** quando custo permitir.
* *Toggle* **"Evitar alagamento"** altera ranking quando há trechos de risco.

---

## 🧪 Testes & Qualidade

* **Core C**: testes unitários (Dijkstra/Yen/custo); cobertura ≥ 70%.
* **API**: testes de integração (200/400/404/422/500); contrato JSONSchema.
* **Carga**: 50 rps por 60s, erro < 1%, p95 `/route` ≤ 400 ms (dataset MVP).

---

## 🔭 Observabilidade

* **Logs JSON**: `ts, req_id, path, from, to, perfil, chuva, k, dur_ms, status`.
* **Métricas** (Prometheus): `http_request_duration_ms_bucket{path="/route"}`, `route_compute_errors_total`, `cache_hit_ratio`.

---

## 🗺️ Roadmap (MVP → Fase 2)

1. Parser CSV + Dijkstra + `/route`
2. Yen k‑shortest + `/alternatives`
3. *Toggle* chuva + `/simulate`
4. Heurística *edge‑to‑fix* + `/metrics/edge-to-fix`
5. Cache/observabilidade/CI
   **Fase 2**: GTFS, Postgres/Redis, elevação, Overpass automation.

---

## 🤝 Contribuição

Issues e PRs com testes e descrição do impacto. Siga *lint* e *pre-commit* definidos no repositório.

---

## 📎 Referências

* Graph Online – [https://graphonline.top/](https://graphonline.top/)
* OpenStreetMap/Overpass – [https://www.openstreetmap.org](https://www.openstreetmap.org) / [https://overpass-api.de/](https://overpass-api.de/)
* ODS 11 – Cidades e Comunidades Sustentáveis

---

## 📋 Guia de Desenvolvimento

Para implementação passo-a-passo, consulte: [OrientacaoAoDesenvolimento.md](../OrientacaoAoDesenvolimento.md)
