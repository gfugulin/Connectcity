// Lógica da tela de resultados de rotas
document.addEventListener('DOMContentLoaded', () => {
  const routes = JSON.parse(sessionStorage.getItem('routes') || '[]');
  const params = JSON.parse(sessionStorage.getItem('routeParams') || '{}');
  const container = document.getElementById('routes-container') || 
                    document.querySelector('.space-y-4') || 
                    document.querySelector('main');

  if (!container) {
    console.error('Container de rotas não encontrado');
    return;
  }

  if (routes.length === 0) {
    container.innerHTML = `
      <div class="p-4 text-center">
        <p class="text-gray-600">Nenhuma rota encontrada</p>
        <button onclick="window.history.back()" class="mt-4 px-4 py-2 bg-blue-500 text-white rounded">
          Voltar
        </button>
      </div>
    `;
    return;
  }

  // Renderizar rotas
  container.innerHTML = routes.map((route, index) => {
    const isRecommended = index === 0;
    // Usar função de utils.js se disponível
    const score = typeof calculateRouteScore === 'function' 
      ? calculateRouteScore(route) 
      : 85 - (index * 5);
    const transportIcons = getTransportIcons(route.path || []);
    
    return `
      <div class="rounded-lg border border-[var(--c-border)] bg-[var(--c-surface)] p-4 shadow-sm cursor-pointer hover:shadow-md transition-shadow" 
           onclick="viewRoute(${route.id})">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="mb-2 flex items-center gap-4">
              <p class="text-xl font-bold text-[var(--c-text-primary)]">
                ${Math.round(route.tempo_total_min)} min
              </p>
              <div class="flex items-center gap-2 text-[var(--c-text-secondary)]">
                ${transportIcons}
              </div>
            </div>
            <p class="text-sm text-[var(--c-text-secondary)]">
              ${route.transferencias} transferência${route.transferencias !== 1 ? 's' : ''}
            </p>
          </div>
          <div class="flex flex-col items-end">
            ${isRecommended ? '<p class="text-sm font-semibold text-[var(--c-primary)]">Recomendada</p>' : ''}
            <p class="text-xs text-[var(--c-text-secondary)]">Pontuação: ${score}</p>
          </div>
        </div>
        <div class="mt-4 h-24 w-full rounded-md bg-gray-200 flex items-center justify-center">
          <span class="text-gray-400 text-sm">Mapa da rota</span>
        </div>
      </div>
    `;
  }).join('');

  // Adicionar função global para visualizar rota
  window.viewRoute = (id) => {
    const route = routes.find(r => r.id === id);
    if (route) {
      sessionStorage.setItem('selectedRoute', JSON.stringify(route));
      window.location.href = 'route-detail.html';
    }
  };
});

// Função movida para utils.js - usar calculateRouteScore de lá

/**
 * Retorna ícones de transporte baseado no path
 * Usa modos da rota se disponível, senão mostra todos
 */
function getTransportIcons(path) {
  // Se a rota tem informação de modos, usar
  if (path && path.length > 0) {
    // Por enquanto, mostrar ícones genéricos
    // TODO: Analisar path para determinar modos reais
  }
  return `
    <span class="material-symbols-outlined text-lg">directions_bus</span>
    <span class="material-symbols-outlined text-lg">directions_subway</span>
    <span class="material-symbols-outlined text-lg">directions_walk</span>
  `;
}

