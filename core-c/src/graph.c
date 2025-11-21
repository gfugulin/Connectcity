#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "graph.h"

static Edge* new_edge(int to, double t_min, int tr, int es, int cr, int al, int modo) {
  Edge* e = (Edge*)calloc(1, sizeof(Edge));
  e->to = to; e->t_min = t_min; e->transferencia = tr; e->escada = es;
  e->calcada_ruim = cr; e->risco_alag = al; e->modo = modo; e->next = NULL; return e;
}

// Função auxiliar para normalizar ID (remover espaços e caracteres não-printáveis)
static void normalize_id(char* dest, const char* src, int max_len) {
  int j = 0;
  for (int i = 0; src[i] != '\0' && i < max_len - 1; i++) {
    if (src[i] >= 32 && src[i] < 127) { // Caracteres printáveis
      dest[j++] = src[i];
    }
  }
  dest[j] = '\0';
}

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

static IdIndex* create_id_index(int capacity) {
  IdIndex* idx = (IdIndex*)calloc(1, sizeof(IdIndex));
  idx->capacity = capacity;
  idx->size = 0;
  idx->entries = (IdIndexEntry*)calloc(capacity, sizeof(IdIndexEntry));
  return idx;
}

static void free_id_index(IdIndex* idx) {
  if (idx) {
    free(idx->entries);
    free(idx);
  }
}

// Hash simples para string
static unsigned int hash_id(const char* id) {
  unsigned int hash = 5381;
  int c;
  while ((c = *id++)) {
    hash = ((hash << 5) + hash) + c; // hash * 33 + c
  }
  return hash;
}

// Função interna para inserir sem rehash (usada durante rehash)
// Esta função DEVE sempre inserir (não pode falhar silenciosamente)
static void id_index_insert_internal(IdIndex* idx, const char* normalized, int node_index) {
  unsigned int h = hash_id(normalized) % idx->capacity;
  int attempts = 0;
  int start_h = h;
  
  // Linear probing até encontrar slot vazio
  while (idx->entries[h].used && attempts < idx->capacity) {
    if (strcmp(idx->entries[h].id, normalized) == 0) {
      return; // Já existe
    }
    h = (h + 1) % idx->capacity;
    attempts++;
    
    // Se deu volta completa, há um problema sério
    if (h == start_h && attempts > 0) {
      printf("[GRAPH] ERRO CRÍTICO: Índice cheio durante inserção interna! capacity=%d, size=%d, tentando inserir '%s'\n",
             idx->capacity, idx->size, normalized);
      // Fazer rehash de emergência (dobrar capacidade novamente)
      int old_capacity = idx->capacity;
      IdIndexEntry* old_entries = idx->entries;
      
      idx->capacity = old_capacity * 2;
      idx->entries = (IdIndexEntry*)calloc(idx->capacity, sizeof(IdIndexEntry));
      idx->size = 0;
      
      // Reinserir todos
      for (int i = 0; i < old_capacity; i++) {
        if (old_entries[i].used) {
          id_index_insert_internal(idx, old_entries[i].id, old_entries[i].index);
        }
      }
      
      free(old_entries);
      
      // Tentar inserir novamente
      h = hash_id(normalized) % idx->capacity;
      attempts = 0;
      start_h = h;
      
      // Tentar novamente
      while (idx->entries[h].used && attempts < idx->capacity) {
        if (strcmp(idx->entries[h].id, normalized) == 0) {
          return; // Já existe
        }
        h = (h + 1) % idx->capacity;
        attempts++;
      }
    }
  }
  
  // Inserir no slot encontrado (DEVE sempre encontrar após rehash)
  if (attempts < idx->capacity && !idx->entries[h].used) {
    strncpy(idx->entries[h].id, normalized, 15);
    idx->entries[h].id[15] = '\0';
    idx->entries[h].index = node_index;
    idx->entries[h].used = 1;
    idx->size++;
  } else {
    // Se não encontrou slot após rehash, fazer outro rehash recursivo
    printf("[GRAPH] AVISO: Não encontrou slot após rehash, fazendo rehash recursivo. capacity=%d, size=%d, attempts=%d, id='%s'\n",
           idx->capacity, idx->size, attempts, normalized);
    
    // Fazer rehash de emergência (dobrar capacidade novamente)
    int old_capacity = idx->capacity;
    IdIndexEntry* old_entries = idx->entries;
    
    idx->capacity = old_capacity * 2;
    idx->entries = (IdIndexEntry*)calloc(idx->capacity, sizeof(IdIndexEntry));
    idx->size = 0;
    
    // Reinserir todos
    for (int i = 0; i < old_capacity; i++) {
      if (old_entries[i].used) {
        id_index_insert_internal(idx, old_entries[i].id, old_entries[i].index);
      }
    }
    
    free(old_entries);
    
    // Tentar inserir novamente recursivamente
    id_index_insert_internal(idx, normalized, node_index);
  }
}

