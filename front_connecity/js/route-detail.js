// Lógica da tela de detalhes da rota
document.addEventListener('DOMContentLoaded', async () => {
  const route = JSON.parse(sessionStorage.getItem('selectedRoute') || 'null');
  const params = JSON.parse(sessionStorage.getItem('routeParams') || '{}');
  const stepsContainer = document.getElementById('steps-container');
  const detailsContainer = document.getElementById('details-container');

  if (!route) {
    if (stepsContainer) {
      stepsContainer.innerHTML = `
        <div class="p-4 text-center">
          <p class="text-gray-600 mb-4">Rota não encontrada</p>
          <button onclick="window.history.back()" class="px-4 py-2 bg-blue-500 text-white rounded">
            Voltar
          </button>
        </div>
      `;
    }
    return;
  }

  // Buscar detalhes completos da rota usando o endpoint
  try {
    const details = await api.getRouteDetails({
      path: route.path,
      profile: params.profile || 'padrao'
    });

    // Renderizar passos
    if (stepsContainer) {
      stepsContainer.innerHTML = generateStepsFromDetails(details.steps || []);
    }

    // Renderizar detalhes
    if (detailsContainer) {
      const score = typeof calculateRouteScore === 'function' 
        ? calculateRouteScore(route) 
        : 85;
      
      detailsContainer.innerHTML = `
        <div class="grid grid-cols-2 gap-x-6 gap-y-4">
          <div class="flex justify-between border-b border-gray-200 py-3">
            <p class="text-sm text-[var(--text-secondary)]">Tempo total</p>
            <p class="text-sm font-medium text-[var(--text-primary)]">
              ${typeof formatTime === 'function' ? formatTime(details.total_time_min) : Math.round(details.total_time_min) + ' min'}
            </p>
          </div>
          <div class="flex justify-between border-b border-gray-200 py-3">
            <p class="text-sm text-[var(--text-secondary)]">Transferências</p>
            <p class="text-sm font-medium text-[var(--text-primary)]">
              ${details.transfers || route.transferencias || 0}
            </p>
          </div>
          <div class="flex justify-between border-b border-gray-200 py-3">
            <p class="text-sm text-[var(--text-secondary)]">Pontuação</p>
            <p class="text-sm font-medium text-[var(--text-primary)]">
              ${score}
            </p>
          </div>
          <div class="flex justify-between py-3">
            <p class="text-sm text-[var(--text-secondary)]">Barreiras evitadas</p>
            <p class="text-sm font-medium text-[var(--text-primary)]">
              ${details.barriers_avoided?.length || route.barreiras_evitas?.length || 0}
            </p>
          </div>
        </div>
      `;
    }

    // Salvar detalhes no sessionStorage
    sessionStorage.setItem('routeDetails', JSON.stringify(details));

  } catch (error) {
    console.error('Erro ao buscar detalhes:', error);
    // Fallback: usar dados básicos da rota
    if (stepsContainer) {
      stepsContainer.innerHTML = generateSteps(route.path || []);
    }
    if (detailsContainer) {
      const score = typeof calculateRouteScore === 'function' 
        ? calculateRouteScore(route) 
        : 85;
      detailsContainer.innerHTML = `
        <div class="grid grid-cols-2 gap-x-6 gap-y-4">
          <div class="flex justify-between border-b border-gray-200 py-3">
            <p class="text-sm text-[var(--text-secondary)]">Tempo total</p>
            <p class="text-sm font-medium text-[var(--text-primary)]">
              ${typeof formatTime === 'function' ? formatTime(route.tempo_total_min) : Math.round(route.tempo_total_min) + ' min'}
            </p>
          </div>
          <div class="flex justify-between border-b border-gray-200 py-3">
            <p class="text-sm text-[var(--text-secondary)]">Transferências</p>
            <p class="text-sm font-medium text-[var(--text-primary)]">
              ${route.transferencias || 0}
            </p>
          </div>
          <div class="flex justify-between border-b border-gray-200 py-3">
            <p class="text-sm text-[var(--text-secondary)]">Pontuação</p>
            <p class="text-sm font-medium text-[var(--text-primary)]">
              ${score}
            </p>
          </div>
          <div class="flex justify-between py-3">
            <p class="text-sm text-[var(--text-secondary)]">Barreiras evitadas</p>
            <p class="text-sm font-medium text-[var(--text-primary)]">
              ${route.barreiras_evitas?.length || 0}
            </p>
          </div>
        </div>
      `;
    }
  }

  // Adicionar função global para salvar rota
  window.saveCurrentRoute = function() {
    const name = prompt('Dê um nome para esta rota:');
    if (name && typeof saveFavorite === 'function') {
      saveFavorite(route, name);
      alert('Rota salva com sucesso!');
    }
  };

  // Função para salvar do popup
  window.saveFavoriteFromPopup = function() {
    const nameInput = document.getElementById('routeName');
    const name = nameInput?.value.trim();
    if (name && typeof saveFavorite === 'function') {
      saveFavorite(route, name);
      document.getElementById('favorite-popup').classList.add('hidden');
      alert('Rota salva com sucesso!');
    }
  };
});

