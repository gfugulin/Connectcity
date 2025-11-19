# 🗺️ Fluxo Completo: Coleta, Conversão e Apresentação de Dados

## 📋 Visão Geral

Este documento explica como o sistema CONNECITY funciona, desde a coleta de dados das APIs (GTFS e OSM) até a apresentação das rotas no mapa, similar ao Google Maps.

---

## 🔄 Fluxo Completo

```
1. COLETA DE DADOS
   ↓
2. PROCESSAMENTO E CONVERSÃO
   ↓
3. INTEGRAÇÃO E EXPORTAÇÃO
   ↓
4. CARREGAMENTO NO GRAFO
   ↓
5. CÁLCULO DE ROTAS
   ↓
6. APRESENTAÇÃO NO MAPA
```

---

## 1️⃣ COLETA DE DADOS

### 1.1 Dados GTFS (Transporte Público)

**Fonte:** APIs de transporte público (SPTrans, BHTrans, etc.)

**Processo:**
```python
# integration/gtfs_processor.py

1. Download do arquivo ZIP GTFS
   ↓
2. Extração dos arquivos CSV:
   - stops.txt (paradas)
   - routes.txt (rotas)
   - trips.txt (viagens)
   - stop_times.txt (horários)
   ↓
3. Carregamento em estruturas Python:
   - GTFSStop (paradas)
   - GTFSRoute (rotas)
   - GTFSTrip (viagens)
   - GTFSStopTime (horários)
```

**Dados Coletados:**
- **Paradas (stops.txt):**
  - `stop_id`: ID único
  - `stop_name`: Nome da parada
  - `stop_lat`, `stop_lon`: Coordenadas
  - `wheelchair_boarding`: Acessibilidade
  - `location_type`: Tipo (stop, station, entrance)

- **Rotas (routes.txt):**
  - `route_id`: ID da rota
  - `route_short_name`: Nome curto (ex: "1001")
  - `route_type`: Tipo (0=tram, 1=metro, 3=bus, etc.)

- **Viagens (trips.txt):**
  - `trip_id`: ID da viagem
  - `route_id`: Rota associada
  - `service_id`: Calendário de operação

- **Horários (stop_times.txt):**
  - `trip_id`: Viagem
  - `stop_id`: Parada
  - `arrival_time`, `departure_time`: Horários
  - `stop_sequence`: Ordem na rota

### 1.2 Dados OSM (Infraestrutura Urbana)

**Fonte:** OpenStreetMap via Overpass API

**Processo:**
```python
# integration/osm_processor.py

1. Query Overpass QL para bounding box
   ↓
2. Download de dados XML:
   - Nodes (pontos)
   - Ways (vias/ruas)
   - Relations (relações)
   ↓
3. Parse XML e carregamento:
   - OSMNode (nós)
   - OSMWay (vias)
   - OSMRelation (relações)
```

**Dados Coletados:**
- **Vias (Ways):**
  - `highway`: Tipo de via (primary, secondary, footway, steps, etc.)
  - `surface`: Superfície (asphalt, dirt, gravel, etc.)
  - `smoothness`: Qualidade (excellent, good, bad, etc.)
  - `wheelchair`: Acessibilidade
  - `tactile_paving`: Piso tátil
  - `kerb`: Meio-fio (lowered, raised, etc.)

- **Nós (Nodes):**
  - `public_transport`: Paradas de transporte
  - `railway`: Estações ferroviárias
  - `lat`, `lon`: Coordenadas

---

## 2️⃣ PROCESSAMENTO E CONVERSÃO

### 2.1 GTFS → Nós e Arestas

**Código:** `integration/gtfs_processor.py::convert_to_conneccity_format()`

**Nós (Paradas):**
```python
for stop in stops:
    node = {
        'id': stop.stop_id,           # ID único
        'name': stop.stop_name,        # Nome da parada
        'lat': stop.stop_lat,          # Latitude
        'lon': stop.stop_lon,          # Longitude
        'tipo': 'onibus' | 'metro'     # Tipo de transporte
    }
```

