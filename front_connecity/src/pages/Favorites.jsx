import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import BottomNav from '../components/BottomNav';

export default function Favorites() {
  const navigate = useNavigate();
  
  // Dados mockados de favoritos
  const [favorites] = useState([
    {
      id: 1,
      name: 'Casa',
      icon: 'home',
      from: 'Av. Paulista, 1000',
      to: 'R. Lavinia Fenton, 53',
      transport: ['onibus', 'trem'], // Ícones de ônibus e trem
      duration: '1h 15min'
    },
    {
      id: 2,
      name: 'Trabalho',
      icon: 'work',
      from: 'R. Lavinia Fenton, 53',
      to: 'Av. Paulista, 1000',
      transport: ['onibus', 'trem'], // Ícone de caminhada
      duration: '45min'
    },
    {
      id: 3,
      name: 'Faculdade',
      icon: 'school',
      from: 'R. Lavinia Fenton, 53',
      to: 'Universidade Presbiteriana Mackenzie',
      transport: ['onibus'], // Ícone de ônibus
      duration: '1h 30min'
    }
  ]);

  const [showMenu, setShowMenu] = useState(null);

  const toggleMenu = (id) => {
    setShowMenu(showMenu === id ? null : id);
  };

  // Fechar menu ao clicar fora
  useEffect(() => {
    const handleClickOutside = () => {
      if (showMenu) {
        setShowMenu(null);
      }
    };

    if (showMenu) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [showMenu]);

  const getTransportIcon = (type) => {
    switch (type) {
      case 'onibus':
        return 'directions_bus';
      case 'trem':
        return 'train';
      case 'metro':
        return 'subway';
      case 'caminhada':
        return 'directions_walk';
      default:
        return 'directions_bus';
    }
  };

  const handleCardClick = (favorite) => {
    // Navegar para detalhes da rota ou buscar rota
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-white pb-24">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="flex items-center p-4">
          <button 
            onClick={() => navigate(-1)}
            className="p-2 -ml-2 text-gray-600 hover:bg-gray-100 rounded-full"
          >
            <span className="material-symbols-outlined text-2xl">arrow_back</span>
          </button>
          <h1 className="flex-1 text-center text-lg font-semibold text-gray-900 -mr-10">
            Favoritos
          </h1>
        </div>
      </header>

      <main className="px-4 py-6">
        {favorites.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16">
            <span className="material-symbols-outlined text-6xl text-gray-300 mb-4">
              bookmark
            </span>
            <p className="text-gray-600 mb-4">Nenhum favorito salvo</p>
            <button
              onClick={() => navigate('/')}
              className="text-primary-600 font-medium"
            >
              Buscar rotas
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {favorites.map((favorite) => (
              <div
                key={favorite.id}
                className="bg-gray-50 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer relative"
                onClick={() => handleCardClick(favorite)}
              >
                <div className="flex items-start gap-4">
                  {/* Ícone circular */}
                  <div className="flex-shrink-0 w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
                    <span className="material-symbols-outlined text-blue-600 text-2xl">
                      {favorite.icon}
                    </span>
                  </div>

                  {/* Conteúdo */}
                  <div className="flex-1 min-w-0">
                    <h2 className="text-base font-bold text-gray-900 mb-1">
                      {favorite.name}
                    </h2>
                    <p className="text-sm text-gray-600 mb-3">
                      {favorite.from} → {favorite.to}
                    </p>

                    {/* Ícones de transporte e tempo */}
                    <div className="flex items-center gap-3">
                      {/* Ícones de transporte */}
                      <div className="flex items-center gap-2">
                        {favorite.transport.map((type, index) => (
                          <span
                            key={index}
                            className="material-symbols-outlined text-gray-600 text-lg"
                          >
                            {getTransportIcon(type)}
                          </span>
                        ))}
                      </div>

                      {/* Tempo */}
                      <div className="flex items-center gap-1">
                        <span className="material-symbols-outlined text-gray-600 text-lg">
                          schedule
                        </span>
                        <span className="text-sm text-gray-600 font-medium">
                          {favorite.duration}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Menu de três pontos */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleMenu(favorite.id);
                    }}
                    className="flex-shrink-0 p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-200"
                  >
                    <span className="material-symbols-outlined text-xl">
                      more_vert
                    </span>
                  </button>

                  {/* Menu dropdown */}
                  {showMenu === favorite.id && (
                    <div 
                      className="absolute right-4 top-16 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-20 min-w-[150px]"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCardClick(favorite);
                          setShowMenu(null);
                        }}
                        className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                      >
                        Ver rota
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          // handleDelete(favorite.id);
                          setShowMenu(null);
                        }}
                        className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-50"
                      >
                        Remover
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Bottom Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200">
        <BottomNav />
      </div>
    </div>
  );
}
