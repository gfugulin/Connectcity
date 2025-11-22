import axios from 'axios';

const API_BASE = 'http://localhost:8080';

const api = {
  /**
   * Verifica se a API está online
   */
  async getHealth() {
    try {
      const res = await axios.get(`${API_BASE}/health`);
      return res.data;
    } catch (error) {
      console.error('API não está disponível:', error);
      throw error;
    }
  },

  /**
   * Busca rotas alternativas
   * @param {string} from - ID do nó de origem
   * @param {string} to - ID do nó de destino
   * @param {string} profile - Perfil ('padrao', 'idoso' ou 'pcd')
   * @param {number} k - Número de alternativas (padrão: 3)
   */
  async searchRoutes(from, to, profile = 'padrao', k = 3) {
    try {
      const res = await axios.post(`${API_BASE}/alternatives`, {
        from: from,
        to: to,
        perfil: profile,
        chuva: false,
        k: k
      });
      return res.data.alternatives;
    } catch (error) {
      console.error('Erro ao buscar rotas:', error);
      if (error.response) {
        // Erro com resposta do servidor
        console.error('Status:', error.response.status);
        console.error('Dados:', error.response.data);
        throw new Error(error.response.data?.detail || `Erro ${error.response.status}: ${error.response.statusText}`);
      } else if (error.request) {
        // Requisição feita mas sem resposta
        console.error('Sem resposta do servidor. Verifique se o backend está rodando em', API_BASE);
        throw new Error('Servidor não está respondendo. Verifique se o backend está rodando.');
      } else {
        // Erro ao configurar a requisição
        console.error('Erro na configuração:', error.message);
        throw error;
      }
    }
  },

  /**
   * Calcula melhor rota
   * @param {string} from - ID do nó de origem
   * @param {string} to - ID do nó de destino
   * @param {string} profile - Perfil ('padrao', 'idoso' ou 'pcd')
   */
  async getRoute(from, to, profile = 'padrao') {
    try {
      const res = await axios.post(`${API_BASE}/route`, {
        from: from,
        to: to,
        perfil: profile,
        chuva: false
      });
      return res.data;
    } catch (error) {
      console.error('Erro ao calcular rota:', error);
      throw error;
    }
  },

  /**
   * Lista perfis disponíveis
   */
  async getProfiles() {
    try {
      const res = await axios.get(`${API_BASE}/profiles`);
      return res.data;
    } catch (error) {
      console.error('Erro ao buscar perfis:', error);
      throw error;
    }
  },

  /**
   * Lista todos os nós do grafo
   */
  async getNodes() {
    try {
      const res = await axios.get(`${API_BASE}/nodes`);
      return res.data.nodes;
    } catch (error) {
      console.error('Erro ao listar nós:', error);
      throw error;
    }
  },

  /**
   * Busca nós por nome ou ID (autocomplete)
   * @param {string} query - Termo de busca
   */
  async searchNodes(query) {
    try {
      const res = await axios.get(`${API_BASE}/nodes/search`, {
        params: { q: query }
      });
      return res.data.nodes;
    } catch (error) {
      console.error('Erro ao buscar nós:', error);
      throw error;
    }
  },

  /**
   * Obtém detalhes completos de uma rota
   * @param {string} from - ID do nó de origem (opcional se path fornecido)
   * @param {string} to - ID do nó de destino (opcional se path fornecido)
   * @param {Array} path - Path da rota (opcional, se não fornecido calcula rota)
   * @param {string} profile - Perfil ('padrao', 'idoso' ou 'pcd')
   */
  async getRouteDetails({ from, to, path, profile = 'padrao' }) {
    try {
      const payload = {
        perfil: profile,
        chuva: false,
      };

      if (Array.isArray(path) && path.length > 0) {
        payload.path = path;
      } else if (from && to) {
        payload.from = from;
        payload.to = to;
      } else {
        throw new Error('Parâmetros insuficientes para /route/details');
      }

      const res = await axios.post(`${API_BASE}/route/details`, payload);
      return res.data;
    } catch (error) {
      console.error('Erro ao obter detalhes da rota:', error);

      // Se backend mandou detail, reempacotar em uma mensagem amigável
      if (error.response && error.response.data && error.response.data.detail) {
        const detail = error.response.data.detail;
        const msg =
          typeof detail === 'string'
            ? detail
            : detail.message || 'Erro ao obter detalhes da rota';
        throw new Error(msg);
      }

      throw error;
    }
  },

  /**
   * Reporta uma barreira encontrada pelo usuário.
   * O formato deve seguir o contrato do backend /barriers/report.
   * @param {Object} report - Dados do relato de barreira
   * @param {number} report.route_id - ID da rota (opcional)
   * @param {string} report.from_node - ID do nó de origem (opcional)
   * @param {string} report.to_node - ID do nó de destino (opcional)
   * @param {number} report.step_index - Índice do passo na rota (opcional)
   * @param {string} report.node_id - ID do nó onde a barreira foi encontrada (opcional)
   * @param {string} report.profile - Perfil do usuário ('padrao', 'idoso' ou 'pcd')
   * @param {string} report.type - Tipo de barreira ('escada', 'calcada_ruim', 'alagamento', 'obstaculo', 'iluminacao_ruim', 'seguranca', 'sinalizacao_ruim', 'outro')
   * @param {number} report.severity - Severidade (1-5)
   * @param {string} report.description - Descrição da barreira (opcional)
   * @param {number} report.lat - Latitude (opcional)
   * @param {number} report.lon - Longitude (opcional)
   * @param {string} report.app_version - Versão do app (opcional)
   * @param {string} report.platform - Plataforma ('web', 'android', 'ios') (opcional)
   */
  async reportBarrier(report) {
    try {
      const res = await axios.post(`${API_BASE}/barriers/report`, report);
      return res.data;
    } catch (error) {
      console.error('Erro ao reportar barreira:', error);
      if (error.response && error.response.data && error.response.data.detail) {
        const detail = error.response.data.detail;
        const msg =
          typeof detail === 'string'
            ? detail
            : detail.message || 'Erro ao reportar barreira';
        throw new Error(msg);
      }
      throw error;
    }
  },

  // ========== API OLHO VIVO (Tempo Real) ==========

  /**
   * Busca linhas de ônibus
   * @param {string} termos - Termo de busca (número ou nome da linha)
   */
  async buscarLinhasOlhoVivo(termos) {
    try {
      const res = await axios.get(`${API_BASE}/olho-vivo/linhas/buscar`, {
        params: { termos }
      });
      return res.data.linhas;
    } catch (error) {
      console.error('Erro ao buscar linhas Olho Vivo:', error);
      throw error;
    }
  },

  /**
   * Busca paradas de ônibus
   * @param {string} termos - Termo de busca (nome ou código da parada)
   */
  async buscarParadasOlhoVivo(termos) {
    try {
      const res = await axios.get(`${API_BASE}/olho-vivo/paradas/buscar`, {
        params: { termos }
      });
      return res.data.paradas;
    } catch (error) {
      console.error('Erro ao buscar paradas Olho Vivo:', error);
      throw error;
    }
  },

  /**
   * Obtém posição dos veículos em tempo real
   * @param {number} codigoLinha - Código da linha (opcional)
   */
  async obterPosicaoVeiculos(codigoLinha = null) {
    try {
      const params = codigoLinha ? { codigo_linha: codigoLinha } : {};
      const res = await axios.get(`${API_BASE}/olho-vivo/posicao`, { params });
      return res.data;
    } catch (error) {
      console.error('Erro ao obter posição dos veículos:', error);
      // Retornar objeto vazio em caso de erro para não quebrar o componente
      if (error.response) {
        console.error('Status:', error.response.status, 'Dados:', error.response.data);
      }
      return { vs: [], l: [] }; // Retornar estrutura vazia compatível
    }
  },

  /**
   * Obtém previsão de chegada
   * @param {number} codigoParada - Código da parada
   * @param {number} codigoLinha - Código da linha (opcional)
   */
  async obterPrevisaoChegada(codigoParada, codigoLinha = null) {
    try {
      const params = { codigo_parada: codigoParada };
      if (codigoLinha) {
        params.codigo_linha = codigoLinha;
      }
      const res = await axios.get(`${API_BASE}/olho-vivo/previsao`, { params });
      return res.data;
    } catch (error) {
      console.error('Erro ao obter previsão de chegada:', error);
      throw error;
    }
  },

  /**
   * Obtém previsão de chegada para todas as linhas de uma parada
   * @param {number} codigoParada - Código da parada
   */
  async obterPrevisaoPorParada(codigoParada) {
    try {
      const res = await axios.get(`${API_BASE}/olho-vivo/previsao/parada/${codigoParada}`);
      return res.data;
    } catch (error) {
      console.error('Erro ao obter previsão por parada:', error);
      throw error;
    }
  },

  /**
   * Busca paradas atendidas por uma linha
   * @param {number} codigoLinha - Código da linha
   */
  async buscarParadasPorLinha(codigoLinha) {
    try {
      const res = await axios.get(`${API_BASE}/olho-vivo/paradas/por-linha/${codigoLinha}`);
      return res.data.paradas;
    } catch (error) {
      console.error('Erro ao buscar paradas por linha:', error);
      throw error;
    }
  },

  /**
   * Busca notificações do sistema
   * @returns {Promise<Object>} Lista de notificações
   */
  async getNotifications() {
    try {
      const res = await axios.get(`${API_BASE}/notifications`);
      return res.data;
    } catch (error) {
      console.error('Erro ao buscar notificações:', error);
      return { notifications: [], unread_count: 0 };
    }
  }
};

// Verificar conexão ao carregar (com retry)
const checkApiHealth = async (retries = 3, delay = 2000) => {
  for (let i = 0; i < retries; i++) {
    try {
      const health = await api.getHealth();
      console.log('✅ API conectada:', health);
      return;
    } catch (error) {
      if (i < retries - 1) {
        console.log(`⏳ Tentativa ${i + 1}/${retries} - Aguardando servidor iniciar...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      } else {
        console.warn('⚠️ API não disponível após', retries, 'tentativas. Certifique-se de que o backend está rodando na porta 8080');
      }
    }
  }
};

// Aguardar um pouco antes de verificar (dar tempo para o servidor iniciar)
setTimeout(() => {
  checkApiHealth();
}, 1000);

export default api;

