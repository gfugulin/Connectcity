// Cliente HTTP para comunicação com a API
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
   * @param {string} profile - Perfil ('padrao' ou 'pcd')
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
      throw error;
    }
  },

  /**
   * Calcula melhor rota
   * @param {string} from - ID do nó de origem
   * @param {string} to - ID do nó de destino
   * @param {string} profile - Perfil ('padrao' ou 'pcd')
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
   * @param {string} profile - Perfil ('padrao' ou 'pcd')
   */
  async getRouteDetails({ from, to, path, profile = 'padrao' }) {
    try {
      const payload = {
        perfil: profile,
        chuva: false
      };
      
      if (path) {
        payload.path = path;
      } else {
        payload.from = from;
        payload.to = to;
      }
      
      const res = await axios.post(`${API_BASE}/route/details`, payload);
      return res.data;
    } catch (error) {
      console.error('Erro ao obter detalhes da rota:', error);
      throw error;
    }
  }
};

// Verificar conexão ao carregar
window.addEventListener('DOMContentLoaded', async () => {
  try {
    const health = await api.getHealth();
    console.log('✅ API conectada:', health);
  } catch (error) {
    console.warn('⚠️ API não disponível. Certifique-se de que o backend está rodando na porta 8080');
  }
});