**Arestas (Conexões entre Paradas):**
```python
# Para cada viagem, criar arestas sequenciais
for trip in trips:
    stops = sorted_stops_by_sequence(trip)
    for i in range(len(stops) - 1):
        edge = {
            'from': stops[i].stop_id,
            'to': stops[i+1].stop_id,
            'tempo_min': calculate_travel_time(
                stops[i].departure_time,
                stops[i+1].arrival_time
            ),
            'transferencia': 0,        # Preenchido depois
            'escada': 0,               # Preenchido com OSM
            'calcada_ruim': 0,         # Preenchido com OSM
            'risco_alag': 0,           # Preenchido com OSM
            'modo': 'onibus' | 'metro' # Tipo de transporte
        }
```

**Cálculo de Tempo:**
```python
def calculate_travel_time(departure, arrival):
    # Converter HH:MM:SS para minutos
    dep_minutes = time_to_minutes(departure)
    arr_minutes = time_to_minutes(arrival)
    
    # Se cruza meia-noite
    if arr_minutes < dep_minutes:
        arr_minutes += 24 * 60
    
    return max(1.0, arr_minutes - dep_minutes)
```

### 2.2 OSM → Nós e Arestas

**Código:** `integration/osm_processor.py::convert_to_conneccity_edges()`

**Nós (Pontos de Interesse):**
```python
for osm_node in nodes:
    if is_transport_node(osm_node):
        node = {
            'id': f"osm_{osm_node.id}",
            'name': osm_node.tags.get('name'),
            'lat': osm_node.lat,
            'lon': osm_node.lon,
            'tipo': map_osm_type(osm_node.tags)
        }
```

**Arestas (Vias):**
```python
for way in ways:
    # Criar arestas entre nós consecutivos
    for i in range(len(way.nodes) - 1):
        edge = {
            'from': way.nodes[i],
            'to': way.nodes[i + 1],
            'tempo_min': calculate_travel_time(way.tags),
            'transferencia': 0,
            'escada': 1 if way.tags['highway'] == 'steps' else 0,
            'calcada_ruim': assess_surface_quality(way.tags),
            'risco_alag': assess_flood_risk(way.tags),
            'modo': get_transport_mode(way.tags)  # 'pe', 'bike', etc.
        }
```

**Cálculo de Tempo (Baseado no Tipo de Via):**
```python
def calculate_travel_time(tags):
    highway = tags.get('highway', '')
    
    # Velocidades médias (km/h)
    speeds = {
        'primary': 50,
        'secondary': 40,
        'tertiary': 30,
        'residential': 20,
        'footway': 5,      # Caminhada
        'cycleway': 15,    # Bicicleta
        'steps': 3         # Escadas
    }
    
    speed = speeds.get(highway, 5)  # Padrão: caminhada
    length = calculate_way_length(way)  # Em km
    time_hours = length / speed
    return time_hours * 60  # Converter para minutos
```

**Avaliação de Barreiras:**
```python
def assess_surface_quality(tags):
    surface = tags.get('surface', '')
    poor_surfaces = ['dirt', 'gravel', 'grass', 'mud', 'sand']
    
    if surface in poor_surfaces:
        return 1  # Calçada ruim
    
    if tags.get('smoothness') in ['bad', 'very_bad', 'horrible']:
        return 1
    
    return 0  # Calçada boa
```

---

## 3️⃣ INTEGRAÇÃO E EXPORTAÇÃO

**Código:** `integration/data_integrator.py`

### 3.1 Integração de Dados

```python
# 1. Integrar nós (GTFS + OSM)
for stop in gtfs_stops:
    integrated_nodes[stop.stop_id] = IntegratedNode(...)

for osm_node in osm_nodes:
    if is_transport_node(osm_node):
        integrated_nodes[f"osm_{osm_node.id}"] = IntegratedNode(...)

# 2. Integrar arestas (GTFS + OSM)
for gtfs_edge in gtfs_edges:
    integrated_edges.append(IntegratedEdge(...))

for osm_edge in osm_edges:
    if not edge_exists(osm_edge):
        integrated_edges.append(IntegratedEdge(...))

# 3. Calcular métricas de qualidade
for node in integrated_nodes:
    node.accessibility_score = calculate_accessibility(node.osm_data)
    node.flood_risk = calculate_flood_risk(node.osm_data)

for edge in integrated_edges:
    edge.calcada_ruim = assess_surface_quality(edge.osm_data)
    edge.risco_alag = assess_flood_risk(edge.osm_data)
    edge.escada = assess_stairs(edge.osm_data)
```

