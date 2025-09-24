# Integração com Dados Reais - GTFS e OpenStreetMap

## 📋 Visão Geral

O Conneccity agora suporta integração completa com dados reais de transporte público (GTFS) e infraestrutura urbana (OpenStreetMap), permitindo:

- **Dados GTFS**: Paradas, rotas, horários e acessibilidade de transporte público
- **Dados OSM**: Infraestrutura urbana, acessibilidade, qualidade de superfícies e riscos
- **Integração Inteligente**: Combinação automática de dados para análise completa

## 🚌 Dados GTFS (General Transit Feed Specification)

### O que é GTFS?

GTFS é um padrão internacional para dados de transporte público que inclui:
- **Paradas**: Localização e características de paradas
- **Rotas**: Linhas de transporte público
- **Viagens**: Horários e sequências de paradas
- **Acessibilidade**: Informações sobre acessibilidade para PcD

### Fontes de Dados GTFS

#### Cidades Brasileiras Disponíveis:
- **Belo Horizonte**: https://ckan.pbh.gov.br/dataset/gtfs
- **São Paulo**: https://www.sptrans.com.br/gtfs/
- **Rio de Janeiro**: https://www.riocard.com/gtfs/
- **Porto Alegre**: https://www.poa.leg.br/gtfs/
- **Curitiba**: https://www.urbs.curitiba.pr.gov.br/gtfs/

### Estrutura dos Dados GTFS

```csv
# stops.txt
stop_id,stop_name,stop_lat,stop_lon,location_type,wheelchair_boarding
ST001,Estação Central,-19.9167,-43.9345,1,1
ST002,Praça da Liberdade,-19.9317,-43.9378,0,0

# routes.txt
route_id,route_short_name,route_long_name,route_type,route_color
R001,1001,Circular Centro,3,FF0000
R002,M1,Metrô Linha 1,1,0000FF

# trips.txt
trip_id,route_id,service_id,trip_headsign,direction_id
T001,R001,S001,Circular Centro,0
T002,R001,S001,Circular Centro,1

# stop_times.txt
trip_id,stop_id,arrival_time,departure_time,stop_sequence
T001,ST001,06:00:00,06:00:00,1
T001,ST002,06:05:00,06:05:00,2
```

## 🗺️ Dados OpenStreetMap (OSM)

### O que é OpenStreetMap?

OSM é um projeto colaborativo que fornece dados geográficos gratuitos incluindo:
- **Vias**: Ruas, calçadas, ciclovias
- **Infraestrutura**: Pontes, túneis, escadas
- **Acessibilidade**: Informações sobre acessibilidade
- **Riscos**: Áreas propensas a alagamento

### Query Overpass QL

```overpass
[out:xml][timeout:300];
(
  way["highway"~"^(primary|secondary|tertiary|residential|service|footway|cycleway|steps|path)$"](bbox);
  way["public_transport"="platform"](bbox);
  way["railway"~"^(tram|subway|light_rail)$"](bbox);
  node["public_transport"="stop_position"](bbox);
  node["railway"="station"](bbox);
  node["railway"="tram_stop"](bbox);
  node["railway"="subway_entrance"](bbox);
);
out geom;
```

### Tags OSM Relevantes

#### Acessibilidade:
- `wheelchair=yes/no/limited`
- `tactile_paving=yes/no`
- `kerb=lowered/raised/flush`

#### Qualidade de Superfície:
- `surface=asphalt/concrete/gravel/dirt/grass`
- `smoothness=excellent/good/intermediate/bad/very_bad/horrible`

#### Riscos:
- `flood_prone=yes/no`
- `natural=water`
- `ele=altitude_em_metros`

## 🔗 Integração de Dados

### Processo de Integração

1. **Download GTFS**: Baixa dados de transporte público
2. **Download OSM**: Obtém dados de infraestrutura urbana
3. **Processamento**: Converte para formato Conneccity
4. **Integração**: Combina dados GTFS e OSM
5. **Análise**: Calcula métricas de qualidade
6. **Exportação**: Gera dados integrados

### Mapeamento de Tipos

#### GTFS → Conneccity:
- `stop` → `onibus`
- `station` → `metro`
- `entrance` → `acesso`

#### OSM → Conneccity:
- `public_transport=stop_position` → `onibus`
- `railway=station` → `metro`
- `railway=tram_stop` → `tram`
- `railway=subway_entrance` → `acesso`

### Cálculo de Custos

```python
# Custo baseado em dados OSM
tempo_min = base_time * surface_factor * accessibility_factor
calcada_ruim = 1 if surface in ['dirt', 'gravel', 'mud'] else 0
escada = 1 if highway == 'steps' else 0
risco_alag = 1 if flood_prone == 'yes' or elevation < 10m else 0
```

## 🌐 API de Dados Reais

### Endpoints Disponíveis

#### Cidades e Integração:
```http
GET  /real-data/cities/available
POST /real-data/integrate/{city_name}
GET  /real-data/integration/status/{city_name}
```

#### Dados GTFS:
```http
GET  /real-data/gtfs/stops/{city_name}?limit=100
GET  /real-data/gtfs/routes/{city_name}?route_type=3
```

#### Dados OSM:
```http
GET  /real-data/osm/analysis/{city_name}
```

#### Dados Integrados:
```http
GET  /real-data/integrated/nodes/{city_name}?tipo=metro&min_accessibility=0.7
GET  /real-data/integrated/edges/{city_name}?modo=pe&has_barriers=false
GET  /real-data/accessibility/report/{city_name}
```

