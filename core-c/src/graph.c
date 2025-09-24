#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "graph.h"

static Edge* new_edge(int to, double t_min, int tr, int es, int cr, int al, int modo) {
  Edge* e = (Edge*)calloc(1, sizeof(Edge));
  e->to = to; e->t_min = t_min; e->transferencia = tr; e->escada = es;
  e->calcada_ruim = cr; e->risco_alag = al; e->modo = modo; e->next = NULL; return e;
}

int node_index_by_id(Graph* g, const char* id) {
  for (int i=0;i<g->n;i++) if (strcmp(g->nodes[i].id,id)==0) return i; return -1;
}

Graph* load_graph_from_csv(const char* nodes_csv, const char* edges_csv) {
  FILE* fn = fopen(nodes_csv, "r"); if (!fn) return NULL;
  FILE* fe = fopen(edges_csv, "r"); if (!fe) { fclose(fn); return NULL; }

  // count nodes
  char line[512]; int n=0; fgets(line, sizeof line, fn); // header
  while (fgets(line, sizeof line, fn)) n++;
  fseek(fn, 0, SEEK_SET); fgets(line, sizeof line, fn);

  Graph* g = (Graph*)calloc(1, sizeof(Graph));
  g->n = n; g->nodes = (Node*)calloc(n, sizeof(Node));

  int i=0; while (fgets(line, sizeof line, fn)) {
    // id,name,lat,lon,tipo
    char id[32], name[128], tipo[32]; double lat, lon;
    if (sscanf(line, "%31[^,],%127[^,],%lf,%lf,%31[^\n]", id, name, &lat, &lon, tipo) == 5) {
      strncpy(g->nodes[i].id, id, 15); g->nodes[i].lat = lat; g->nodes[i].lon = lon; g->nodes[i].adj = NULL; i++;
    }
  }
  fclose(fn);

  // edges
  fgets(line, sizeof line, fe); // header
  while (fgets(line, sizeof line, fe)) {
    // from,to,tempo_min,transferencia,escada,calcada_ruim,risco_alag,modo
    char from[32], to[32], modo_s[32]; double t; int tr, es, cr, al; int modo=0;
    if (sscanf(line, "%31[^,],%31[^,],%lf,%d,%d,%d,%d,%31[^\n]", from, to, &t, &tr, &es, &cr, &al, modo_s) == 8) {
      if (strcmp(modo_s,"pe")==0) modo=0; else if (strcmp(modo_s,"onibus")==0) modo=1; else if (strcmp(modo_s,"metro")==0) modo=2; else if (strcmp(modo_s,"trem")==0) modo=3;
      int u = node_index_by_id(g, from); int v = node_index_by_id(g, to); if (u<0||v<0) continue;
      Edge* e = new_edge(v, t, tr, es, cr, al, modo); e->next = g->nodes[u].adj; g->nodes[u].adj = e;
    }
  }
  fclose(fe);
  return g;
}

void free_graph(Graph* g) {
  if (!g) return; for (int i=0;i<g->n;i++) { Edge* e=g->nodes[i].adj; while (e){ Edge* nx=e->next; free(e); e=nx; } }
  free(g->nodes); free(g);
}