### 3.2 Exportação para CSV

**Arquivo:** `data/integrated/integrated_nodes.csv`
```csv
id,name,lat,lon,tipo,accessibility_score,flood_risk
stop_123,Estação Sé,-23.5505,-46.6333,metro,0.8,0
osm_456,Rua Principal,-23.5510,-46.6340,polo,0.5,0
```

**Arquivo:** `data/integrated/integrated_edges.csv`
```csv
from,to,tempo_min,transferencia,escada,calcada_ruim,risco_alag,modo
stop_123,stop_456,5.0,0,0,0,0,metro
osm_456,osm_789,3.0,0,1,1,0,pe
```

---

## 4️⃣ CARREGAMENTO NO GRAFO

**Código:** `api/app/main.py::_init_engine_with_fallback()`

```python
# 1. Priorizar dados integrados
if exists("data/integrated/integrated_nodes.csv"):
    engine = Engine(
        "data/integrated/integrated_nodes.csv",
        "data/integrated/integrated_edges.csv",
        DEFAULT_WEIGHTS
    )

# 2. Fallback para dados primários
elif exists("data/nodes.csv"):
    engine = Engine(
        "data/nodes.csv",
        "data/edges.csv",
        DEFAULT_WEIGHTS
    )

# 3. Engine C carrega grafo em memória
# - Indexa nós por ID
# - Cria estrutura de adjacência
# - Calcula pesos das arestas baseado no perfil
```

**Pesos por Perfil:**
```python
DEFAULT_WEIGHTS = {
    "padrao": {
        "alpha": 6,   # Peso do tempo
        "beta": 2,    # Peso de transferências
        "gamma": 1,   # Peso de escadas
        "delta": 4    # Peso de calçada ruim
    },
    "idoso": {
        "alpha": 6,   # Tempo
        "beta": 4,    # Transferências (mais peso)
        "gamma": 2,   # Escadas (mais peso)
        "delta": 4    # Calçada ruim
    },
    "pcd": {
        "alpha": 6,   # Tempo
        "beta": 12,   # Transferências (muito peso)
        "gamma": 6,   # Escadas (muito peso)
        "delta": 4    # Calçada ruim
    }
}
```

**Cálculo de Peso da Aresta:**
```python
def calculate_edge_weight(edge, profile, rain):
    weights = DEFAULT_WEIGHTS[profile]
    
    weight = (
        weights["alpha"] * edge.tempo_min +           # Tempo
        weights["beta"] * edge.transferencia +        # Transferências
        weights["gamma"] * edge.escada +              # Escadas
        weights["delta"] * edge.calcada_ruim +        # Calçada ruim
        (weights["delta"] * 2 if rain and edge.risco_alag else 0)  # Alagamento
    )
    
    return weight
```

---

## 5️⃣ CÁLCULO DE ROTAS

**Código:** `api/app/main.py::get_alternatives()`

### 5.1 Algoritmo de Roteamento

```python
# 1. Converter IDs para índices
s = engine.idx(from_id)  # Índice do nó origem
t = engine.idx(to_id)    # Índice do nó destino

# 2. Calcular parâmetros baseado no perfil
params = engine._params(profile, rain)

# 3. Calcular k rotas alternativas (Yen's algorithm)
alternatives = engine.k_alternatives(s, t, params, k=3)

# Retorna: [(path_indices, cost), ...]
```

### 5.2 Processamento das Rotas

```python
for path_indices, cost in alternatives:
    # 1. Converter índices para IDs
    path_ids = [engine.node_id(idx) for idx in path_indices]
    
    # 2. Calcular transferências
    transfers = calculate_transfers(path_ids, edges_df)
    
    # 3. Identificar barreiras evitadas
    barriers = identify_avoided_barriers(path_ids, edges_df, profile)
    
    # 4. Construir resposta
    alt = {
        'id': i,
        'tempo_total_min': cost,
        'transferencias': transfers,
        'path': path_ids,  # Lista de IDs de nós
        'barreiras_evitas': barriers
    }
```