### Exemplos de Uso

#### 1. Listar Cidades Disponíveis:
```bash
curl http://localhost:8080/real-data/cities/available
```

#### 2. Integrar Dados de Belo Horizonte:
```bash
curl -X POST http://localhost:8080/real-data/integrate/belo_horizonte
```

#### 3. Obter Paradas Acessíveis:
```bash
curl "http://localhost:8080/real-data/integrated/nodes/belo_horizonte?min_accessibility=0.8"
```

#### 4. Relatório de Acessibilidade:
```bash
curl http://localhost:8080/real-data/accessibility/report/belo_horizonte
```

## 📊 Análises Disponíveis

### Análise de Acessibilidade

```json
{
  "accessibility_report": {
    "overall": {
      "total_nodes": 150,
      "accessible_nodes": 45,
      "partially_accessible_nodes": 60,
      "inaccessible_nodes": 45,
      "accessibility_percentage": 30.0
    },
    "by_type": {
      "metro": {
        "total": 20,
        "accessible": 18,
        "partially_accessible": 2,
        "inaccessible": 0
      },
      "onibus": {
        "total": 130,
        "accessible": 27,
        "partially_accessible": 58,
        "inaccessible": 45
      }
    },
    "recommendations": [
      "Melhorar acessibilidade em onibus: apenas 20.8% são acessíveis",
      "Priorizar melhorias de acessibilidade em onibus: 45 inacessíveis vs 27 acessíveis"
    ]
  }
}
```

### Análise de Qualidade de Superfície

```json
{
  "surface_quality_analysis": {
    "total_ways": 500,
    "surface_types": {
      "asphalt": 300,
      "concrete": 150,
      "gravel": 30,
      "dirt": 20
    },
    "poor_surfaces": [
      {
        "way_id": "W001",
        "surface": "gravel",
        "highway_type": "residential"
      }
    ],
    "good_surfaces": [
      {
        "way_id": "W002",
        "surface": "asphalt",
        "highway_type": "primary"
      }
    ]
  }
}
```

### Análise de Risco de Alagamento

```json
{
  "flood_risk_analysis": {
    "total_ways": 500,
    "flood_prone_areas": [
      {
        "way_id": "W003",
        "highway_type": "residential",
        "description": "Área baixa próxima ao rio"
      }
    ],
    "water_features": [
      {
        "way_id": "W004",
        "water_type": "river"
      }
    ],
    "elevation_data": [
      {
        "way_id": "W005",
        "elevation": 5.2
      }
    ]
  }
}
```

## 🛠️ Configuração e Uso

### 1. Instalação de Dependências

```bash
pip install -r requirements.txt
```

### 2. Executar Demonstração

```bash
python scripts/integrate-real-data.py
```

### 3. Iniciar API com Dados Reais

```bash
uvicorn app.main:app --reload --port 8080
```

### 4. Testar Integração

```bash
# Listar cidades
curl http://localhost:8080/real-data/cities/available

# Integrar dados
curl -X POST http://localhost:8080/real-data/integrate/belo_horizonte

# Verificar status
curl http://localhost:8080/real-data/integration/status/belo_horizonte
```

## 📈 Métricas de Qualidade

### Score de Acessibilidade (0-1)
- **0.9-1.0**: Totalmente acessível
- **0.7-0.9**: Acessível com pequenas limitações
- **0.3-0.7**: Parcialmente acessível
- **0.0-0.3**: Inacessível

### Score de Confiança (0-1)
- **0.9-1.0**: Dados de alta qualidade
- **0.7-0.9**: Dados de boa qualidade
- **0.5-0.7**: Dados de qualidade média
- **0.0-0.5**: Dados de baixa qualidade

## 🔄 Atualização de Dados

### Frequência Recomendada:
- **GTFS**: Semanal (dados de horários)
- **OSM**: Mensal (infraestrutura urbana)
- **Cache**: Diário (dados processados)

### Processo de Atualização:
1. Verificar disponibilidade de novos dados
2. Baixar e validar dados
3. Processar e integrar
4. Atualizar cache
5. Notificar sobre mudanças

## 🚀 Próximos Passos

### Melhorias Planejadas:
1. **Cache Inteligente**: Cache de dados OSM com TTL
2. **Validação Robusta**: Validação de qualidade de dados
3. **Atualização Automática**: Scheduler para atualizações
4. **Métricas Avançadas**: Análise de padrões de uso
5. **Interface Web**: Dashboard para visualização

### Integrações Futuras:
1. **Dados de Tráfego**: APIs de tráfego em tempo real
2. **Dados Meteorológicos**: Previsão do tempo
3. **Dados de Eventos**: Eventos que afetam mobilidade
4. **Dados de Construção**: Obras e interdições

## 📚 Recursos Adicionais

### Documentação:
- [GTFS Specification](https://gtfs.org/)
- [OpenStreetMap Wiki](https://wiki.openstreetmap.org/)
- [Overpass API](https://overpass-api.de/)

### Ferramentas:
- [GTFS Validator](https://github.com/MobilityData/gtfs-validator)
- [JOSM Editor](https://josm.openstreetmap.de/)
- [Overpass Turbo](https://overpass-turbo.eu/)

### Dados Brasileiros:
- [Belo Horizonte GTFS](https://ckan.pbh.gov.br/dataset/gtfs)
- [São Paulo GTFS](https://www.sptrans.com.br/gtfs/)
- [OpenStreetMap Brasil](https://wiki.openstreetmap.org/wiki/Brasil)
