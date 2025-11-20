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
              const isRecommended = index === 0;
              const score = calculateRouteScore(route);
              const modes = route.modes || [];
              
              return (
                <div
                  key={route.id}
                  onClick={() => handleRouteClick(route)}
                  className="rounded-lg border border-[var(--c-border)] bg-[var(--c-surface)] p-4 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="mb-2 flex items-center gap-4">
                        <p className="text-xl font-bold text-[var(--c-text-primary)]">
                          {Math.round(route.tempo_total_min)} min
                        </p>
                        <div className="flex items-center gap-2 text-[var(--c-text-secondary)]">
                          {modes.length > 0 ? (
                            modes.map((mode, i) => (
                              <span key={i} className="material-symbols-outlined text-lg">
                                {getTransportIcon(mode)}
                              </span>
                            ))
                          ) : (
                            <>
                              <span className="material-symbols-outlined text-lg">directions_bus</span>
                              <span className="material-symbols-outlined text-lg">directions_subway</span>
                              <span className="material-symbols-outlined text-lg">directions_walk</span>
                            </>
                          )}
                        </div>
                      </div>
                      <p className="text-sm text-[var(--c-text-secondary)]">
                        {route.transferencias} transferência{route.transferencias !== 1 ? 's' : ''}
                      </p>
                    </div>
                    <div className="flex flex-col items-end">
                      {isRecommended && (
                        <p className="text-sm font-semibold text-[var(--c-primary)]">Recomendada</p>
                      )}
                      <p className="text-xs text-[var(--c-text-secondary)]">Pontuação: {score}</p>
                    </div>
                  </div>
                  <div className="mt-4 h-24 w-full rounded-md bg-gray-200 flex items-center justify-center">
                    <span className="text-gray-400 text-sm">Mapa da rota</span>
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

