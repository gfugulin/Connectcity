# 🗺️ API OpenStreetMap - Overpass API

## 📋 Visão Geral

O sistema utiliza a **Overpass API** do OpenStreetMap para obter dados de infraestrutura urbana, incluindo:
- Vias e ruas (highways)
- Paradas de transporte público
- Estações ferroviárias
- Acessibilidade (escadas, calçadas, etc.)
- Qualidade de superfície
- Riscos de alagamento

**URL Base:** `http://overpass-api.de/api/interpreter`

**Documentação Oficial:** [https://wiki.openstreetmap.org/wiki/Overpass_API](https://wiki.openstreetmap.org/wiki/Overpass_API)

---

## 🔐 Autenticação

**Status:** ✅ **NÃO REQUER AUTENTICAÇÃO**

A Overpass API é pública e não requer autenticação ou token. Pode ser usada diretamente.

---

## 📡 Como Funciona

### Overpass QL (Query Language)

A Overpass API usa uma linguagem de consulta própria chamada **Overpass QL** para buscar dados específicos do OpenStreetMap.

### Query Básica

```overpass
[out:xml][timeout:300];
(
  way["highway"~"^(primary|secondary|tertiary|residential|service|footway|cycleway|steps|path)$"]({min_lat},{min_lon},{max_lat},{max_lon});
  node["public_transport"="stop_position"]({min_lat},{min_lon},{max_lat},{max_lon});
);
out geom;
```

**Componentes:**
- `[out:xml]` - Formato de saída (XML)
- `[timeout:300]` - Timeout em segundos
- `way[...]` - Buscar vias (ruas, caminhos)
- `node[...]` - Buscar nós (pontos)
- `({min_lat},{min_lon},{max_lat},{max_lon})` - Bounding box (área geográfica)
- `out geom;` - Incluir geometria completa

---

## 🎯 Dados Coletados

### 1. Vias (Ways)

**Tipos de Highway Coletados:**
- `primary` - Vias principais
- `secondary` - Vias secundárias
- `tertiary` - Vias terciárias
- `residential` - Ruas residenciais
- `service` - Vias de serviço
- `footway` - Calçadas
- `cycleway` - Ciclovias
- `steps` - Escadas
- `path` - Caminhos

**Tags Importantes:**
- `highway` - Tipo de via
- `surface` - Superfície (asphalt, dirt, gravel, etc.)
- `smoothness` - Qualidade (excellent, good, bad, etc.)
- `wheelchair` - Acessibilidade para cadeirantes
- `tactile_paving` - Piso tátil
- `kerb` - Meio-fio (lowered, raised, etc.)

### 2. Nós de Transporte Público

**Tipos Coletados:**
- `public_transport=stop_position` - Paradas de ônibus
- `railway=station` - Estações ferroviárias
- `railway=tram_stop` - Paradas de bonde
- `railway=subway_entrance` - Entradas de metrô

### 3. Plataformas de Transporte

- `public_transport=platform` - Plataformas de embarque
- `railway=tram` - Linhas de bonde
- `railway=subway` - Linhas de metrô
- `railway=light_rail` - VLT

---

## 💻 Uso no Código

### Cliente Python

```python
from integration.osm_processor import OSMProcessor

# Inicializar processador
processor = OSMProcessor("data/osm")

# Definir bounding box (São Paulo - Centro)
# Formato: (min_lon, min_lat, max_lon, max_lat)
bbox = (-46.65, -23.55, -46.60, -23.50)

# Obter dados OSM
xml_path = processor.get_bbox_data(bbox, timeout=300)

# Parse dos dados
processor.parse_osm_xml(xml_path)

# Acessar dados
print(f"Nós coletados: {len(processor.nodes)}")
print(f"Vias coletadas: {len(processor.ways)}")
print(f"Relações coletadas: {len(processor.relations)}")
```

### Query Customizada

A query atual busca:

```python
query = f"""
[out:xml][timeout:{timeout}];
(
  # Vias (ruas, caminhos)
  way["highway"~"^(primary|secondary|tertiary|residential|service|footway|cycleway|steps|path)$"]({min_lat},{min_lon},{max_lat},{max_lon});
  
  # Plataformas de transporte
  way["public_transport"="platform"]({min_lat},{min_lon},{max_lat},{max_lat});
  
  # Linhas ferroviárias
  way["railway"~"^(tram|subway|light_rail)$"]({min_lat},{min_lon},{max_lat},{max_lon});
  
  # Paradas de transporte público
  node["public_transport"="stop_position"]({min_lat},{min_lon},{max_lat},{max_lon});
  
  # Estações ferroviárias
  node["railway"="station"]({min_lat},{min_lon},{max_lat},{max_lon});
  
  # Paradas de bonde
  node["railway"="tram_stop"]({min_lat},{min_lon},{max_lat},{max_lon});
  
  # Entradas de metrô
  node["railway"="subway_entrance"]({min_lat},{min_lon},{max_lat},{max_lon});
);
out geom;
"""
```

---

## 🔄 Processamento dos Dados

### 1. Parse XML

```python
processor.parse_osm_xml(xml_path)

# Dados parseados ficam disponíveis em:
# - processor.nodes: Dict[str, OSMNode]
# - processor.ways: Dict[str, OSMWay]
# - processor.relations: Dict[str, OSMRelation]
```

### 2. Conversão para Formato Conneccity

```python
# Converter vias para arestas
edges = processor.convert_to_conneccity_edges()

# Cada aresta contém:
# {
#   'from': node_id,
#   'to': node_id,
#   'tempo_min': tempo_em_minutos,
#   'transferencia': 0,
#   'escada': 0 ou 1,
#   'calcada_ruim': 0 ou 1,
#   'risco_alag': 0 ou 1,
#   'modo': 'pe' | 'bike' | etc.
# }
```

### 3. Análises Disponíveis

```python
# Análise de acessibilidade
accessibility = processor.analyze_accessibility()
# Retorna: vias acessíveis, inacessíveis, recursos encontrados

# Análise de qualidade de superfície
surface_quality = processor.analyze_surface_quality()
# Retorna: vias com superfície ruim, qualidade média, etc.

# Análise de risco de alagamento
flood_risk = processor.analyze_flood_risk()
# Retorna: áreas com risco de alagamento
```

---

## 📊 Exemplo de Dados Coletados

### Nó OSM

```python
OSMNode(
    id="123456",
    lat=-23.5505,
    lon=-46.6333,
    tags={
        "public_transport": "stop_position",
        "name": "Parada Lapa",
        "wheelchair": "yes"
    }
)
```

### Via OSM

```python
OSMWay(
    id="789012",
    nodes=["123", "456", "789"],
    tags={
        "highway": "footway",
        "surface": "asphalt",
        "smoothness": "good",
        "wheelchair": "yes",
        "tactile_paving": "yes"
    }
)
```

---

## 🎯 Bounding Boxes Configuradas

### São Paulo

```python
CITY_BOUNDS = {
    "sao_paulo": (-46.8, -23.8, -46.3, -23.4),  # Toda a cidade
    
    # Áreas específicas
    "centro": (-46.65, -23.55, -46.60, -23.50),
    "zona_sul": (-46.75, -23.65, -46.60, -23.55),
    "zona_norte": (-46.70, -23.45, -46.50, -23.35),
    "zona_leste": (-46.60, -23.55, -46.40, -23.45),
    "zona_oeste": (-46.80, -23.55, -46.65, -23.45)
}
```

### Outras Cidades

```python
"belo_horizonte": (-44.1, -20.0, -43.8, -19.8),
"rio_de_janeiro": (-43.4, -23.1, -43.1, -22.8),
"porto_alegre": (-51.3, -30.2, -51.0, -30.0),
"curitiba": (-49.4, -25.6, -49.1, -25.3)
```

---

## ⚙️ Configurações

### Timeout

```python
# Timeout padrão: 300 segundos (5 minutos)
# Para áreas grandes, pode ser necessário aumentar
xml_path = processor.get_bbox_data(bbox, timeout=600)  # 10 minutos
```

### Formato de Saída

Atualmente usa **XML**, mas Overpass API também suporta:
- `[out:xml]` - XML (padrão)
- `[out:json]` - JSON
- `[out:csv]` - CSV

**Nota:** O código atual está configurado para XML. Para mudar para JSON, seria necessário ajustar o parser.

---

## 🔍 Tags OSM Relevantes para Acessibilidade

### Acessibilidade

- `wheelchair=yes` - Acessível para cadeirantes
- `wheelchair=no` - Não acessível
- `wheelchair=limited` - Acesso limitado
- `tactile_paving=yes` - Piso tátil presente
- `kerb=lowered` - Meio-fio rebaixado

### Qualidade de Superfície

- `surface=asphalt` - Asfalto (boa)
- `surface=concrete` - Concreto (boa)
- `surface=dirt` - Terra (ruim)
- `surface=gravel` - Cascalho (ruim)
- `smoothness=excellent` - Excelente
- `smoothness=good` - Boa
- `smoothness=bad` - Ruim
- `smoothness=very_bad` - Muito ruim

### Barreiras

- `highway=steps` - Escadas
- `barrier=*` - Barreiras físicas
- `flood_prone=yes` - Área propensa a alagamento

---

## 📈 Estatísticas de Coleta

### Exemplo: Centro de São Paulo

```
Nós coletados: 696
Vias coletadas: 8.153
Arestas geradas: 38.790

Análise de Acessibilidade:
- Vias acessíveis: 14 (0.17%)
- Vias inacessíveis: 1 (0.01%)
- Status desconhecido: 8.138 (99.82%)

Recursos encontrados:
- Piso tátil: Várias vias
- Meio-fio rebaixado: Algumas vias
```

---

## ⚠️ Limitações e Considerações

### 1. Rate Limiting

- Overpass API tem limites de requisições
- Não fazer muitas requisições simultâneas
- Implementar cache quando possível

### 2. Tamanho da Área

- Áreas muito grandes podem exceder timeout
- Dividir em áreas menores se necessário
- Usar bounding boxes específicas

### 3. Qualidade dos Dados

- Dados OSM são colaborativos
- Qualidade varia por região
- Nem todas as tags estão preenchidas
- Verificar dados antes de usar

### 4. Atualização

- Dados OSM são atualizados constantemente
- Cache pode ficar desatualizado
- Considerar atualização periódica

---

## 🔄 Integração com o Sistema

### Fluxo Completo

```python
# 1. Coletar dados OSM
osm_processor = OSMProcessor()
xml_path = osm_processor.get_bbox_data(bbox)
osm_processor.parse_osm_xml(xml_path)

# 2. Converter para formato Conneccity
edges = osm_processor.convert_to_conneccity_edges()

# 3. Integrar com dados GTFS
integrator = DataIntegrator()
integrator.integrate_city_data("sao_paulo", bbox=bbox)

# 4. Exportar dados integrados
# Arquivos gerados:
# - data/integrated/integrated_nodes.csv
# - data/integrated/integrated_edges.csv
```

### Uso no Grafo

Os dados OSM são convertidos em:
- **Nós:** Pontos de interesse, paradas, estações
- **Arestas:** Conexões entre pontos com:
  - Tempo de viagem
  - Barreiras (escadas, calçada ruim)
  - Risco de alagamento
  - Modo de transporte

---

## 📚 Referências

- [Overpass API Documentation](https://wiki.openstreetmap.org/wiki/Overpass_API)
- [Overpass QL Language Guide](https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL)
- [OSM Tags for Accessibility](https://wiki.openstreetmap.org/wiki/Key:wheelchair)
- [OSM Highway Types](https://wiki.openstreetmap.org/wiki/Key:highway)
- [OpenStreetMap Wiki](https://wiki.openstreetmap.org/)

---

## ✅ Status da Implementação

- ✅ **API Overpass:** Funcionando
- ✅ **Coleta de Dados:** Implementada
- ✅ **Parse XML:** Implementado
- ✅ **Conversão para Conneccity:** Implementada
- ✅ **Análises:** Implementadas (acessibilidade, superfície, alagamento)
- ✅ **Integração com GTFS:** Implementada

**URL Testada:** `http://overpass-api.de/api/interpreter` ✅ Funcionando

