import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getFavorites, deleteFavorite, formatTime, getFavoriteIcon } from '../utils';
import BottomNav from '../components/BottomNav';

export default function Favorites() {
  const navigate = useNavigate();
  const [favorites, setFavorites] = useState([]);
  const [showMenuId, setShowMenuId] = useState(null);

  useEffect(() => {
    setFavorites(getFavorites());
  }, []);

  const handleDelete = (id) => {
    if (window.confirm('Deseja remover este favorito?')) {
      deleteFavorite(id);
      setFavorites(getFavorites());
      setShowMenuId(null);
    }
  };

  const handleViewRoute = (favorite) => {
    if (favorite.route) {
      sessionStorage.setItem('selectedRoute', JSON.stringify(favorite.route));
      // Restaurar parâmetros da rota se disponíveis
      if (favorite.fromId && favorite.toId) {
        sessionStorage.setItem('routeParams', JSON.stringify({
          fromId: favorite.fromId,
          toId: favorite.toId,
          profile: favorite.profile || 'padrao'
        }));
      }
      navigate(`/route/${favorite.route.id}`);
    }
  };

  const getTransportIcons = (route) => {
    const modes = route.modes || [];
    const icons = [];
    
    modes.forEach(mode => {
      const modeLower = mode?.toLowerCase();
      if (modeLower === 'onibus' || modeLower === 'bus') {
        icons.push({ icon: 'directions_bus', label: 'Ônibus' });
      } else if (modeLower === 'metro' || modeLower === 'subway') {
        icons.push({ icon: 'directions_subway', label: 'Metrô' });
      } else if (modeLower === 'trem' || modeLower === 'train') {
        icons.push({ icon: 'train', label: 'Trem' });
      } else if (modeLower === 'pe' || modeLower === 'walk') {
        icons.push({ icon: 'directions_walk', label: 'A pé' });
      }
    });
    
    // Se não houver modos, verificar se há caminhada na rota
    if (icons.length === 0 && route.path && route.path.length > 0) {
      icons.push({ icon: 'directions_walk', label: 'A pé' });
    }
    
    return icons;
  };

  return (
    <div className="relative flex min-h-screen w-full flex-col justify-between overflow-x-hidden bg-white">
      <div className="flex-1">
        {/* Header */}
        <header className="sticky top-0 z-10 bg-white border-b border-gray-200">
          <div className="flex items-center p-4">
            <button
              onClick={() => navigate(-1)}
              className="text-[var(--text-primary)]"
            >
              <span className="material-symbols-outlined">arrow_back_ios_new</span>
            </button>
            <h1 className="flex-1 text-center text-lg font-bold text-[var(--text-primary)]">
              Favoritos
            </h1>
            <div className="w-8"></div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto pb-24 px-4 py-4">
          {favorites.length === 0 ? (
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
              <span className="material-symbols-outlined text-6xl text-gray-300 mb-4">
                bookmark
              </span>
              <p className="text-gray-600 mb-4 text-lg">Nenhum favorito salvo</p>
              <button
                onClick={() => navigate('/')}
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                Buscar rotas
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {favorites.map((fav) => {
                const route = fav.route || {};
                const time = formatTime(route.tempo_total_min || 0);
                const icon = fav.icon || getFavoriteIcon(fav.name);
                const transportIcons = getTransportIcons(route);
                
                // Buscar nomes da origem e destino
                // Prioridade: fav.from/fav.to > route.from/route.to > route.from_name/route.to_name > steps
                let fromName = fav.from || route.from || route.from_name || '';
                let toName = fav.to || route.to || route.to_name || '';
                
                // Se não encontrou nos dados salvos, tentar buscar nos steps do route
                if ((!fromName || !toName) && route.steps && Array.isArray(route.steps) && route.steps.length > 0) {
                  if (!fromName) {
                    fromName = route.steps[0]?.from_name || route.steps[0]?.from || '';
                  }
                  if (!toName) {
                    const lastStep = route.steps[route.steps.length - 1];
                    toName = lastStep?.to_name || lastStep?.to || '';
                  }
                }
                
                // Fallback final - só usar se realmente não encontrou nada
                if (!fromName || fromName === '') fromName = 'Origem';
                if (!toName || toName === '') toName = 'Destino';

                return (
                  <div
                    key={fav.id}
                    className="bg-gray-50 rounded-lg shadow-sm hover:shadow-md transition-shadow relative"
                  >
                    <div
                      className="flex items-center gap-4 p-4 cursor-pointer"
                      onClick={() => handleViewRoute(fav)}
                    >
                      {/* Ícone circular */}
                      <div className="flex items-center justify-center rounded-full bg-blue-100 shrink-0 size-12">
                        <span className="material-symbols-outlined text-2xl text-blue-600">
                          {icon}
                        </span>
                      </div>

                      {/* Conteúdo */}
                      <div className="flex-grow min-w-0">
                        <div className="flex items-start justify-between gap-2 mb-1">
                          <h2 className="text-base font-bold text-gray-900 leading-tight">
                            {fav.name}
                          </h2>
                          {/* Menu de três pontos */}
                          <div className="relative shrink-0">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setShowMenuId(showMenuId === fav.id ? null : fav.id);
                              }}
                              className="text-gray-400 hover:text-gray-600 p-1"
                            >
                              <span className="material-symbols-outlined text-xl">
                                more_vert
                              </span>
                            </button>
                            
                            {/* Menu dropdown */}
                            {showMenuId === fav.id && (
                              <>
                                <div
                                  className="fixed inset-0 z-10"
                                  onClick={() => setShowMenuId(null)}
                                />
                                <div className="absolute right-0 top-8 z-20 bg-white rounded-lg shadow-lg border border-gray-200 min-w-[120px]">
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleDelete(fav.id);
                                    }}
                                    className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-50 rounded-lg"
                                  >
                                    <span className="material-symbols-outlined text-lg align-middle mr-2">
                                      delete
                                    </span>
                                    Remover
                                  </button>
                                </div>
                              </>
                            )}
                          </div>
                        </div>

                        {/* Endereço */}
                        <p className="text-sm text-gray-600 mb-3">
                          {fromName} → {toName}
                        </p>

                        {/* Ícones de transporte e tempo */}
                        <div className="flex items-center gap-4">
                          {/* Ícones de transporte */}
                          {transportIcons.length > 0 && (
                            <div className="flex items-center gap-2">
                              {transportIcons.map((transport, idx) => (
                                <span
                                  key={idx}
                                  className="material-symbols-outlined text-lg text-gray-600"
                                  title={transport.label}
                                >
                                  {transport.icon}
                                </span>
                              ))}
                            </div>
                          )}

                          {/* Tempo */}
                          <div className="flex items-center gap-1 text-gray-600">
                            <span className="material-symbols-outlined text-lg">schedule</span>
                            <span className="text-sm font-medium">{time}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </main>
      </div>

      {/* Footer com BottomNav */}
      <footer className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200">
        <BottomNav />
        <div className="h-safe-area-bottom bg-white"></div>
      </footer>
    </div>
  );
}