**Cálculo de Transferências:**
```python
def calculate_transfers(path, edges_df):
    transfers = 0
    previous_mode = None
    
    for i in range(len(path) - 1):
        edge = get_edge(path[i], path[i+1])
        current_mode = edge['modo']
        
        # Transferência = mudança de modo (exceto caminhada)
        if previous_mode and current_mode != previous_mode:
            if previous_mode != 'pe' and current_mode != 'pe':
                transfers += 1
        
        previous_mode = current_mode
    
    return transfers
```

---

## 6️⃣ APRESENTAÇÃO NO MAPA

### 6.1 Frontend Recebe Dados

**Código:** `front_connecity/src/pages/Home.jsx`

```javascript
// 1. Buscar rotas
const routes = await api.searchRoutes(from, to, profile);

// Resposta:
{
  alternatives: [
    {
      id: 0,
      tempo_total_min: 25.5,
      transferencias: 1,
      path: ["stop_123", "stop_456", "stop_789"],
      barreiras_evitas: ["escada@stop_456->stop_789"]
    },
    ...
  ]
}
```

### 6.2 Buscar Coordenadas dos Nós

```javascript
// Para cada nó no path, buscar coordenadas
for (const nodeId of route.path) {
  const node = await api.getNode(nodeId);
  // node = { id, name, lat, lon, tipo }
  
  coordinates.push([node.lat, node.lon]);
}
```

### 6.3 Desenhar Rota no Mapa

**Código:** `front_connecity/src/components/Map.jsx`

```javascript
// 1. Criar polyline conectando os pontos
const routePolyline = L.polyline(coordinates, {
  color: '#0d80f2',
  weight: 5,
  opacity: 0.7
}).addTo(map);

// 2. Adicionar marcadores
// Origem (vermelho)
L.marker([fromNode.lat, fromNode.lon], {
  icon: originIcon
}).addTo(map);

// Destino (azul)
L.marker([toNode.lat, toNode.lon], {
  icon: destinationIcon
}).addTo(map);

// 3. Ajustar zoom para mostrar toda a rota
map.fitBounds(routePolyline.getBounds(), {
  padding: [50, 50]
});
```

### 6.4 Diferenciação por Modo de Transporte

```javascript
// Cores diferentes por modo
const modeColors = {
  'metro': '#0066CC',    // Azul
  'onibus': '#FF6600',   // Laranja
  'pe': '#00CC66',       // Verde
  'tram': '#CC0066'      // Rosa
};

// Desenhar segmentos com cores diferentes
for (const segment of route.segments) {
  const color = modeColors[segment.mode] || '#666666';
  
  L.polyline(segment.coordinates, {
    color: color,
    weight: 5,
    opacity: 0.7
  }).addTo(map);
}
```

---

## 📊 Resumo do Fluxo

### Entrada:
- **GTFS:** Paradas, rotas, horários de transporte público
- **OSM:** Vias, infraestrutura urbana, acessibilidade

### Processamento:
1. **Coleta:** Download e parse de dados
2. **Conversão:** GTFS/OSM → Nós e Arestas
3. **Integração:** Combinação de dados
4. **Exportação:** CSV para o engine

### Cálculo:
1. **Grafo:** Carregamento em memória
2. **Pesos:** Cálculo baseado no perfil
3. **Roteamento:** Algoritmo de caminho mais curto (Dijkstra/Yen)

### Saída:
1. **API:** Retorna path (lista de IDs de nós)
2. **Frontend:** Busca coordenadas dos nós
3. **Mapa:** Desenha polyline conectando os pontos

---

## 🔍 Comparação com Google Maps

| Aspecto | Google Maps | CONNECITY |
|---------|-------------|-----------|
| **Dados** | Proprietários + GTFS | GTFS + OSM (open source) |
| **Algoritmo** | Proprietário | Dijkstra/Yen (open source) |
| **Perfis** | Padrão | Padrão, Idoso, PcD |
| **Barreiras** | Não considera | Escadas, calçadas, alagamento |
| **Acessibilidade** | Limitada | Foco em acessibilidade |

---

## 🎯 Próximos Passos

1. **Desenhar rota no mapa:** Implementar polyline no componente Map
2. **Cores por modo:** Diferenciação visual de transportes
3. **Marcadores intermediários:** Mostrar pontos de transferência
4. **Geolocalização:** Usar localização atual como origem


