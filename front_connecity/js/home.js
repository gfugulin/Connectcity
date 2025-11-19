// Lógica da tela inicial (planejamento de rota)
document.addEventListener('DOMContentLoaded', async () => {
  // Elementos do formulário
  const fromInput = document.querySelector('input[type="text"][value="Sua localização"]') || 
                    document.querySelector('input[placeholder*="De onde"]') ||
                    document.querySelector('input[placeholder*="Origem"]');
  
  const toInput = document.querySelector('input[placeholder="Destino"]') ||
                  document.querySelector('input[placeholder*="Para onde"]');
  
  const profileInputs = document.querySelectorAll('input[name="mobility-profile"]');
  const searchBtn = document.querySelector('button:has(.arrow_forward), button:contains("Buscar")') ||
                    document.querySelector('button[type="button"]') ||
                    document.querySelector('button');

  if (!searchBtn) {
    console.error('Botão de busca não encontrado');
    return;
  }

  // Buscar perfis disponíveis
  try {
    const profilesData = await api.getProfiles();
    console.log('Perfis disponíveis:', profilesData);
  } catch (error) {
    console.warn('Não foi possível carregar perfis:', error);
  }

  // Handler do botão de busca
  searchBtn.addEventListener('click', async (e) => {
    e.preventDefault();
    
    const from = fromInput?.value.trim() || '';
    const to = toInput?.value.trim() || '';
    const profile = Array.from(profileInputs).find(r => r.checked)?.value || 'padrao';
    
    // Validação básica
    if (!from || !to) {
      alert('Por favor, preencha origem e destino');
      return;
    }

    // Desabilitar botão durante busca
    const originalText = searchBtn.textContent;
    searchBtn.disabled = true;
    searchBtn.textContent = 'Buscando...';
    
    try {
      // Buscar rotas
      const routes = await api.searchRoutes(from, to, profile);
      
      if (routes.length === 0) {
        alert('Nenhuma rota encontrada entre os pontos selecionados');
        return;
      }

      // Salvar rotas no sessionStorage
      sessionStorage.setItem('routes', JSON.stringify(routes));
      sessionStorage.setItem('routeParams', JSON.stringify({ from, to, profile }));
      
      // Navegar para página de resultados
      window.location.href = 'routes.html';
      
    } catch (error) {
      let errorMessage = 'Erro ao buscar rota';
      
      if (error.response) {
        // Erro da API
        const detail = error.response.data?.detail || error.response.data?.message;
        if (detail) {
          errorMessage = detail;
        } else if (error.response.status === 404) {
          errorMessage = 'Localização não encontrada. Verifique os IDs dos nós.';
        } else if (error.response.status === 422) {
          errorMessage = 'Não foi possível calcular a rota entre esses pontos.';
        }
      } else if (error.request) {
        errorMessage = 'Não foi possível conectar com o servidor. Verifique se a API está rodando.';
      }
      
      // Usar função utilitária se disponível, senão usar alert
      if (typeof showError === 'function') {
        showError(error);
      } else {
        alert(errorMessage);
        console.error('Erro completo:', error);
      }
      
    } finally {
      // Reabilitar botão
      searchBtn.disabled = false;
      searchBtn.textContent = originalText;
    }
  });

  // Permitir buscar com Enter
  [fromInput, toInput].forEach(input => {
    if (input) {
      input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          searchBtn.click();
        }
      });
    }
  });

  // Autocomplete simples (opcional - pode melhorar depois)
  let searchTimeout;
  [fromInput, toInput].forEach((input, index) => {
    if (input) {
      input.addEventListener('input', async (e) => {
        const query = e.target.value.trim();
        
        // Limpar timeout anterior
        clearTimeout(searchTimeout);
        
        // Se query tem pelo menos 2 caracteres, buscar
        if (query.length >= 2) {
          searchTimeout = setTimeout(async () => {
            try {
              const nodes = await api.searchNodes(query);
              // Por enquanto, apenas logar resultados
              // TODO: Mostrar dropdown de sugestões
              if (nodes.length > 0) {
                console.log(`Sugestões para "${query}":`, nodes);
              }
            } catch (error) {
              // Ignorar erros de busca silenciosamente
            }
          }, 300); // Debounce de 300ms
        }
      });
    }
  });
});

