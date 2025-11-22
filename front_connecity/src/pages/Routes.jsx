import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { calculateRouteScore, getTransportIcon } from '../utils';
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
    <div className="relative flex min-h-screen w-full flex-col justify-between overflow-x-hidden bg-green-50">
      <div className="flex-1">
        <header className="sticky top-0 z-10 flex items-center justify-between border-b border-gray-200 bg-white p-4">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center justify-center text-gray-700"
          >
            <span className="material-symbols-outlined">arrow_back</span>
          </button>
          <h1 className="flex-1 text-center text-lg font-bold text-gray-900">Rotas</h1>
          <div className="w-8"></div>
        </header>
        <main className="p-4 pb-24">
          <div className="space-y-4">
            {routes.map((route, index) => {
              const isRecommended = index === 0;
              const score = calculateRouteScore(route);
              const modes = route.modes || [];
              
              // Se não tiver modos, tentar inferir do path (fallback)
              let displayModes = modes;
              if (displayModes.length === 0 && route.path && route.path.length > 0) {
                // Por padrão, mostrar ícones genéricos se não tiver modos
                displayModes = ['onibus', 'pe'];
              }
              
              return (
                <div
                  key={route.id || index}
                  className="rounded-xl border border-gray-200 bg-white p-4 shadow-md"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="mb-2 flex items-center gap-4">
                        <p className="text-2xl font-bold text-gray-900">
                          {Math.round(route.tempo_total_min || 0)} min
                        </p>
                        <div className="flex items-center gap-2 text-gray-600">
                          {displayModes.length > 0 ? (
                            displayModes.map((mode, i) => (
                              <span key={i} className="material-symbols-outlined text-xl">
                                {getTransportIcon(mode)}
                              </span>
                            ))
                          ) : (
                            <>
                              <span className="material-symbols-outlined text-xl">directions_bus</span>
                              <span className="material-symbols-outlined text-xl">train</span>
                              <span className="material-symbols-outlined text-xl">directions_walk</span>
                            </>
                          )}
                        </div>
                      </div>
                      <p className="text-sm text-gray-600">
                        {route.transferencias || 0} transferência{(route.transferencias || 0) !== 1 ? 's' : ''}
                      </p>
                    </div>
                    <div className="flex flex-col items-end">
                      {isRecommended && (
                        <p className="text-sm font-semibold text-blue-600 mb-1">Recomendada</p>
                      )}
                      <p className="text-xs text-gray-500">Pontuação: {score}</p>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRouteClick(route);
                    }}
                    className="w-full mt-4 rounded-lg bg-gray-100 hover:bg-gray-200 px-4 py-3 text-sm font-medium text-gray-700 transition-colors"
                  >
                    Mapa da rota
                  </button>
                </div>
              );
            })}
          </div>
        </main>
      </div>
      <footer className="fixed bottom-0 left-0 right-0 border-t border-gray-200 bg-white px-4 pb-safe-area-bottom pt-2">
        <BottomNav />
      </footer>
    </div>
  );
}


