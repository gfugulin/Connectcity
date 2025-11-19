import { Link, useLocation } from 'react-router-dom';

export default function BottomNav() {
  const location = useLocation();
  
  const isActive = (path) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <nav className="flex justify-around border-t border-gray-200 bg-white pb-2 pt-1">
      <Link
        to="/"
        className={`flex flex-col items-center gap-1 flex-1 py-2 ${
          isActive('/') ? 'text-primary-600' : 'text-gray-500 hover:text-primary-600'
        }`}
      >
        <span className="material-symbols-outlined text-3xl">map</span>
        <span className="text-xs font-medium">Rotas</span>
      </Link>
      <Link
        to="/favorites"
        className={`flex flex-col items-center gap-1 flex-1 py-2 ${
          isActive('/favorites') ? 'text-primary-600' : 'text-gray-500 hover:text-primary-600'
        }`}
      >
        <span className="material-symbols-outlined text-3xl">bookmark</span>
        <span className="text-xs font-medium">Favoritos</span>
      </Link>
      <Link
        to="/profile"
        className={`flex flex-col items-center gap-1 flex-1 py-2 ${
          isActive('/profile') ? 'text-primary-600' : 'text-gray-500 hover:text-primary-600'
        }`}
      >
        <span className="material-symbols-outlined text-3xl">person</span>
        <span className="text-xs font-medium">Perfil</span>
      </Link>
    </nav>
  );
}

