#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "graph.h"
#include "cost.h"

// Declaração forward
static void sort_improvements_by_impact(EdgeAnalysisResult* result);

// Função para calcular impacto de uma melhoria específica
double calculate_improvement_impact(Graph* g, int from, int to, const char* issue_type, CostParams p) {
    if (!g || from < 0 || to < 0 || from >= g->n || to >= g->n) return 0.0;
    
    // Encontrar a aresta específica
    Edge* e = g->nodes[from].adj;
    while (e && e->to != to) {
        e = e->next;
    }
    
    if (!e) return 0.0;
    
    // Calcular custo atual
    double current_cost = edge_cost(e, p);
    
    // Calcular custo potencial após melhoria
    double potential_cost = e->t_min; // Apenas tempo base
    
    // Aplicar pesos baseado no tipo de melhoria
    if (strcmp(issue_type, "escada") == 0 && e->escada) {
        potential_cost += p.alpha * (e->transferencia ? 1.0 : 0.0);
        potential_cost += p.gamma * (e->calcada_ruim ? 1.0 : 0.0);
        if (p.chuva_on) potential_cost += p.delta * (e->risco_alag ? 1.0 : 0.0);
    } else if (strcmp(issue_type, "calcada_ruim") == 0 && e->calcada_ruim) {
        potential_cost += p.alpha * (e->transferencia ? 1.0 : 0.0);
        potential_cost += p.beta * (e->escada ? 1.0 : 0.0);
        if (p.chuva_on) potential_cost += p.delta * (e->risco_alag ? 1.0 : 0.0);
    } else if (strcmp(issue_type, "risco_alag") == 0 && e->risco_alag) {
        potential_cost += p.alpha * (e->transferencia ? 1.0 : 0.0);
        potential_cost += p.beta * (e->escada ? 1.0 : 0.0);
        potential_cost += p.gamma * (e->calcada_ruim ? 1.0 : 0.0);
    } else if (strcmp(issue_type, "transferencia") == 0 && e->transferencia) {
        potential_cost += p.beta * (e->escada ? 1.0 : 0.0);
        potential_cost += p.gamma * (e->calcada_ruim ? 1.0 : 0.0);
        if (p.chuva_on) potential_cost += p.delta * (e->risco_alag ? 1.0 : 0.0);
    } else {
        return 0.0; // Não há melhoria possível
    }
    
    return current_cost - potential_cost;
}

// Função para contar rotas afetadas por uma aresta
int count_affected_routes(Graph* g, int from, int to, CostParams p) {
    int count = 0;
    
    // Para cada par de nós, verificar se a aresta está na rota mais curta
    for (int s = 0; s < g->n; s++) {
        for (int t = 0; t < g->n; t++) {
            if (s == t) continue;
            
            Route route = dijkstra_shortest(g, s, t, p);
            if (route.len > 0) {
                // Verificar se a aresta está na rota
                for (int i = 0; i < route.len - 1; i++) {
                    if (route.path[i] == from && route.path[i + 1] == to) {
                        count++;
                        break;
                    }
                }
                free_route(&route);
            }
        }
    }
    
    return count;
}

// Função principal para análise de arestas
EdgeAnalysisResult* analyze_edge_improvements(Graph* g, CostParams p, int max_results) {
    if (!g || max_results <= 0) return NULL;
    
    EdgeAnalysisResult* result = malloc(sizeof(EdgeAnalysisResult));
    result->improvements = malloc(max_results * sizeof(EdgeImprovement));
    result->count = 0;
    result->capacity = max_results;
    
    // Analisar todas as arestas do grafo
    for (int from = 0; from < g->n; from++) {
        Edge* e = g->nodes[from].adj;
        while (e && result->count < max_results) {
            int to = e->to;
            
            // Verificar cada tipo de melhoria possível
            const char* issue_types[] = {"escada", "calcada_ruim", "risco_alag", "transferencia"};
            int issue_checks[] = {e->escada, e->calcada_ruim, e->risco_alag, e->transferencia};
            
            for (int i = 0; i < 4; i++) {
                if (issue_checks[i] && result->count < max_results) {
                    double savings = calculate_improvement_impact(g, from, to, issue_types[i], p);
                    
                    if (savings > 0.1) { // Apenas melhorias significativas
                        EdgeImprovement* imp = &result->improvements[result->count];
                        imp->from = from;
                        imp->to = to;
                        strncpy(imp->issue_type, issue_types[i], 31);
                        imp->issue_type[31] = '\0';
                        imp->current_cost = edge_cost(e, p);
                        imp->potential_savings = savings;
                        imp->affected_routes = count_affected_routes(g, from, to, p);
                        imp->impact_score = savings * imp->affected_routes;
                        imp->priority = result->count + 1;
                        
                        result->count++;
                    }
                }
            }
            
            e = e->next;
        }
    }
    
    // Ordenar por impacto
    sort_improvements_by_impact(result);
    
    return result;
}

// Função para ordenar melhorias por impacto
static void sort_improvements_by_impact(EdgeAnalysisResult* result) {
    if (!result || result->count <= 1) return;
    
    // Bubble sort simples (adequado para pequenos datasets)
    for (int i = 0; i < result->count - 1; i++) {
        for (int j = 0; j < result->count - i - 1; j++) {
            if (result->improvements[j].impact_score < result->improvements[j + 1].impact_score) {
                EdgeImprovement temp = result->improvements[j];
                result->improvements[j] = result->improvements[j + 1];
                result->improvements[j + 1] = temp;
            }
        }
    }
    
    // Atualizar prioridades
    for (int i = 0; i < result->count; i++) {
        result->improvements[i].priority = i + 1;
    }
}

// Função para liberar memória
void free_edge_analysis(EdgeAnalysisResult* result) {
    if (result) {
        if (result->improvements) {
            free(result->improvements);
        }
        free(result);
    }
}
