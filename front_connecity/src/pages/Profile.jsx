import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getUserPreferences, saveUserPreferences } from '../utils';
import BottomNav from '../components/BottomNav';

export default function Profile() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState('padrao');
  const [walkPreference, setWalkPreference] = useState(50); // 0-100, 0 = menos caminhada, 100 = mais caminhada
  const [transferPreference, setTransferPreference] = useState(50); // 0-100, 0 = menos transferências, 100 = mais transferências
  const [largeFont, setLargeFont] = useState(false);
  const [highContrast, setHighContrast] = useState(false);

  useEffect(() => {
    // Carregar preferências salvas
    const prefs = getUserPreferences();
    if (prefs.profile) setProfile(prefs.profile);
    if (prefs.walkPreference !== undefined) setWalkPreference(prefs.walkPreference);
    if (prefs.transferPreference !== undefined) setTransferPreference(prefs.transferPreference);
    if (prefs.largeFont !== undefined) setLargeFont(prefs.largeFont);
    if (prefs.highContrast !== undefined) setHighContrast(prefs.highContrast);
  }, []);

  // Salvar preferências quando mudarem
  useEffect(() => {
    const prefs = {
      profile,
      walkPreference,
      transferPreference,
      largeFont,
      highContrast
    };
    saveUserPreferences(prefs);
  }, [profile, walkPreference, transferPreference, largeFont, highContrast]);

  // Aplicar estilos de acessibilidade
  useEffect(() => {
    const root = document.documentElement;
    if (largeFont) {
      root.style.fontSize = '18px';
    } else {
      root.style.fontSize = '';
    }
    
    if (highContrast) {
      root.classList.add('high-contrast');
    } else {
      root.classList.remove('high-contrast');
    }
  }, [largeFont, highContrast]);

  const handleProfileChange = (newProfile) => {
    setProfile(newProfile);
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
              Configurações
            </h1>
            <div className="w-8"></div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto pb-24 px-4 py-6">
          {/* Perfil de Mobilidade */}
          <section className="mb-8">
            <h2 className="text-base font-bold text-gray-900 mb-4">Perfil de Mobilidade</h2>
            <div className="flex gap-3">
              {[
                { value: 'padrao', label: 'Padrão' },
                { value: 'idoso', label: 'Idoso' },
                { value: 'pcd', label: 'PcD' }
              ].map((p) => (
                <button
                  key={p.value}
                  onClick={() => handleProfileChange(p.value)}
                  className={`flex-1 rounded-lg px-4 py-3 text-sm font-medium transition-colors ${
                    profile === p.value
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </section>

          {/* Preferências de Rota */}
          <section className="mb-8">
            <h2 className="text-base font-bold text-gray-900 mb-4">Preferências de Rota</h2>
            
            {/* Prefiro andar menos */}
            <div className="mb-6">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-gray-900">Prefiro andar menos</span>
              </div>
              <div className="relative">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={walkPreference}
                  onChange={(e) => setWalkPreference(Number(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>Menos</span>
                  <span>Mais</span>
                </div>
              </div>
            </div>

            {/* Prefiro menos transferências */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-gray-900">Prefiro menos transferências</span>
              </div>
              <div className="relative">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={transferPreference}
                  onChange={(e) => setTransferPreference(Number(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>Menos</span>
                  <span>Mais</span>
                </div>
              </div>
            </div>
          </section>

          {/* Acessibilidade */}
          <section className="mb-8">
            <h2 className="text-base font-bold text-gray-900 mb-4">Acessibilidade</h2>
            
            {/* Aumentar fonte */}
            <div className="flex items-center justify-between py-3 border-b border-gray-200">
              <span className="text-sm text-gray-900">Aumentar fonte</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={largeFont}
                  onChange={(e) => setLargeFont(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            {/* Alto contraste */}
            <div className="flex items-center justify-between py-3">
              <span className="text-sm text-gray-900">Alto contraste</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={highContrast}
                  onChange={(e) => setHighContrast(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </section>

          {/* Ajuda */}
          <section>
            <h2 className="text-base font-bold text-gray-900 mb-4">Ajuda</h2>
            
            {/* Perguntas Frequentes */}
            <button
              onClick={() => navigate('/faq')}
              className="w-full flex items-center justify-between py-3 border-b border-gray-200 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-8 h-8 rounded-full bg-gray-100">
                  <span className="material-symbols-outlined text-gray-600 text-lg">help</span>
                </div>
                <span className="text-sm text-gray-900">Perguntas Frequentes</span>
              </div>
              <span className="material-symbols-outlined text-gray-400">chevron_right</span>
            </button>
          </section>
        </main>
      </div>

      {/* Footer com BottomNav */}
      <footer className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200">
        <BottomNav />
        <div className="h-safe-area-bottom bg-white"></div>
      </footer>

      {/* Estilos para slider */}
      <style>{`
        input[type="range"].slider {
          -webkit-appearance: none;
          appearance: none;
          background: transparent;
          cursor: pointer;
        }
        
        input[type="range"].slider::-webkit-slider-track {
          background: #e5e7eb;
          height: 8px;
          border-radius: 4px;
        }
        
        input[type="range"].slider::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: #2563eb;
          cursor: pointer;
          margin-top: -6px;
        }
        
        input[type="range"].slider::-moz-range-track {
          background: #e5e7eb;
          height: 8px;
          border-radius: 4px;
        }
        
        input[type="range"].slider::-moz-range-thumb {
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: #2563eb;
          cursor: pointer;
          border: none;
        }
        
        .high-contrast {
          --text-primary: #000000;
          --text-secondary: #333333;
          --primary-color: #0000FF;
          --secondary-color: #FFFF00;
        }
      `}</style>
    </div>
  );
}

