import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { getErrorMessage, getUserPreferences } from '../utils';
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
  const [showNotifications, setShowNotifications] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showMenu, setShowMenu] = useState(false);

  // Carregar perfil salvo nas preferências
  useEffect(() => {
    const prefs = getUserPreferences();
    if (prefs.profile) {
      setProfile(prefs.profile);
    }
  }, []);

  // Carregar notificações
  useEffect(() => {
    const loadNotifications = async () => {
      try {
        const data = await api.getNotifications();
        setNotifications(data.notifications || []);
        setUnreadCount(data.unread_count || 0);
      } catch (error) {
        console.error('Erro ao carregar notificações:', error);
      }
    };
    
    loadNotifications();
    // Atualizar notificações a cada 5 minutos
    const interval = setInterval(loadNotifications, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

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
        <header className="relative z-30 flex items-center justify-between p-4 bg-white/80 backdrop-blur-sm">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="relative"
          >
            <span className="material-symbols-outlined text-gray-800 text-3xl">menu</span>
            {/* Menu dropdown */}
            {showMenu && (
              <>
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setShowMenu(false)}
                />
                <div className="absolute left-0 top-12 z-50 bg-white rounded-lg shadow-lg border border-gray-200 min-w-[200px]">
                  <button
                    onClick={() => {
                      navigate('/profile');
                      setShowMenu(false);
                    }}
                    className="w-full text-left px-4 py-3 text-sm text-gray-900 hover:bg-gray-50 rounded-lg flex items-center gap-2"
                  >
                    <span className="material-symbols-outlined">settings</span>
                    Configurações
                  </button>
                  <button
                    onClick={() => {
                      navigate('/favorites');
                      setShowMenu(false);
                    }}
                    className="w-full text-left px-4 py-3 text-sm text-gray-900 hover:bg-gray-50 rounded-lg flex items-center gap-2"
                  >
                    <span className="material-symbols-outlined">bookmark</span>
                    Favoritos
                  </button>
                  <button
                    onClick={() => {
                      navigate('/faq');
                      setShowMenu(false);
                    }}
                    className="w-full text-left px-4 py-3 text-sm text-gray-900 hover:bg-gray-50 rounded-lg flex items-center gap-2"
                  >
                    <span className="material-symbols-outlined">help</span>
                    Ajuda
                  </button>
                </div>
              </>
            )}
          </button>
          <h1 className="text-xl font-bold text-gray-900">CONNECITY</h1>
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative"
            >
              <span className="material-symbols-outlined text-gray-800 text-3xl">notifications</span>
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>
            
            {/* Dropdown de notificações - FORA do botão para evitar nesting */}
            {showNotifications && (
              <>
                {/* Overlay para fechar */}
                <div
                  className="fixed inset-0 z-[90] bg-black/20"
                  onClick={() => setShowNotifications(false)}
                />
                {/* Popup de notificações */}
                <div 
                  className="fixed right-4 top-20 z-[100] bg-white rounded-xl shadow-2xl border border-gray-200 w-[calc(100%-2rem)] max-w-sm max-h-[50vh] overflow-hidden flex flex-col"
                  onClick={(e) => e.stopPropagation()}
                  style={{ maxHeight: '400px' }}
                >
                  {/* Header do popup */}
                  <div className="sticky top-0 bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between z-10">
                    <h3 className="text-lg font-bold text-gray-900">Notificações</h3>
                    <button
                      onClick={() => setShowNotifications(false)}
                      className="text-gray-400 hover:text-gray-600 p-1"
                    >
                      <span className="material-symbols-outlined text-xl">close</span>
                    </button>
                  </div>
                  
                  {/* Lista de notificações */}
                  <div className="overflow-y-auto flex-1">
                    {notifications.length === 0 ? (
                      <div className="p-8 text-center text-gray-500 text-sm">
                        <span className="material-symbols-outlined text-4xl text-gray-300 mb-2 block">
                          notifications_off
                        </span>
                        <p>Nenhuma notificação</p>
                      </div>
                    ) : (
                      <div className="divide-y divide-gray-200">
                        {notifications.map((notif) => {
                          const getIcon = () => {
                            switch (notif.type) {
                              case 'warning': return 'warning';
                              case 'alert': return 'error';
                              case 'tip': return 'lightbulb';
                              case 'maintenance': return 'build';
                              default: return 'info';
                            }
                          };
                          
                          const getColor = () => {
                            switch (notif.type) {
                              case 'warning': return 'text-yellow-600 bg-yellow-50';
                              case 'alert': return 'text-red-600 bg-red-50';
                              case 'tip': return 'text-blue-600 bg-blue-50';
                              case 'maintenance': return 'text-orange-600 bg-orange-50';
                              default: return 'text-gray-600 bg-gray-50';
                            }
                          };
                          
                          return (
                            <div
                              key={notif.id}
                              className={`p-4 hover:bg-gray-50 transition-colors ${
                                notif.priority >= 3 ? 'bg-blue-50/50' : ''
                              }`}
                            >
                              <div className="flex items-start gap-3">
                                <div className={`flex items-center justify-center w-10 h-10 rounded-full shrink-0 ${getColor()}`}>
                                  <span className="material-symbols-outlined text-xl">
                                    {getIcon()}
                                  </span>
                                </div>
                                <div className="flex-1 min-w-0">
                                  <h4 className="text-sm font-semibold text-gray-900 mb-1">
                                    {notif.title}
                                  </h4>
                                  <p className="text-xs text-gray-600 leading-relaxed">
                                    {notif.message}
                                  </p>
                                  {notif.action_url && (
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        if (notif.action_url.startsWith('/')) {
                                          navigate(notif.action_url);
                                        } else {
                                          window.open(notif.action_url, '_blank');
                                        }
                                        setShowNotifications(false);
                                      }}
                                      className="mt-2 text-xs text-blue-600 hover:text-blue-700 font-medium"
                                    >
                                      {notif.action_label || 'Ver mais'}
                                    </button>
                                  )}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
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

