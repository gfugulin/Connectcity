Analisando a estrutura do grafo no código:


[3 tools called]


Lendo os arquivos principais para entender a estrutura completa:


[4 tools called]


Estrutura do grafo no sistema:

## Estrutura do grafo

### 1. Representação em memória (C)

O grafo é implementado em C para performance e usa uma lista de adjacências:

```15:26:core-c/src/graph.h
typedef struct Edge {
  int to;
  double t_min;            // tempo_min
  uint8_t transferencia;   // 0/1
  uint8_t escada;          // 0/1
  uint8_t calcada_ruim;    // 0/1
  uint8_t risco_alag;      // 0/1
  uint8_t modo;            // 0=pe,1=onibus,2=metro,3=trem
  struct Edge* next;
} Edge;

typedef struct Node { char id[16]; double lat, lon; Edge* adj; } Node;
```

```31:35:core-c/src/graph.h
typedef struct Graph { 
  Node* nodes; 
  int n; 
  IdIndex* id_index;  // Índice hash para busca O(1) de IDs
} Graph;
```

### 2. Componentes principais

#### Nós (Nodes)
- ID: identificador único (máx. 15 caracteres)
- Coordenadas: `lat` e `lon`
- Lista de adjacências: ponteiro para a primeira aresta (`Edge* adj`)

#### Arestas (Edges)
Cada aresta contém:
- `to`: índice do nó destino
- `t_min`: tempo em minutos
- `transferencia`: flag (0/1)
- `escada`: flag (0/1)
- `calcada_ruim`: flag (0/1)
- `risco_alag`: flag (0/1)
- `modo`: 0=pe, 1=ônibus, 2=metrô, 3=trem
- `next`: ponteiro para próxima aresta (lista encadeada)

### 3. Índice hash para busca rápida

O grafo mantém um índice hash (`IdIndex`) para busca O(1) de nós por ID:

```23:34:core-c/src/graph.c
// Estrutura para índice hash simples (linear probing)
typedef struct {
  char id[16];
  int index;
  int used;
} IdIndexEntry;

struct IdIndex {
  IdIndexEntry* entries;
  int size;
  int capacity;
};
```

- Hash com linear probing
- Rehash automático quando necessário
- Capacidade inicial: 2x o número de nós

### 4. Carregamento de dados

O grafo é carregado a partir de dois arquivos CSV:

#### `nodes.csv`
Formato: `id,name,lat,lon,tipo`
- Cada linha representa um nó (parada, ponto de interesse, etc.)

#### `edges.csv`
Formato: `from,to,tempo_min,transferencia,escada,calcada_ruim,risco_alag,modo`
- Cada linha representa uma conexão entre dois nós
- Exemplo: `18856,18857,5.2,0,0,1,0,onibus`

### 5. Cálculo de custo de rota

O custo considera múltiplos fatores através de pesos configuráveis:

```39:43:core-c/src/graph.h
typedef struct CostParams {
  double alpha, beta, gamma, delta; // pesos em minutos
  int chuva_on;   // 0/1
  int perfil_pcd; // 0/1 (mantido para futura customização)
} CostParams;
```

- `alpha`: peso do tempo base
- `beta`: peso de transferências
- `gamma`: peso de barreiras (escadas, calçadas ruins)
- `delta`: peso de risco de alagamento
- `chuva_on`: multiplicador para condições de chuva
- `perfil_pcd`: ajuste para perfil de pessoa com deficiência

### 6. Algoritmos de roteamento

#### Dijkstra (rota mais curta)
```108:167:core-c/src/dijkstra.c
// Dijkstra otimizado com heap binário
Route dijkstra_shortest(Graph* g, int s, int t, CostParams p) {
  int n = g->n;
  double* dist = (double*)calloc(n, sizeof(double));
  int* prev = (int*)calloc(n, sizeof(int));
  
  for (int i = 0; i < n; i++) {
    dist[i] = DBL_MAX;
    prev[i] = -1;
  }
  dist[s] = 0.0;
  
  // Criar heap mínimo
  MinHeap* heap = heap_create(n);
  heap_insert(heap, s, 0.0);
  
  while (!heap_is_empty(heap)) {
    int u = heap_extract_min(heap);
    
    if (u == t) break; // Encontrou destino
    
    // Relaxar arestas adjacentes
    for (Edge* e = g->nodes[u].adj; e; e = e->next) {
      double w = edge_cost(e, p);
      double new_dist = dist[u] + w;
      
      if (new_dist < dist[e->to]) {
        dist[e->to] = new_dist;
        prev[e->to] = u;
        heap_decrease_key(heap, e->to, new_dist);
      }
    }
  }
  
  // Reconstruir caminho
  Route r = {0};
  if (dist[t] == DBL_MAX) {
    heap_free(heap);
    free(dist);
    free(prev);
    return r;
  }
  
  int len = 0;
  for (int x = t; x != -1; x = prev[x]) len++;
  
  r.path = (int*)malloc(len * sizeof(int));
  r.len = len;
  r.custo = dist[t];
  
  int x = t;
  for (int i = len - 1; i >= 0; i--) {
    r.path[i] = x;
    x = prev[x];
  }
  
  heap_free(heap);
  free(dist);
  free(prev);
  return r;
}
```

