/**
 * Formata tempo em minutos para string legível
 * @param {number} minutes - Tempo em minutos
 * @returns {string} Tempo formatado (ex: "45 min" ou "1h 30min")
 */
export function formatTime(minutes) {
  if (minutes < 60) {
    return `${Math.round(minutes)} min`;
  }
  const hours = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);
  return mins > 0 ? `${hours}h ${mins}min` : `${hours}h`;
}

/**
 * Calcula pontuação da rota (0-100)
 * @param {Object} route - Objeto de rota
 * @returns {number} Pontuação de 0 a 100
 */
export function calculateRouteScore(route) {
  let score = 100;
  
  // Penalizar por tempo (máximo 30 pontos)
  score -= Math.min(route.tempo_total_min / 2, 30);
  
  // Penalizar por transferências (10 pontos cada)
  score -= (route.transferencias || 0) * 10;
  
  // Bonus por evitar barreiras (5 pontos cada)
  score += (route.barreiras_evitas?.length || 0) * 5;
  
  return Math.max(0, Math.min(100, Math.round(score)));
}

/**
 * Obtém ícone de transporte baseado no modo
 * @param {string} mode - Modo de transporte ('metro', 'onibus', 'pe', 'trem')
 * @returns {string} Nome do ícone Material Symbols
 */
export function getTransportIcon(mode) {
  const icons = {
    'metro': 'directions_subway',
    'onibus': 'directions_bus',
    'pe': 'directions_walk',
    'trem': 'train',
    'bus': 'directions_bus',
    'subway': 'directions_subway',
    'walk': 'directions_walk',
    'train': 'train'
  };
  return icons[mode?.toLowerCase()] || 'directions_walk';
}

/**
 * Exibe mensagem de erro amigável
 * @param {Error} error - Objeto de erro do axios
 * @returns {string} Mensagem de erro
 */
export function getErrorMessage(error) {
  let message = 'Erro ao processar requisição';
  
  if (error.response) {
    // Erro da API
    const detail = error.response.data?.detail || error.response.data?.message || '';
    
    if (detail.includes('não encontrado') || detail.includes('not found')) {
      message = 'Localização não encontrada. Verifique os IDs dos nós.';
    } else if (detail.includes('sem caminho') || detail.includes('no path')) {
      message = 'Não há rota disponível entre esses pontos.';
    } else if (detail.includes('inválido') || detail.includes('invalid')) {
      message = 'Dados inválidos. Verifique os campos preenchidos.';
    } else if (detail) {
      message = detail;
    } else if (error.response.status === 404) {
      message = 'Recurso não encontrado.';
    } else if (error.response.status === 422) {
      message = 'Não foi possível processar a requisição.';
    } else if (error.response.status === 500) {
      message = 'Erro no servidor. Tente novamente mais tarde.';
    }
  } else if (error.request) {
    // Sem resposta do servidor
    message = 'Não foi possível conectar com o servidor. Verifique se a API está rodando.';
  } else {
    // Erro na configuração da requisição
    message = error.message || 'Erro desconhecido.';
  }
  
  return message;
}

/**
 * Salva favorito no localStorage
 * @param {Object} route - Objeto de rota
 * @param {string} name - Nome do favorito
 * @param {string} icon - Ícone selecionado (opcional)
 * @returns {Object} Favorito salvo
 */
export function saveFavorite(route, name, icon = null) {
  const favorites = JSON.parse(localStorage.getItem('favorites') || '[]');
  const favorite = {
    id: Date.now().toString(),
    name: name || `Rota ${favorites.length + 1}`,
    route: route,
    from: route.from || route.from_name || '',
    to: route.to || route.to_name || '',
    fromId: route.fromId || null,
    toId: route.toId || null,
    profile: route.profile || 'padrao',
    icon: icon || getFavoriteIcon(name),
    createdAt: new Date().toISOString()
  };
  favorites.push(favorite);
  localStorage.setItem('favorites', JSON.stringify(favorites));
  return favorite;
}

/**
 * Remove favorito do localStorage
 * @param {string} id - ID do favorito
 */
export function deleteFavorite(id) {
  const favorites = JSON.parse(localStorage.getItem('favorites') || '[]');
  const filtered = favorites.filter(f => f.id !== id);
  localStorage.setItem('favorites', JSON.stringify(filtered));
  return filtered;
}

/**
 * Obtém todos os favoritos
 * @returns {Array} Lista de favoritos
 */
export function getFavorites() {
  return JSON.parse(localStorage.getItem('favorites') || '[]');
}

/**
 * Obtém preferências do usuário
 * @returns {Object} Preferências
 */
export function getUserPreferences() {
  return JSON.parse(localStorage.getItem('userPreferences') || '{}');
}

/**
 * Salva preferências do usuário
 * @param {Object} preferences - Preferências
 */
export function saveUserPreferences(preferences) {
  localStorage.setItem('userPreferences', JSON.stringify(preferences));
}

/**
 * Obtém ícone baseado no nome do favorito
 * @param {string} name - Nome do favorito
 * @returns {string} Nome do ícone
 */
export function getFavoriteIcon(name) {
  const nameLower = name.toLowerCase();
  if (nameLower.includes('casa') || nameLower.includes('home')) return 'home';
  if (nameLower.includes('trabalho') || nameLower.includes('work')) return 'work';
  if (nameLower.includes('faculdade') || nameLower.includes('universidade') || nameLower.includes('university')) return 'school';
  if (nameLower.includes('escola') || nameLower.includes('school')) return 'school';
  if (nameLower.includes('academia') || nameLower.includes('gym')) return 'fitness_center';
  if (nameLower.includes('mercado') || nameLower.includes('shopping')) return 'shopping_cart';
  return 'place';
}

