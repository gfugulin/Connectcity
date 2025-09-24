#include <stdlib.h>
#include <float.h>
#include "graph.h"
#include "cost.h"

typedef struct { double key; int v; } Pair;
static int cmp(const void* a, const void* b){ double d=((Pair*)a)->key-((Pair*)b)->key; return d<0?-1:(d>0?1:0);}

Route dijkstra_shortest(Graph* g, int s, int t, CostParams p){
  int n=g->n; double* dist=calloc(n,sizeof(double)); int* prev=calloc(n,sizeof(int));
  for(int i=0;i<n;i++){ dist[i]=DBL_MAX; prev[i]=-1; }
  dist[s]=0.0;
  // vetor como heap simples (re-sorting)
  Pair* Q=calloc(n,sizeof(Pair)); int qn=0; for(int i=0;i<n;i++){ Q[i].key=dist[i]; Q[i].v=i; } qn=n;
  while(qn>0){ qsort(Q, qn, sizeof(Pair), cmp); int u=Q[0].v; // extrai min
    // remove u
    for(int i=1;i<qn;i++) Q[i-1]=Q[i]; qn--;
    if (u==t) break;
    for(Edge* e=g->nodes[u].adj; e; e=e->next){ double w=edge_cost(e,p); if (dist[u]+w < dist[e->to]){ dist[e->to]=dist[u]+w; prev[e->to]=u; for(int i=0;i<qn;i++) if(Q[i].v==e->to){ Q[i].key=dist[e->to]; break; } } }
  }
  // reconstrói caminho
  Route r={0}; if (dist[t]==DBL_MAX){ free(dist); free(prev); free(Q); return r; }
  int len=0; for(int x=t;x!=-1;x=prev[x]) len++; r.path=malloc(len*sizeof(int)); r.len=len; r.custo=dist[t];
  int x=t; for(int i=len-1;i>=0;i--){ r.path[i]=x; x=prev[x]; }
  free(dist); free(prev); free(Q); return r;
}

void free_route(Route* r){ if(r && r->path){ free(r->path); r->path=NULL; r->len=0; }}
