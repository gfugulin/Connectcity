// Lógica da tela de favoritos
document.addEventListener('DOMContentLoaded', () => {
  const favorites = getFavorites();
  const container = document.querySelector('.space-y-4') || 
                    document.querySelector('main > div') ||
                    document.querySelector('main');

  if (!container) {
    console.error('Container de favoritos não encontrado');
    return;
  }

  if (favorites.length === 0) {
    container.innerHTML = `
      <div class="p-4 text-center">
        <span class="material-symbols-outlined text-6xl text-gray-300 mb-4">bookmark</span>
        <p class="text-gray-600 mb-4">Nenhum favorito salvo</p>
        <a href="index.html" class="text-blue-500 underline">Buscar rotas</a>
      </div>
    `;
    return;
  }

  // Renderizar favoritos
  container.innerHTML = favorites.map(fav => {
    const route = fav.route || {};
    const time = formatTime(route.tempo_total_min || 0);
    const icon = getFavoriteIcon(fav.name);
    
    return `
      <div class="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer" 
           onclick="viewFavoriteRoute('${fav.id}')">
        <div class="flex items-center gap-4 p-4">
          <div class="flex items-center justify-center rounded-full bg-blue-100 text-[var(--primary-color)] shrink-0 size-12">
            <span class="material-symbols-outlined text-2xl">${icon}</span>
          </div>
          <div class="flex-grow">
            <div class="flex justify-between items-start">
              <h2 class="text-gray-800 text-lg font-semibold leading-tight">${fav.name}</h2>
              <button onclick="event.stopPropagation(); deleteFavoriteById('${fav.id}')" 
                      class="text-gray-400 hover:text-gray-600">
                <span class="material-symbols-outlined">delete</span>
              </button>
            </div>
            <p class="text-gray-500 text-sm font-normal mt-1">
              ${fav.from || route.from || 'Origem'} → ${fav.to || route.to || 'Destino'}
            </p>
            <div class="flex items-center gap-4 mt-3 text-gray-600">
              <div class="flex items-center gap-1">
                <span class="material-symbols-outlined text-lg">schedule</span>
                <span class="text-sm font-medium">${time}</span>
              </div>
              ${route.transferencias ? `
                <div class="flex items-center gap-1">
                  <span class="material-symbols-outlined text-lg">swap_horiz</span>
                  <span class="text-sm">${route.transferencias} transferência(s)</span>
                </div>
              ` : ''}
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');

  // Funções globais
  window.viewFavoriteRoute = function(id) {
    const favorite = favorites.find(f => f.id === id);
    if (favorite && favorite.route) {
      sessionStorage.setItem('selectedRoute', JSON.stringify(favorite.route));
      window.location.href = 'route-detail.html';
    }
  };

  window.deleteFavoriteById = function(id) {
    if (confirm('Deseja remover este favorito?')) {
      deleteFavorite(id);
      location.reload();
    }
  };
});

/**
 * Obtém ícone baseado no nome do favorito
 * @param {string} name - Nome do favorito
 * @returns {string} Nome do ícone
 */
function getFavoriteIcon(name) {
  const nameLower = name.toLowerCase();
  if (nameLower.includes('casa') || nameLower.includes('home')) return 'home';
  if (nameLower.includes('trabalho') || nameLower.includes('work')) return 'work';
  if (nameLower.includes('faculdade') || nameLower.includes('escola') || nameLower.includes('school')) return 'school';
  if (nameLower.includes('academia') || nameLower.includes('gym')) return 'fitness_center';
  if (nameLower.includes('mercado') || nameLower.includes('shopping')) return 'shopping_cart';
  return 'place';
}

