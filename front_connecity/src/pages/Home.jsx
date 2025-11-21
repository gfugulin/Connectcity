import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { getErrorMessage } from '../utils';
import BottomNav from '../components/BottomNav';
import Map from '../components/Map';

export default function Home() {
  const navigate = useNavigate();
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [profile, setProfile] = useState('padrao');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [suggestions, setSuggestions] = useState({ from: [], to: [] });
  const [showSuggestions, setShowSuggestions] = useState({ from: false, to: false });
  const [fromNode, setFromNode] = useState(null);
  const [toNode, setToNode] = useState(null);
  const [showRealtime, setShowRealtime] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    
    // Validar que usuário selecionou origem e destino da lista
    // (como Google Maps: precisa selecionar da lista, não apenas digitar)
    if (!fromNode || !toNode) {
      if (!fromNode && !toNode) {
        setError('Por favor, selecione origem e destino da lista de sugestões');
      } else if (!fromNode) {
        setError('Por favor, selecione a origem da lista de sugestões');
      } else {
        setError('Por favor, selecione o destino da lista de sugestões');
      }
      return;
    }
    
    // Usar IDs dos nós selecionados para buscar rotas
    // (o input mostra o nome, mas a busca usa o ID)
    const fromId = fromNode.id;
    const toId = toNode.id;

    setLoading(true);
    setError('');

    try {
      const routes = await api.searchRoutes(fromId, toId, profile);
      
      if (routes.length === 0) {
        setError('Nenhuma rota encontrada entre os pontos selecionados');
        return;
      }

      // Salvar rotas no sessionStorage
      sessionStorage.setItem('routes', JSON.stringify(routes));
      sessionStorage.setItem('routeParams', JSON.stringify({ 
        from: fromNode?.name || from, 
        to: toNode?.name || to, 
        fromId, 
        toId, 
        profile 
      }));
      
      // Navegar para página de resultados
      navigate('/routes');
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = async (field, value) => {
    // Atualizar valor do input (mostra o que o usuário digitou)
    if (field === 'from') {
      setFrom(value);
      // Se usuário está digitando, limpar nó selecionado (força nova seleção)
      if (value !== fromNode?.name) {
        setFromNode(null);
      }
    } else {
      setTo(value);
      // Se usuário está digitando, limpar nó selecionado (força nova seleção)
      if (value !== toNode?.name) {
        setToNode(null);
      }
    }

    // Autocomplete
    if (value.length >= 2) {
      try {
        const nodes = await api.searchNodes(value);
        setSuggestions(prev => ({
          ...prev,
          [field]: nodes.slice(0, 5) // Limitar a 5 sugestões
        }));
        setShowSuggestions(prev => ({
          ...prev,
          [field]: true
        }));
      } catch (err) {
        // Ignorar erros silenciosamente
      }
    } else {
      setShowSuggestions(prev => ({
        ...prev,
        [field]: false
      }));
    }
  };

  const selectSuggestion = (field, node) => {
    // Quando seleciona uma sugestão, mostra o nome completo no input
    // e salva o nó completo (com ID) para usar na busca
    const displayName = node.name || node.id;
    
    if (field === 'from') {
      setFrom(displayName); // Input mostra o nome do lugar selecionado
      setFromNode(node);    // Salva nó completo (com ID) para busca
    } else {
      setTo(displayName);   // Input mostra o nome do lugar selecionado
      setToNode(node);      // Salva nó completo (com ID) para busca
    }
    
    // Fechar sugestões
    setShowSuggestions(prev => ({
      ...prev,
      [field]: false
    }));
  };

  // Buscar informações dos nós quando IDs mudarem
  useEffect(() => {
    const fetchNodeInfo = async (nodeId, setNode) => {
      if (!nodeId) {
        setNode(null);
        return;
      }
      
      try {
        const nodes = await api.searchNodes(nodeId);
        const node = nodes.find(n => n.id === nodeId);
        if (node) {
          setNode(node);
        }
      } catch (err) {
        // Ignorar erros
      }
    };

    if (from && from !== fromNode?.id) {
      fetchNodeInfo(from, setFromNode);
    }
    if (to && to !== toNode?.id) {
      fetchNodeInfo(to, setToNode);
    }
  }, [from, to]);

  return (
    <div className="relative min-h-screen w-full">
              {/* Mapa */}
              <div className="absolute inset-0 z-0">
                <Map 
                  fromNode={fromNode} 
                  toNode={toNode}
                  showRealtime={showRealtime}
                />
              </div>
      <div className="absolute inset-0 z-10 bg-black/10" />
      
      <div className="relative z-20 flex flex-col h-screen">
        {/* Header */}
        <header className="flex items-center justify-between p-4 bg-white/80 backdrop-blur-sm">
          <span className="material-symbols-outlined text-gray-800 text-3xl">menu</span>
          <h1 className="text-xl font-bold text-gray-900">CONNECITY</h1>
          <span className="material-symbols-outlined text-gray-800 text-3xl">notifications</span>
        </header>

        <div className="flex-grow" />

                {/* Form */}
                <div className="bg-white rounded-t-3xl p-4 shadow-2xl">
                  {/* Toggle Tempo Real */}
                  {fromNode && toNode && (
                    <div className="mb-4 flex items-center justify-between rounded-lg bg-blue-50 p-3">
                      <div className="flex items-center gap-2">
                        <span className="material-symbols-outlined text-blue-600">schedule</span>
                        <span className="text-sm font-medium text-blue-900">
                          Mostrar ônibus em tempo real
                        </span>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={showRealtime}
                          onChange={(e) => setShowRealtime(e.target.checked)}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                  )}
          <div className="w-12 h-1.5 bg-gray-300 rounded-full mx-auto mb-4" />
          
          <form onSubmit={handleSearch} className="space-y-3">
            {/* Origem */}
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                trip_origin
              </span>
              <input
                type="text"
                value={from}
                onChange={(e) => handleInputChange('from', e.target.value)}
                onFocus={() => setShowSuggestions(prev => ({ ...prev, from: suggestions.from.length > 0 }))}
                onBlur={() => setTimeout(() => setShowSuggestions(prev => ({ ...prev, from: false })), 200)}
                className="form-input w-full pl-10 pr-4 py-3 border-gray-300 rounded-xl bg-gray-100 focus:ring-primary-500 focus:border-primary-500 text-base"
                placeholder="Digite origem (ex: Cidade Jardim)"
              />
              {showSuggestions.from && suggestions.from.length > 0 && (
                <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                  {suggestions.from.map((node) => (
                    <button
                      key={node.id}
                      type="button"
                      onClick={() => selectSuggestion('from', node)}
                      className="w-full text-left px-4 py-2 hover:bg-gray-100 flex items-center gap-2"
                    >
                      <span className="material-symbols-outlined text-gray-400">place</span>
                      <div>
                        <div className="font-medium">{node.name}</div>
                        <div className="text-sm text-gray-500">{node.id}</div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Destino */}
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                location_on
              </span>
              <input
                type="text"
                value={to}
                onChange={(e) => handleInputChange('to', e.target.value)}
                onFocus={() => setShowSuggestions(prev => ({ ...prev, to: suggestions.to.length > 0 }))}
                onBlur={() => setTimeout(() => setShowSuggestions(prev => ({ ...prev, to: false })), 200)}
                className="form-input w-full pl-10 pr-4 py-3 border-gray-300 rounded-xl bg-gray-100 focus:ring-primary-500 focus:border-primary-500 text-base"
                placeholder="Digite destino (ex: Cidade Universitária)"
              />
              {showSuggestions.to && suggestions.to.length > 0 && (
                <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                  {suggestions.to.map((node) => (
                    <button
                      key={node.id}
                      type="button"
                      onClick={() => selectSuggestion('to', node)}
                      className="w-full text-left px-4 py-2 hover:bg-gray-100 flex items-center gap-2"
                    >
                      <span className="material-symbols-outlined text-gray-400">place</span>
                      <div>
                        <div className="font-medium">{node.name}</div>
                        <div className="text-sm text-gray-500">{node.id}</div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Perfil de Mobilidade */}
            <div className="mt-5">
              <h3 className="text-gray-800 text-base font-semibold mb-2">Perfil de Mobilidade</h3>
              <div className="flex space-x-3">
                {[
                  { value: 'padrao', icon: 'directions_walk', label: 'Padrão' },
                  { value: 'idoso', icon: 'elderly', label: 'Idoso' },
                  { value: 'pcd', icon: 'accessible', label: 'PcD' }
                ].map((p) => (
                  <label key={p.value} className="flex-1 cursor-pointer">
                    <input
                      type="radio"
                      name="mobility-profile"
                      value={p.value}
                      checked={profile === p.value}
                      onChange={(e) => setProfile(e.target.value)}
                      className="sr-only"
                    />
                    <div
                      className={`flex flex-col items-center justify-center p-3 rounded-xl border-2 ${
                        profile === p.value
                          ? 'border-primary-500 bg-primary-50 text-primary-700 font-semibold'
                          : 'border-gray-300 bg-gray-100 text-gray-600'
                      }`}
                    >
                      <span className="material-symbols-outlined mb-1">{p.icon}</span>
                      <span className="text-xs">{p.label}</span>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Erro */}
            {error && (
              <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}

            {/* Botão Buscar */}
            <div className="mt-5">
              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 rounded-xl h-12 px-6 bg-primary-500 text-white text-base font-bold shadow-lg shadow-primary-500/30 hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Buscando...' : 'Buscar Rota'}
                <span className="material-symbols-outlined">arrow_forward</span>
              </button>
            </div>
          </form>

          {/* Footer Navigation */}
          <div className="border-t border-gray-200 mt-4 pt-2 -mx-4">
            <BottomNav />
          </div>
        </div>
      </div>
    </div>
  );
}

