#ifndef CONNEC_COST_H
#define CONNEC_COST_H
#include "graph.h"

static inline double edge_cost(const Edge* e, CostParams p) {
  double c = e->t_min;
  c += p.alpha * (e->transferencia ? 1.0 : 0.0);
  c += p.beta  * (e->escada ? 1.0 : 0.0);
  c += p.gamma * (e->calcada_ruim ? 1.0 : 0.0);
  if (p.chuva_on) c += p.delta * (e->risco_alag ? 1.0 : 0.0);
  return c;
}

#endif
