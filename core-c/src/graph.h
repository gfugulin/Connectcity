#ifndef CONNEC_GRAPH_H
#define CONNEC_GRAPH_H
#include <stdint.h>

#ifdef _WIN32
#  ifdef CONNEC_BUILD
#    define CONNEC_API __declspec(dllexport)
#  else
#    define CONNEC_API __declspec(dllimport)
#  endif
#else
#  define CONNEC_API
#endif

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

typedef struct Graph { Node* nodes; int n; } Graph;

typedef struct Route { int* path; int len; double custo; } Route;

typedef struct CostParams {
  double alpha, beta, gamma, delta; // pesos em minutos
  int chuva_on;   // 0/1
  int perfil_pcd; // 0/1 (mantido para futura customização)
} CostParams;

CONNEC_API Graph* load_graph_from_csv(const char* nodes_csv, const char* edges_csv);
CONNEC_API void    free_graph(Graph* g);

CONNEC_API Route   dijkstra_shortest(Graph* g, int s, int t, CostParams p);
CONNEC_API int     k_shortest_yen(Graph* g, int s, int t, CostParams p, int k, Route* out);
CONNEC_API void    free_route(Route* r);

CONNEC_API int     node_index_by_id(Graph* g, const char* id);

// Edge analysis functions
typedef struct {
    int from, to;
    char issue_type[32];
    double current_cost;
    double potential_savings;
    int affected_routes;
    double impact_score;
    int priority;
} EdgeImprovement;

typedef struct {
    EdgeImprovement* improvements;
    int count;
    int capacity;
} EdgeAnalysisResult;

CONNEC_API EdgeAnalysisResult* analyze_edge_improvements(Graph* g, CostParams p, int max_results);
CONNEC_API void                free_edge_analysis(EdgeAnalysisResult* result);

#endif