#### K-Shortest Paths (Yen)
- Retorna K rotas alternativas
- Usa o algoritmo de Yen para encontrar caminhos distintos

### 7. Interface Python (FFI)

O Python acessa o grafo via FFI (Foreign Function Interface):

```52:87:api/app/ffi.py
class Engine:
    def __init__(self, nodes_csv: str, edges_csv: str, profile_weights: dict):
        self.g = lib.load_graph_from_csv(nodes_csv.encode(), edges_csv.encode())
        self.weights = profile_weights

    def _params(self, perfil: str, chuva: bool) -> CostParams:
        w = self.weights[perfil]
        return CostParams(w["alpha"], w["beta"], w["gamma"], w["delta"], int(chuva), int(perfil=="pcd"))

    def idx(self, node_id: str) -> int:
        return lib.node_index_by_id(self.g, node_id.encode())
    
    def node_id(self, idx: int) -> str:
        """Obter ID do nó por índice"""
        if idx < 0 or idx >= self.g.contents.n:
            return ""
        return self.g.contents.nodes[idx].id.decode()

    def best(self, s: int, t: int, p: CostParams) -> Tuple[List[int], float]:
        r = lib.dijkstra_shortest(self.g, s, t, p)
        try:
            if r.len == 0:
                return [], 0.0
            return [r.path[i] for i in range(r.len)], r.custo
        finally:
            lib.free_route(ct.byref(r))

    def k_alternatives(self, s: int, t: int, p: CostParams, k: int) -> List[Tuple[List[int], float]]:
        routes = (Route * k)()
        n = lib.k_shortest_yen(self.g, s, t, p, k, routes)
        out = []
        for i in range(n):
            r = routes[i]
            out.append(([r.path[j] for j in range(r.len)], r.custo))
            lib.free_route(ct.byref(routes[i]))
        return out
```

### 8. Processamento de rotas (Python)

O Python processa os resultados do engine C para adicionar informações legíveis:

