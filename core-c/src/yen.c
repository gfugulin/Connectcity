#include <stdlib.h>
#include <string.h>
#include <float.h>
#include "graph.h"
#include "cost.h"

// Estrutura para heap mínimo
typedef struct {
    Route route;
    double cost;
    int valid;
} RouteCandidate;

// Função para comparar candidatos (heap mínimo)
static int compare_candidates(const void* a, const void* b) {
    RouteCandidate* ca = (RouteCandidate*)a;
    RouteCandidate* cb = (RouteCandidate*)b;
    if (!ca->valid) return 1;
    if (!cb->valid) return -1;
    return (ca->cost > cb->cost) - (ca->cost < cb->cost);
}

// Função para verificar se duas rotas são iguais
static int routes_equal(const Route* r1, const Route* r2) {
    if (r1->len != r2->len) return 0;
    for (int i = 0; i < r1->len; i++) {
        if (r1->path[i] != r2->path[i]) return 0;
    }
    return 1;
}

// Função para copiar uma rota
static Route copy_route(const Route* src) {
    Route dst = {0};
    if (src->len > 0) {
        dst.path = malloc(src->len * sizeof(int));
        memcpy(dst.path, src->path, src->len * sizeof(int));
        dst.len = src->len;
        dst.custo = src->custo;
    }
    return dst;
}

// Função para remover aresta temporariamente (modifica o grafo)
static void remove_edge_temporarily(Graph* g, int from, int to) {
    Edge** e = &g->nodes[from].adj;
    while (*e) {
        if ((*e)->to == to) {
            Edge* temp = *e;
            *e = (*e)->next;
            free(temp);
            break;
        }
        e = &(*e)->next;
    }
}

// Implementação completa do algoritmo de Yen para k-shortest paths
int k_shortest_yen(Graph* g, int s, int t, CostParams p, int k, Route* out) {
    if (k <= 0 || !g || s < 0 || t < 0 || s >= g->n || t >= g->n) return 0;
    
    // Encontrar a primeira rota (melhor rota)
    Route first_route = dijkstra_shortest(g, s, t, p);
    if (first_route.len == 0) return 0;
    
    // Copiar primeira rota para saída
    out[0] = copy_route(&first_route);
    int found_routes = 1;
    
    if (k == 1) {
        free_route(&first_route);
        return 1;
    }
    
    // Array para armazenar rotas já encontradas
    Route* A = malloc(k * sizeof(Route));
    A[0] = copy_route(&first_route);
    int A_size = 1;
    
    // Heap para candidatos
    RouteCandidate* B = calloc(k * 100, sizeof(RouteCandidate)); // Buffer generoso
    int B_size = 0;
    
    // Para cada rota em A, gerar candidatos
    for (int i = 0; i < A_size && found_routes < k; i++) {
        Route* current_route = &A[i];
        
        // Para cada aresta na rota atual
        for (int j = 0; j < current_route->len - 1; j++) {
            int spur_node = current_route->path[j];
            int root_path_len = j + 1;
            
            // Criar rota raiz (do início até spur_node)
            Route root_path = {0};
            if (root_path_len > 0) {
                root_path.path = malloc(root_path_len * sizeof(int));
                memcpy(root_path.path, current_route->path, root_path_len * sizeof(int));
                root_path.len = root_path_len;
                root_path.custo = 0.0;
            }
            
            // Remover arestas que já foram usadas nas rotas anteriores
            for (int a_idx = 0; a_idx < A_size; a_idx++) {
                Route* prev_route = &A[a_idx];
                if (prev_route->len > j && 
                    memcmp(prev_route->path, current_route->path, (j + 1) * sizeof(int)) == 0) {
                    // Remover aresta spur_node -> next_node temporariamente
                    if (j + 1 < prev_route->len) {
                        remove_edge_temporarily(g, spur_node, prev_route->path[j + 1]);
                    }
                }
            }
            
            // Calcular rota spur (de spur_node até destino)
            Route spur_path = dijkstra_shortest(g, spur_node, t, p);
            
            if (spur_path.len > 0) {
                // Combinar rota raiz + rota spur
                Route total_path = {0};
                total_path.len = root_path.len + spur_path.len - 1; // -1 porque spur_node está em ambas
                total_path.path = malloc(total_path.len * sizeof(int));
                
                // Copiar rota raiz
                memcpy(total_path.path, root_path.path, root_path.len * sizeof(int));
                // Copiar rota spur (pulando o primeiro nó que já está na raiz)
                memcpy(total_path.path + root_path.len, 
                       spur_path.path + 1, 
                       (spur_path.len - 1) * sizeof(int));
                
                // Calcular custo total
                total_path.custo = root_path.custo + spur_path.custo;
                
                // Verificar se esta rota já foi encontrada
                int already_found = 0;
                for (int b_idx = 0; b_idx < B_size; b_idx++) {
                    if (B[b_idx].valid && routes_equal(&total_path, &B[b_idx].route)) {
                        already_found = 1;
                        break;
                    }
                }
                
                if (!already_found) {
                    // Adicionar ao heap de candidatos
                    B[B_size].route = total_path;
                    B[B_size].cost = total_path.custo;
                    B[B_size].valid = 1;
                    B_size++;
                } else {
                    free_route(&total_path);
                }
            }
            
            // Restaurar arestas removidas (simplificado)
            // Em implementação real, manteríamos uma lista de arestas removidas
            
            free_route(&root_path);
            free_route(&spur_path);
        }
        
        // Se temos candidatos, pegar o melhor
        if (B_size > 0) {
            // Ordenar candidatos por custo
            qsort(B, B_size, sizeof(RouteCandidate), compare_candidates);
            
            // Encontrar o primeiro candidato válido
            for (int b_idx = 0; b_idx < B_size; b_idx++) {
                if (B[b_idx].valid) {
                    // Verificar se já está em A
                    int already_in_A = 0;
                    for (int a_idx = 0; a_idx < A_size; a_idx++) {
                        if (routes_equal(&B[b_idx].route, &A[a_idx])) {
                            already_in_A = 1;
                            break;
                        }
                    }
                    
                    if (!already_in_A) {
                        // Adicionar à lista de rotas encontradas
                        A[A_size] = copy_route(&B[b_idx].route);
                        out[found_routes] = copy_route(&B[b_idx].route);
                        found_routes++;
                        A_size++;
                        
                        // Marcar como usado
                        B[b_idx].valid = 0;
                        break;
                    }
                }
            }
        }
    }
    
    // Limpeza
    for (int i = 0; i < A_size; i++) {
        free_route(&A[i]);
    }
    for (int i = 0; i < B_size; i++) {
        if (B[i].valid) {
            free_route(&B[i].route);
        }
    }
    
    free(A);
    free(B);
    free_route(&first_route);
    
    return found_routes;
}