static void id_index_insert(IdIndex* idx, const char* id, int node_index) {
  char normalized[16];
  normalize_id(normalized, id, 16);
  
  // Loop até inserir com sucesso (pode fazer rehash se necessário)
  while (1) {
    unsigned int h = hash_id(normalized) % idx->capacity;
    int attempts = 0;
    
    // Linear probing até encontrar slot vazio
    while (idx->entries[h].used && attempts < idx->capacity) {
      if (strcmp(idx->entries[h].id, normalized) == 0) {
        // ID já existe - logar para diagnóstico (apenas primeiros 5 para não poluir logs)
        static int dup_count = 0;
        if (dup_count < 5) {
          printf("[GRAPH] ID duplicado detectado: '%s' (node_index=%d, já existe no índice %d)\n",
                 normalized, node_index, idx->entries[h].index);
          dup_count++;
        }
        return; // Já existe
      }
      h = (h + 1) % idx->capacity;
      attempts++;
    }
    
    // Se encontrou slot vazio, inserir
    if (attempts < idx->capacity && !idx->entries[h].used) {
      strncpy(idx->entries[h].id, normalized, 15);
      idx->entries[h].id[15] = '\0';
      idx->entries[h].index = node_index;
      idx->entries[h].used = 1;
      idx->size++;
      return; // Inserido com sucesso
    }
    
    // Se não encontrou slot (índice cheio), fazer rehash e tentar novamente
    int old_capacity = idx->capacity;
    int old_size = idx->size;
    IdIndexEntry* old_entries = idx->entries;
    
    // Dobrar capacidade
    idx->capacity = old_capacity * 2;
    idx->entries = (IdIndexEntry*)calloc(idx->capacity, sizeof(IdIndexEntry));
    idx->size = 0;
    
    // Reinserir todos os elementos antigos
    int reinseridos = 0;
    for (int i = 0; i < old_capacity; i++) {
      if (old_entries[i].used) {
        id_index_insert_internal(idx, old_entries[i].id, old_entries[i].index);
        reinseridos++;
      }
    }
    
    free(old_entries);
    
    // Logging para diagnóstico
    printf("[GRAPH] Rehash executado: capacidade %d -> %d, nós reinseridos: %d/%d, novo size: %d\n",
           old_capacity, idx->capacity, reinseridos, old_size, idx->size);
    
    // Inserir o novo elemento após rehash
    int size_before_insert = idx->size;
    id_index_insert_internal(idx, normalized, node_index);
    int size_after_insert = idx->size;
    
    // Se inseriu com sucesso, sair do loop
    if (size_after_insert > size_before_insert) {
      return; // Inserido com sucesso após rehash
    }
    
    // Se não inseriu, continuar loop para tentar novamente (pode precisar de outro rehash)
    // Isso não deveria acontecer, mas se acontecer, o loop continuará
  }
}

static int id_index_lookup(IdIndex* idx, const char* id) {
  char normalized[16];
  normalize_id(normalized, id, 16);
  unsigned int h = hash_id(normalized) % idx->capacity;
  
  // Linear probing
  int attempts = 0;
  while (idx->entries[h].used && attempts < idx->capacity) {
    if (strcmp(idx->entries[h].id, normalized) == 0) {
      return idx->entries[h].index;
    }
    h = (h + 1) % idx->capacity;
    attempts++;
  }
  
  return -1;
}

int node_index_by_id(Graph* g, const char* id) {
  // Se o grafo tem índice, usar (será criado durante carregamento)
  if (g && g->id_index) {
    return id_index_lookup(g->id_index, id);
  }
  
  // Fallback: busca linear (lento, mas funciona)
  char normalized_id[32];
  normalize_id(normalized_id, id, 32);
  
  for (int i=0;i<g->n;i++) {
    if (strcmp(g->nodes[i].id, normalized_id) == 0) return i;
  }
  return -1;
}

