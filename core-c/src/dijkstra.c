#include <stdlib.h>
#include <float.h>
#include "graph.h"
#include "cost.h"

// Heap binário mínimo para Dijkstra
typedef struct {
  int* heap;      // Array de índices de nós
  double* dist;   // Distâncias (chaves do heap)
  int* pos;       // Posição de cada nó no heap (para decrease-key)
  int size;       // Tamanho atual do heap
  int capacity;   // Capacidade máxima
} MinHeap;

static MinHeap* heap_create(int capacity) {
  MinHeap* h = (MinHeap*)calloc(1, sizeof(MinHeap));
  h->heap = (int*)calloc(capacity, sizeof(int));
  h->dist = (double*)calloc(capacity, sizeof(double));
  h->pos = (int*)calloc(capacity, sizeof(int));
  h->capacity = capacity;
  h->size = 0;
  for (int i = 0; i < capacity; i++) h->pos[i] = -1;
  return h;
}

static void heap_free(MinHeap* h) {
  if (h) {
    free(h->heap);
    free(h->dist);
    free(h->pos);
    free(h);
  }
}

static void heap_swap(MinHeap* h, int i, int j) {
  int tmp = h->heap[i];
  h->heap[i] = h->heap[j];
  h->heap[j] = tmp;
  h->pos[h->heap[i]] = i;
  h->pos[h->heap[j]] = j;
}

static void heap_up(MinHeap* h, int idx) {
  while (idx > 0) {
    int parent = (idx - 1) / 2;
    if (h->dist[h->heap[idx]] >= h->dist[h->heap[parent]]) break;
    heap_swap(h, idx, parent);
    idx = parent;
  }
}

static void heap_down(MinHeap* h, int idx) {
  while (1) {
    int left = 2 * idx + 1;
    int right = 2 * idx + 2;
    int smallest = idx;
    
    if (left < h->size && h->dist[h->heap[left]] < h->dist[h->heap[smallest]]) {
      smallest = left;
    }
    if (right < h->size && h->dist[h->heap[right]] < h->dist[h->heap[smallest]]) {
      smallest = right;
    }
    
    if (smallest == idx) break;
    heap_swap(h, idx, smallest);
    idx = smallest;
  }
}

static void heap_insert(MinHeap* h, int v, double d) {
  if (h->pos[v] >= 0) return; // Já está no heap
  h->heap[h->size] = v;
  h->dist[v] = d;
  h->pos[v] = h->size;
  h->size++;
  heap_up(h, h->size - 1);
}

static int heap_extract_min(MinHeap* h) {
  if (h->size == 0) return -1;
  int min = h->heap[0];
  h->pos[min] = -1;
  h->size--;
  if (h->size > 0) {
    h->heap[0] = h->heap[h->size];
    h->pos[h->heap[0]] = 0;
    heap_down(h, 0);
  }
  return min;
}

static void heap_decrease_key(MinHeap* h, int v, double new_dist) {
  if (h->pos[v] < 0) {
    heap_insert(h, v, new_dist);
    return;
  }
  if (new_dist >= h->dist[v]) return;
  h->dist[v] = new_dist;
  heap_up(h, h->pos[v]);
}

static int heap_is_empty(MinHeap* h) {
  return h->size == 0;
}

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

void free_route(Route* r) {
  if (r && r->path) {
    free(r->path);
    r->path = NULL;
    r->len = 0;
  }
}