/**
 * Gera HTML dos passos da rota a partir dos detalhes
 * @param {Array} steps - Array de steps do endpoint /route/details
 * @returns {string} HTML dos passos
 */
function generateStepsFromDetails(steps) {
  if (!steps || steps.length === 0) {
    return '<p class="text-gray-500">Nenhum passo disponível</p>';
  }

  return steps.map((step, index) => {
    const isLast = index === steps.length - 1;
    const mode = step.mode || 'pe';
    const icon = getStepIcon(mode);
    const instruction = getStepInstruction(step, mode);
    
    return `
      <div class="relative flex items-start gap-4">
        ${!isLast ? '<div class="absolute left-6 top-12 h-full w-0.5 bg-gray-300"></div>' : ''}
        <div class="relative z-10 flex size-12 shrink-0 items-center justify-center rounded-full bg-[var(--secondary-color)]">
          <span class="material-symbols-outlined text-[var(--text-primary)]">${icon}</span>
        </div>
        <div class="flex-1 pt-2.5">
          <p class="text-base font-medium text-[var(--text-primary)]">
            ${instruction}
          </p>
          <p class="text-sm text-[var(--text-secondary)]">
            ${step.from_name || step.from} → ${step.to_name || step.to}
          </p>
          ${step.time_min > 0 ? `<p class="text-xs text-[var(--text-secondary)] mt-1">${typeof formatTime === 'function' ? formatTime(step.time_min) : Math.round(step.time_min) + ' min'}</p>` : ''}
        </div>
      </div>
    `;
  }).join('');
}

/**
 * Gera HTML dos passos da rota (fallback simples)
 * @param {Array} path - Array de IDs dos nós
 * @returns {string} HTML dos passos
 */
function generateSteps(path) {
  if (!path || path.length === 0) {
    return '<p class="text-gray-500">Nenhum passo disponível</p>';
  }

  return path.map((node, index) => {
    const isLast = index === path.length - 1;
    const icon = index === 0 ? 'trip_origin' : 
                 isLast ? 'location_on' : 
                 'radio_button_checked';
    
    return `
      <div class="relative flex items-start gap-4">
        ${!isLast ? '<div class="absolute left-6 top-12 h-full w-0.5 bg-gray-300"></div>' : ''}
        <div class="relative z-10 flex size-12 shrink-0 items-center justify-center rounded-full bg-[var(--secondary-color)]">
          <span class="material-symbols-outlined text-[var(--text-primary)]">${icon}</span>
        </div>
        <div class="flex-1 pt-2.5">
          <p class="text-base font-medium text-[var(--text-primary)]">
            ${index === 0 ? 'Origem' : isLast ? 'Destino' : `Ponto ${index + 1}`}
          </p>
          <p class="text-sm text-[var(--text-secondary)]">${node}</p>
        </div>
      </div>
    `;
  }).join('');
}

/**
 * Obtém ícone baseado no modo de transporte
 */
function getStepIcon(mode) {
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
 * Gera instrução do passo
 */
function getStepInstruction(step, mode) {
  if (step.instruction) {
    return step.instruction;
  }
  
  const modeNames = {
    'metro': 'Pegue o metrô',
    'onibus': 'Pegue o ônibus',
    'pe': 'Caminhe',
    'trem': 'Pegue o trem',
    'bus': 'Pegue o ônibus',
    'subway': 'Pegue o metrô',
    'walk': 'Caminhe',
    'train': 'Pegue o trem'
  };
  
  const modeName = modeNames[mode?.toLowerCase()] || 'Continue';
  
  if (step.type === 'walk') {
    return 'Caminhe até o ponto de partida';
  }
  
  return `${modeName} até ${step.to_name || step.to}`;
}