```214:384:api/app/route_utils.py
def get_route_details(path: List[str], cost: float, edges_df: pd.DataFrame, 
                     nodes_df: pd.DataFrame, profile: str) -> Dict:
    """
    Retorna detalhes completos de uma rota, incluindo passo a passo.
    """
    if len(path) == 0:
        return {
            'path': [],
            'total_time_min': 0.0,
            'transfers': 0,
            'barriers_avoided': [],
            'steps': [],
            'modes': []
        }
    
    global _nodes_by_id, _nodes_df

    segments = get_path_segments(path, edges_df)
    transfers = calculate_transfers(path, edges_df)
    barriers = identify_avoided_barriers(path, edges_df, profile)
    
    # Mapeamento legível de modos para o usuário
    mode_labels = {
        'onibus': 'Ônibus',
        'metro': 'Metrô',
        'trem': 'Trem',
        'pe': 'Caminhada'
    }
    
    # Construir passo a passo
    steps = []
    current_mode = None
    current_segment_group = []
    
    for i, segment in enumerate(segments):
        from_node = segment['from']
        to_node = segment['to']
        modo = segment['modo']
        tempo = segment['tempo_min']
        
        # Obter informações dos nós (preferencialmente via índice em memória)
        from_node_info = None
        to_node_info = None

        nodes_source = nodes_df if nodes_df is not None else _nodes_df

        if _nodes_by_id is not None:
            from_node_info = _nodes_by_id.get(str(from_node))
            to_node_info = _nodes_by_id.get(str(to_node))
        elif nodes_source is not None and 'id' in nodes_source.columns:
            from_rows = nodes_source[nodes_source['id'] == str(from_node)]
            to_rows = nodes_source[nodes_source['id'] == str(to_node)]
            from_node_info = from_rows.iloc[0] if len(from_rows) > 0 else None
            to_node_info = to_rows.iloc[0] if len(to_rows) > 0 else None
        
        # Se mudou o modo, finalizar grupo anterior e começar novo
        if current_mode is not None and modo != current_mode:
            if current_segment_group:
                first_seg = current_segment_group[0]
                last_seg = current_segment_group[-1]
                step_mode = current_mode
                step_mode_label = mode_labels.get(step_mode, step_mode)
                instruction = None

                if step_mode == 'pe':
                    instruction = f"Caminhe de {first_seg.get('from_name', first_seg['from'])} até {last_seg.get('to_name', last_seg['to'])}"
                else:
                    instruction = f"Pegue {step_mode_label} em {first_seg.get('from_name', first_seg['from'])} até {last_seg.get('to_name', last_seg['to'])}"

                steps.append({
                    'type': 'transport',
                    'mode': step_mode,
                    'mode_label': step_mode_label,
                    'from': first_seg['from'],
                    'to': last_seg['to'],
                    'from_name': first_seg.get('from_name', first_seg['from']),
                    'to_name': last_seg.get('to_name', last_seg['to']),
                    'time_min': sum(s['tempo_min'] for s in current_segment_group),
                    'segments': current_segment_group,
                    'instruction': instruction
                })
            
            current_segment_group = []
        
        # Adicionar segmento ao grupo atual
        segment_data = {
            'from': from_node,
            'to': to_node,
            'from_name': str(from_node_info['name']) if from_node_info is not None else from_node,
            'to_name': str(to_node_info['name']) if to_node_info is not None else to_node,
            'from_lat': float(from_node_info['lat']) if from_node_info is not None else 0.0,
            'from_lon': float(from_node_info['lon']) if from_node_info is not None else 0.0,
            'to_lat': float(to_node_info['lat']) if to_node_info is not None else 0.0,
            'to_lon': float(to_node_info['lon']) if to_node_info is not None else 0.0,
            'tempo_min': tempo,
            'modo': modo
        }
        current_segment_group.append(segment_data)
        
        current_mode = modo
    
    # Adicionar último grupo
    if current_segment_group:
        first_seg = current_segment_group[0]
        last_seg = current_segment_group[-1]
        step_mode = current_mode
        step_mode_label = mode_labels.get(step_mode, step_mode)
        instruction = None

        if step_mode == 'pe':
            instruction = f"Caminhe de {first_seg.get('from_name', first_seg['from'])} até {last_seg.get('to_name', last_seg['to'])}"
        else:
            instruction = f"Pegue {step_mode_label} em {first_seg.get('from_name', first_seg['from'])} até {last_seg.get('to_name', last_seg['to'])}"

        steps.append({
            'type': 'transport',
            'mode': step_mode,
            'mode_label': step_mode_label,
            'from': first_seg['from'],
            'to': first_seg['to'],
            'from_name': first_seg.get('from_name', first_seg['from']),
            'to_name': last_seg.get('to_name', last_seg['to']),
            'time_min': sum(s['tempo_min'] for s in current_segment_group),
            'segments': current_segment_group,
            'instruction': instruction
        })
    
    # Adicionar passo inicial (caminhada até primeiro ponto, se necessário)
    if steps and path:
        first_node_info = None
        nodes_source = nodes_df if nodes_df is not None else _nodes_df

        if _nodes_by_id is not None:
            first_node_info = _nodes_by_id.get(str(path[0]))
        elif nodes_source is not None and 'id' in nodes_source.columns:
            first_node_rows = nodes_source[nodes_source['id'] == str(path[0])]
            if len(first_node_rows) > 0:
                first_node_info = first_node_rows.iloc[0]

        if first_node_info is not None:
            initial_name = str(first_node_info['name'])
            steps.insert(0, {
                'type': 'walk',
                'mode': 'pe',
                'mode_label': mode_labels.get('pe', 'Caminhada'),
                'from': path[0],
                'to': path[0],
                'from_name': initial_name,
                'to_name': initial_name,
                'time_min': 0.0,
                'instruction': f"Iniciar viagem em {initial_name}"
            })
    
    # Calcular tempo total em minutos a partir dos segmentos,
    # em vez de usar diretamente o \"cost\" genérico do engine C.
    if segments:
        total_time_min = sum(seg['tempo_min'] for seg in segments)
    else:
        # Fallback: se por algum motivo não houver segmentos, usar o cost bruto.
        total_time_min = cost

    return {
        'path': path,
        'total_time_min': total_time_min,
        'transfers': transfers,
        'barriers_avoided': barriers,
        'steps': steps,
        # Modos em formato bruto e legível
        'modes': list(set(s['modo'] for s in segments)) if segments else [],
        'modes_labels': list(set(mode_labels.get(s['modo'], s['modo']) for s in segments)) if segments else []
    }
```

### 9. Características

- Performance: implementação em C com heap binário para Dijkstra
- Busca rápida: índice hash O(1) para lookup de nós
- Multi-modal: suporta caminhada, ônibus, metrô e trem
- Acessibilidade: flags para escadas, calçadas ruins e risco de alagamento
- Perfis: pesos configuráveis por perfil (padrão, idoso, PcD)
- Condições climáticas: multiplicador para chuva

### 10. Fluxo de dados

1. CSV → C Engine: carrega grafo em memória
2. C Engine: calcula rotas (Dijkstra/Yen)
3. Python FFI: recebe caminho como lista de índices
4. Python Utils: converte índices para IDs e adiciona metadados
5. API: retorna JSON com detalhes da rota

Quer detalhes de alguma parte específica?