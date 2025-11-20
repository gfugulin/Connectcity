import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getFavorites, deleteFavorite, formatTime, getFavoriteIcon } from '../utils';
import BottomNav from '../components/BottomNav';

export default function Favorites() {
  const navigate = useNavigate();
  const [favorites, setFavorites] = useState([]);

  useEffect(() => {
    setFavorites(getFavorites());
  }, []);

  const handleDelete = (id) => {
    if (window.confirm('Deseja remover este favorito?')) {
      deleteFavorite(id);
      setFavorites(getFavorites());
    }
  };

  const handleViewRoute = (favorite) => {
    if (favorite.route) {
      sessionStorage.setItem('selectedRoute', JSON.stringify(favorite.route));
      navigate(`/route/${favorite.route.id}`);
    }
  };

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
          <h1 className="flex-1 text-center text-lg font-bold text-[var(--c-text-primary)]">
            Favoritos
          </h1>
          <div className="w-8"></div>
        </header>
        <main className="p-4">
          {favorites.length === 0 ? (
            <div className="p-4 text-center">
              <span className="material-symbols-outlined text-6xl text-gray-300 mb-4 block">
                bookmark
              </span>
              <p className="text-gray-600 mb-4">Nenhum favorito salvo</p>
              <button
                onClick={() => navigate('/')}
                className="text-blue-500 underline"
              >
                Buscar rotas
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {favorites.map((fav) => {
                const route = fav.route || {};
                const time = formatTime(route.tempo_total_min || 0);
                const icon = getFavoriteIcon(fav.name);

                return (
                  <div
                    key={fav.id}
                    onClick={() => handleViewRoute(fav)}
                    className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer"
                  >
                    <div className="flex items-center gap-4 p-4">
                      <div className="flex items-center justify-center rounded-full bg-blue-100 text-[var(--primary-color)] shrink-0 size-12">
                        <span className="material-symbols-outlined text-2xl">{icon}</span>
                      </div>
                      <div className="flex-grow">
                        <div className="flex justify-between items-start">
                          <h2 className="text-gray-800 text-lg font-semibold leading-tight">
                            {fav.name}
                          </h2>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(fav.id);
                            }}
                            className="text-gray-400 hover:text-gray-600"
                          >
                            <span className="material-symbols-outlined">delete</span>
                          </button>
                        </div>
                        <p className="text-gray-500 text-sm font-normal mt-1">
                          {fav.from || route.from || 'Origem'} → {fav.to || route.to || 'Destino'}
                        </p>
                        <div className="flex items-center gap-4 mt-3 text-gray-600">
                          <div className="flex items-center gap-1">
                            <span className="material-symbols-outlined text-lg">schedule</span>
                            <span className="text-sm font-medium">{time}</span>
                          </div>
                          {route.transferencias && (
                            <div className="flex items-center gap-1">
                              <span className="material-symbols-outlined text-lg">swap_horiz</span>
                              <span className="text-sm">
                                {route.transferencias} transferência{route.transferencias !== 1 ? 's' : ''}
                              </span>
                            </div>
                          )}
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
      <footer className="sticky bottom-0 border-t border-[var(--c-border)] bg-[var(--c-background)] px-4 pb-3 pt-2">
        <BottomNav />
      </footer>
    </div>
  );
}