Graph* load_graph_from_csv(const char* nodes_csv, const char* edges_csv) {
  FILE* fn = fopen(nodes_csv, "r"); if (!fn) return NULL;
  FILE* fe = fopen(edges_csv, "r"); if (!fe) { fclose(fn); return NULL; }

  // count nodes
  char line[512]; int n=0; fgets(line, sizeof line, fn); // header
  while (fgets(line, sizeof line, fn)) n++;
  fseek(fn, 0, SEEK_SET); fgets(line, sizeof line, fn);

  Graph* g = (Graph*)calloc(1, sizeof(Graph));
  g->n = n; 
  g->nodes = (Node*)calloc(n, sizeof(Node));
  // Criar índice hash para busca rápida de IDs (capacidade 2x o número de nós)
  g->id_index = create_id_index(n * 2);

  int i=0; while (fgets(line, sizeof line, fn)) {
    // Formato esperado: id,name,lat,lon,tipo
    // Porém, o campo "name" pode conter vírgulas e aspas (por exemplo: "R. Delsuc Alves De Magalhães, 194")
    // Por isso, NÃO usamos sscanf direto. Em vez disso:
    // - Pegamos o último campo (tipo) pelo último separador ','
    // - Depois o penúltimo (lon), depois o antepenúltimo (lat)
    // - O primeiro campo antes da primeira vírgula é o id

    // Remover quebra de linha no fim, se existir
    size_t len = strlen(line);
    while (len > 0 && (line[len-1] == '\n' || line[len-1] == '\r')) {
      line[--len] = '\0';
    }
    if (len == 0) continue;

    char *tipo_str = NULL;
    char *lon_str = NULL;
    char *lat_str = NULL;
    char *id_str  = NULL;

    // Última vírgula: separa lon/tipo
    char *comma4 = strrchr(line, ',');
    if (!comma4) continue;
    *comma4 = '\0';
    tipo_str = comma4 + 1;

    // Próxima vírgula da direita para a esquerda: separa lat/lon
    char *comma3 = strrchr(line, ',');
    if (!comma3) continue;
    *comma3 = '\0';
    lon_str = comma3 + 1;

    // Próxima vírgula: separa id+name / lat
    char *comma2 = strrchr(line, ',');
    if (!comma2) continue;
    *comma2 = '\0';
    lat_str = comma2 + 1;

    // Primeira vírgula do restante: separa id / name
    char *comma1 = strchr(line, ',');
    if (!comma1) continue;
    *comma1 = '\0';
    id_str = line;

    // Converter lat/lon
    char *endptr = NULL;
    double lat = strtod(lat_str, &endptr);
    if (endptr == lat_str) continue; // falha na conversão
    endptr = NULL;
    double lon = strtod(lon_str, &endptr);
    if (endptr == lon_str) continue; // falha na conversão

    // Normalizar ID antes de copiar (remover caracteres não-printáveis)
    char id_normalized[16];
    normalize_id(id_normalized, id_str, 16);

    // Copiar ID normalizado garantindo null termination (struct tem char id[16], então máximo 15 chars + null)
    strncpy(g->nodes[i].id, id_normalized, 15);
    g->nodes[i].id[15] = '\0';  // Garantir null termination
    g->nodes[i].lat = lat; 
    g->nodes[i].lon = lon; 
    g->nodes[i].adj = NULL;
    
    // Adicionar ao índice hash para busca O(1)
    int size_before = g->id_index->size;
    id_index_insert(g->id_index, id_normalized, i);
    int size_after = g->id_index->size;
    
    // Logging a cada 1000 nós para diagnóstico mais frequente
    if ((i + 1) % 1000 == 0) {
      printf("[GRAPH] Checkpoint: %d/%d nós processados, %d inseridos no índice (%.1f%%, inseriu: %s)\n",
             i + 1, g->n, g->id_index->size, 100.0 * g->id_index->size / (i + 1),
             (size_after > size_before) ? "SIM" : "NÃO");
    }
    
    // Logging a cada 5000 nós para diagnóstico
    if ((i + 1) % 5000 == 0) {
      printf("[GRAPH] Progresso: %d/%d nós processados, %d inseridos no índice (%.1f%%)\n",
             i + 1, g->n, g->id_index->size, 100.0 * g->id_index->size / (i + 1));
    }
    
    i++;
  }
  fclose(fn);
  
  // Verificar se todos os nós foram inseridos no índice
  printf("[GRAPH] Carregamento concluído: %d nós processados, %d inseridos no índice\n",
         g->n, g->id_index->size);
  if (g->id_index->size != g->n) {
    printf("[GRAPH] ⚠️ ATENÇÃO: Apenas %d/%d nós inseridos no índice hash (%.1f%%)!\n", 
           g->id_index->size, g->n, 100.0 * g->id_index->size / g->n);
    printf("[GRAPH] ⚠️ Capacidade do índice: %d, Taxa de ocupação: %.1f%%\n",
           g->id_index->capacity, 100.0 * g->id_index->size / g->id_index->capacity);
  } else {
    printf("[GRAPH] ✅ Índice hash populado: %d/%d nós (100%%)\n", 
           g->id_index->size, g->n);
  }

  // edges
  fgets(line, sizeof line, fe); // header
  int edges_loaded = 0;
  int edges_skipped = 0;
  int edges_skipped_from = 0;
  int edges_skipped_to = 0;
  while (fgets(line, sizeof line, fe)) {
    // from,to,tempo_min,transferencia,escada,calcada_ruim,risco_alag,modo
    char from[32], to[32], modo_s[32]; double t; int tr, es, cr, al; int modo=0;
    if (sscanf(line, "%31[^,],%31[^,],%lf,%d,%d,%d,%d,%31[^\n]", from, to, &t, &tr, &es, &cr, &al, modo_s) == 8) {
      // Remover espaços e caracteres invisíveis dos IDs (trim)
      // Função auxiliar para trim
      // Normalizar IDs (remover caracteres não-printáveis)
      char from_normalized[32], to_normalized[32];
      normalize_id(from_normalized, from, 32);
      normalize_id(to_normalized, to, 32);
      
      if (strcmp(modo_s,"pe")==0) modo=0; else if (strcmp(modo_s,"onibus")==0) modo=1; else if (strcmp(modo_s,"metro")==0) modo=2; else if (strcmp(modo_s,"trem")==0) modo=3;
      int u = node_index_by_id(g, from_normalized); 
      int v = node_index_by_id(g, to_normalized); 
      if (u<0||v<0) {
        edges_skipped++;
        if (u < 0) edges_skipped_from++;
        if (v < 0) edges_skipped_to++;
        // Log primeiras 10 arestas ignoradas para debug
        if (edges_skipped <= 10) {
          printf("[GRAPH] Aresta ignorada: '%s' -> '%s' (normalized: '%s' -> '%s', u=%d, v=%d)\n", 
                 from, to, from_normalized, to_normalized, u, v);
        }
        continue;
      }
      Edge* e = new_edge(v, t, tr, es, cr, al, modo); 
      e->next = g->nodes[u].adj; 
      g->nodes[u].adj = e;
      edges_loaded++;
    }
  }
  fclose(fe);
  // Log de diagnóstico - IMPORTANTE para debug (SEMPRE ATIVO)
  printf("[GRAPH] Arestas carregadas: %d, ignoradas: %d (total no CSV: ~244547)\n", edges_loaded, edges_skipped);
  if (edges_skipped > 0) {
    printf("[GRAPH]   - Ignoradas por 'from' invalido: %d\n", edges_skipped_from);
    printf("[GRAPH]   - Ignoradas por 'to' invalido: %d\n", edges_skipped_to);
  }
  if (edges_skipped > 1000) {
    printf("[GRAPH] ⚠️ ATENÇÃO: Muitas arestas ignoradas! Verifique correspondência de IDs.\n");
  }
  // Validação: verificar se nó 18856 tem arestas (para debug)
  int test_node_idx = node_index_by_id(g, "18856");
  if (test_node_idx >= 0) {
    int edge_count = 0;
    Edge* e = g->nodes[test_node_idx].adj;
    while (e) { edge_count++; e = e->next; }
    printf("[GRAPH] Debug: No 18856 (indice %d) tem %d arestas\n", test_node_idx, edge_count);
  }
  return g;
}

void free_graph(Graph* g) {
  if (!g) return; 
  for (int i=0;i<g->n;i++) { 
    Edge* e=g->nodes[i].adj; 
    while (e){ Edge* nx=e->next; free(e); e=nx; } 
  }
  free_id_index(g->id_index);
  free(g->nodes); 
  free(g);
}
