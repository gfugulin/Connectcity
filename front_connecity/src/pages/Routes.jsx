import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { calculateRouteScore, getTransportIcon, formatTime } from '../utils';
import BottomNav from '../components/BottomNav';

export default function Routes() {
  const navigate = useNavigate();
  const [routes, setRoutes] = useState([]);

  useEffect(() => {
    const storedRoutes = JSON.parse(sessionStorage.getItem('routes') || '[]');
    setRoutes(storedRoutes);
  }, []);

  const handleRouteClick = (route) => {
    sessionStorage.setItem('selectedRoute', JSON.stringify(route));
    navigate(`/route/${route.id}`);
  };

  if (routes.length === 0) {
    return (
      <div className="relative flex min-h-screen w-full flex-col justify-between overflow-x-hidden">
        <div className="flex-1">
          <header className="sticky top-0 z-10 flex items-center justify-between border-b border-[var(--c-border)] bg-[var(--c-background)] p-4">
            <button
              onClick={() => navigate(-1)}
              className="flex items-center justify-center text-[var(--c-text-primary)]"
            >
              <span className="material-symbols-outlined">arrow_back</span>
            </button>
            <h1 className="flex-1 text-center text-lg font-bold text-[var(--c-text-primary)]">Rotas</h1>
            <div className="w-8"></div>
          </header>
          <main className="p-4">
            <div className="p-4 text-center">
              <p className="text-gray-600">Nenhuma rota encontrada</p>
              <button
                onClick={() => navigate('/')}
                className="mt-4 px-4 py-2 bg-blue-500 text-white rounded"
              >
                Voltar
              </button>
            </div>
          </main>
        </div>
        <footer className="sticky bottom-0 border-t border-[var(--c-border)] bg-[var(--c-background)] px-4 pb-3 pt-2">
          <BottomNav />
        </footer>
      </div>
    );
  }

  return (
    <div className="relative flex min-h-screen w-full flex-col justify-between overflow-x-hidden">
      <div className="flex-1">
        <header className="sticky top-0 z-10 flex items-center justify-between border-b border-[var(--c-border)] bg-[var(--c-background)] p-4">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center justify-center text-[var(--c-text-primary)]"
          >
            <span className="material-symbols-outlined">arrow_back</span>
          </button>
          <h1 className="flex-1 text-center text-lg font-bold text-[var(--c-text-primary)]">Rotas</h1>
          <div className="w-8"></div>
        </header>
        <main className="p-4">
          <div className="space-y-4">
            {routes.map((route, index) => {
              const isRecommended = index === 0 || route.recommended;
              const score = route.score || calculateRouteScore(route);
              const modes = route.modes || [];
              
              return (
                <div
                  key={route.id}
                  onClick={() => handleRouteClick(route)}
                  className="bg-gray-50 rounded-xl p-4 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="mb-2 flex items-center gap-3">
                        <p className="text-2xl font-bold text-gray-900">
                          {formatTime(route.tempo_total_min)}
                        </p>
                        <div className="flex items-center gap-1.5">
                          {modes.length > 0 ? (
                            modes.map((mode, i) => (
                              <span key={i} className="material-symbols-outlined text-gray-700 text-lg">
                                {getTransportIcon(mode)}
                              </span>
                            ))
                          ) : (
                            <>
                              <span className="material-symbols-outlined text-lg text-gray-700">train</span>
                              <span className="material-symbols-outlined text-lg text-gray-700">directions_subway</span>
                              <span className="material-symbols-outlined text-lg text-gray-700">directions_walk</span>
                            </>
                          )}
                        </div>
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm text-gray-600">
                          {route.transferencias || 0} transferência{(route.transferencias || 0) !== 1 ? 's' : ''}
                        </p>
                        {route.via && (
                          <p className="text-xs text-gray-500">
                            via {route.via}
                          </p>
                        )}
                        {route.distancia_km && (
                          <p className="text-xs text-gray-500">
                            {route.distancia_km} km
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      {isRecommended && (
                        <p className="text-sm font-semibold text-primary-600">Recomendada</p>
                      )}
                      <p className="text-xs text-gray-500">Pontuação: {score}</p>
                    </div>
                  </div>

                  {/* Aviso de atraso */}
                  {route.delay && (
                    <div className="mb-3 p-3 bg-orange-50 border border-orange-200 rounded-lg">
                      <div className="flex items-start gap-2">
                        <span className="material-symbols-outlined text-orange-600 text-lg flex-shrink-0">warning</span>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-orange-900 mb-1">
                            Atraso na {route.delay.line}
                          </p>
                          <p className="text-xs text-orange-700">
                            {route.delay.message}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Ilustração da rota */}
                  <div className="mt-4 h-32 w-full rounded-lg bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center overflow-hidden">
                    {route.illustration === 'train' && (
                      <div className="text-6xl">🚆</div>
                    )}
                    {route.illustration === 'bus' && (
                      <div className="text-6xl">🚌</div>
                    )}
                    {route.illustration === 'walk' && (
                      <div className="text-6xl">🚶</div>
                    )}
                    {!route.illustration && (
                      <span className="text-gray-400 text-sm">Mapa da rota</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </main>
      </div>
      <footer className="sticky bottom-0 border-t border-[var(--c-border)] bg-[var(--c-background)] px-4 pb-3 pt-2">
        <BottomNav />
      </footer>
    </div>
  );
}

