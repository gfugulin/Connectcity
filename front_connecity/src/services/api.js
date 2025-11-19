import axios from 'axios';

const API_BASE = 'http://localhost:8080';

// Modo mock - ativar para usar dados mockados
const USE_MOCK_DATA = true; // Mude para false para usar API real

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
    // Dados mockados para apresentação
    if (USE_MOCK_DATA) {
      // Simular delay de rede
      await new Promise(resolve => setTimeout(resolve, 500));

      // Verificar se é a busca específica: R. Lavínia Fenton → Parque Ibirapuera
      const isLaviniaToIbirapuera = (
        (from === 'node1' || from?.toLowerCase().includes('lavinia') || from?.toLowerCase().includes('marajoara')) &&
        (to === 'node2' || to?.toLowerCase().includes('ibirapuera') || to?.toLowerCase().includes('parque'))
      );

      let mockRoutes;

      if (isLaviniaToIbirapuera) {
        // Rotas específicas: R. Lavínia Fenton → Parque Ibirapuera
        mockRoutes = [
          {
            id: 'route1',
            from: from,
            to: to,
            tempo_total_min: 124, // 2h 4min (conforme Google Maps)
            transferencias: 1,
            barreiras_evitas: ['escada', 'calcada_ruim'],
            modes: ['onibus', 'metro', 'pe'],
            path: ['node1', 'node5', 'node2'],
            score: 75,
            recommended: true,
            illustration: 'bus',
            via: 'Alameda dos Maracatins',
            distancia_km: 8.7
          },
          {
            id: 'route2',
            from: from,
            to: to,
            tempo_total_min: 125, // 2h 5min
            transferencias: 2,
            barreiras_evitas: ['escada'],
            modes: ['onibus', 'metro', 'pe'],
            path: ['node1', 'node7', 'node5', 'node2'],
            score: 65,
            recommended: false,
            illustration: 'bus',
            via: 'Alameda dos Nhambiquaras',
            distancia_km: 8.7
          },
          {
            id: 'route3',
            from: from,
            to: to,
            tempo_total_min: 126, // 2h 6min
            transferencias: 1,
            barreiras_evitas: [],
            modes: ['onibus', 'pe'],
            path: ['node1', 'node6', 'node2'],
            score: 60,
            recommended: false,
            illustration: 'walk',
            via: 'Av. Santo Amaro',
            distancia_km: 8.9
          }
        ];
      } else {
        // Rotas genéricas para outras buscas
        mockRoutes = [
          {
            id: 'route1',
            from: from,
            to: to,
            tempo_total_min: 45,
            transferencias: 1,
            barreiras_evitas: ['escada', 'calcada_ruim'],
            modes: ['trem', 'metro', 'pe'],
            path: ['node1', 'node4', 'node2'],
            score: 85,
            recommended: true,
            illustration: 'train'
          },
          {
            id: 'route2',
            from: from,
            to: to,
            tempo_total_min: 50,
            transferencias: 2,
            barreiras_evitas: ['escada'],
            modes: ['trem', 'metro', 'pe'],
            path: ['node1', 'node6', 'node4', 'node2'],
            score: 70,
            recommended: false,
            delay: {
              line: 'Linha 4 - Amarela',
              message: 'Atrasos de até 15 minutos devido a uma falha de sinalização.',
              minutes: 15
            },
            illustration: 'bus'
          },
          {
            id: 'route3',
            from: from,
            to: to,
            tempo_total_min: 55,
            transferencias: 1,
            barreiras_evitas: [],
            modes: ['onibus', 'pe'],
            path: ['node1', 'node5', 'node2'],
            score: 60,
            recommended: false,
            illustration: 'walk'
          }
        ];
      }

      return mockRoutes.slice(0, k);
    }

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
    // Dados mockados para autocomplete
    if (USE_MOCK_DATA) {
      const mockNodes = [
        { id: 'node1', name: 'R. Lavínia Fenton - Jardim Marajoara, São Paulo - SP', lat: -23.6230, lon: -46.7000, tipo: 'endereco' },
        { id: 'node2', name: 'Parque Ibirapuera', lat: -23.5880, lon: -46.6580, tipo: 'ponto_interesse' },
        { id: 'node3', name: 'Av. Paulista, 1000', lat: -23.5615, lon: -46.6565, tipo: 'endereco' },
        { id: 'node4', name: 'Universidade Presbiteriana Mackenzie', lat: -23.5489, lon: -46.6388, tipo: 'ponto_interesse' },
        { id: 'node5', name: 'Estação Sé', lat: -23.5503, lon: -46.6333, tipo: 'estacao' },
        { id: 'node6', name: 'Terminal Bandeira', lat: -23.5505, lon: -46.6333, tipo: 'terminal' },
        { id: 'node7', name: 'Metrô Tatuapé', lat: -23.5400, lon: -46.5760, tipo: 'estacao' },
        { id: 'node8', name: 'Shopping Center Norte', lat: -23.5100, lon: -46.6200, tipo: 'ponto_interesse' },
        { id: 'node9', name: 'Aeroporto de Congonhas', lat: -23.6260, lon: -46.6560, tipo: 'aeroporto' },
        { id: 'node10', name: 'Terminal Lapa', lat: -23.5200, lon: -46.7000, tipo: 'terminal' },
        { id: 'node11', name: 'R. Lavinia Fenton, 53', lat: -23.5505, lon: -46.6333, tipo: 'endereco' }
      ];

      const queryLower = query.toLowerCase();
      const filtered = mockNodes.filter(node => 
        node.name.toLowerCase().includes(queryLower) || 
        node.id.toLowerCase().includes(queryLower)
      );
      
      return filtered.slice(0, 5);
    }

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
    // Dados mockados para detalhes da rota
    if (USE_MOCK_DATA) {
      await new Promise(resolve => setTimeout(resolve, 300));

      // Verificar se é a rota específica: R. Lavínia Fenton → Parque Ibirapuera
      const isLaviniaToIbirapuera = (
        (path?.[0] === 'node1' || from === 'node1' || from?.toLowerCase().includes('lavinia')) &&
        (path?.[path.length - 1] === 'node2' || to === 'node2' || to?.toLowerCase().includes('ibirapuera'))
      );

      let mockSteps;
      let routeData;

      if (isLaviniaToIbirapuera) {
        // Detalhes específicos: R. Lavínia Fenton → Parque Ibirapuera
        mockSteps = [
          {
            from: path?.[0] || from,
            to: path?.[1] || 'node5',
            from_name: 'R. Lavínia Fenton - Jardim Marajoara',
            to_name: 'Estação Sé',
            mode: 'pe',
            tempo_min: 8,
            distancia_km: 0.6,
            instruction: 'Caminhe até o ponto na Av. Washington Luiz, 2354 (aproximadamente 8 minutos)'
          },
          {
            from: path?.[1] || 'node5',
            to: path?.[2] || 'node2',
            from_name: '5185 - Terminal Pq. Dom Pedro II',
            to_name: 'Av. Pedro Álvares Cabral, 1175 - Parada 1/Mac-Usp',
            mode: 'onibus',
            tempo_min: 18,
            distancia_km: 5.2,
            instruction: 'Pegue o onibus 5185 - Terminal Pq. Dom Pedro II até a Parada 1/Mac-Usp'
          },
          {
            from: path?.[2] || 'node2',
            to: path?.[2] || to,
            from_name: 'Av. Pedro Álvares Cabral, 1175 - Parada 1/Mac-Usp',
            to_name: 'Parque Ibirapuera',
            mode: 'pe',
            tempo_min: 15,
            distancia_km: 1.2,
            instruction: 'Pegue a passarela e Caminhe até o Parque Ibirapuera'
          }
        ];

        routeData = {
          total_time_min: 35, // 2h 4min
          total_distance_km: 9.7,
          transfers: 1,
          barriers_avoided: ['escada', 'calcada_ruim'],
          steps: mockSteps,
          from: path?.[0] || from,
          to: path?.[path.length - 1] || to,
          from_name: 'R. Lavínia Fenton - Jardim Marajoara, São Paulo - SP',
          to_name: 'Parque Ibirapuera',
          via: 'Alameda dos Maracatins'
        };
      } else {
        // Detalhes genéricos para outras rotas
        mockSteps = [
          {
            from: path?.[0] || from,
            to: path?.[1] || 'node4',
            from_name: 'R. Lavinia Fenton, 53',
            to_name: 'Estação Sé',
            mode: 'pe',
            tempo_min: 5,
            distancia_km: 0.5,
            instruction: 'Caminhe até a Estação Sé'
          },
          {
            from: path?.[1] || 'node4',
            to: path?.[2] || to,
            from_name: 'Estação Sé',
            to_name: 'Av. Paulista, 1000',
            mode: 'metro',
            tempo_min: 15,
            distancia_km: 3.2,
            instruction: 'Pegue o metrô na Linha 3 (Vermelha) até a Estação Trianon-Masp'
          },
          {
            from: path?.[2] || 'node2',
            to: path?.[2] || to,
            from_name: 'Estação Trianon-Masp',
            to_name: 'Av. Paulista, 1000',
            mode: 'pe',
            tempo_min: 3,
            distancia_km: 0.3,
            instruction: 'Caminhe até o destino'
          }
        ];

        routeData = {
          total_time_min: 45,
          total_distance_km: 4.0,
          transfers: path?.length ? path.length - 2 : 1,
          barriers_avoided: ['escada', 'calcada_ruim'],
          steps: mockSteps,
          from: path?.[0] || from,
          to: path?.[path.length - 1] || to,
          from_name: 'R. Lavinia Fenton, 53',
          to_name: 'Av. Paulista, 1000'
        };
      }

      return routeData;
    }

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
      throw error;
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
  }
};

// Verificar conexão ao carregar
api.getHealth().then(health => {
  console.log('✅ API conectada:', health);
}).catch(() => {
  console.warn('⚠️ API não disponível. Certifique-se de que o backend está rodando na porta 8080');
});

export default api;

