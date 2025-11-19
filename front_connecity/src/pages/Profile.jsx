import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import BottomNav from '../components/BottomNav';

export default function Profile() {
  const navigate = useNavigate();
  
  // Estado para perfil de mobilidade
  const [mobilityProfile, setMobilityProfile] = useState('padrao');
  
  // Estado para preferências de rota (valores de 0 a 100)
  const [routePreferences, setRoutePreferences] = useState({
    preferLessWalking: 70, // 0 = Menos, 100 = Mais
    preferFewerTransfers: 40 // 0 = Menos, 100 = Mais
  });
  
  // Estado para acessibilidade
  const [accessibility, setAccessibility] = useState({
    largeFont: false,
    highContrast: false
  });

  const handleSliderChange = (key, value) => {
    setRoutePreferences(prev => ({
      ...prev,
      [key]: parseInt(value)
    }));
  };

  const handleToggle = (key) => {
    setAccessibility(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
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
            Configurações
          </h1>
        </div>
      </header>

      <main className="px-4 py-6 space-y-8">
        {/* Perfil de Mobilidade */}
        <section>
          <h2 className="text-base font-bold text-gray-900 mb-4">Perfil de Mobilidade</h2>
          <div className="grid grid-cols-3 gap-3">
            {[
              { value: 'padrao', icon: 'directions_walk', label: 'Padrão' },
              { value: 'idoso', icon: 'elderly', label: 'Idoso' },
              { value: 'pcd', icon: 'accessible', label: 'PcD' }
            ].map((profile) => (
              <label key={profile.value} className="cursor-pointer">
                <input
                  type="radio"
                  name="mobility-profile"
                  value={profile.value}
                  checked={mobilityProfile === profile.value}
                  onChange={(e) => setMobilityProfile(e.target.value)}
                  className="sr-only"
                />
                <div
                  className={`flex flex-col items-center justify-center p-4 rounded-xl border-2 transition-all ${
                    mobilityProfile === profile.value
                      ? 'border-primary-500 bg-primary-50 text-primary-700 font-semibold'
                      : 'border-gray-300 bg-white text-gray-600 hover:border-gray-400'
                  }`}
                >
                  <span className="material-symbols-outlined text-3xl mb-2">{profile.icon}</span>
                  <span className="text-sm font-medium">{profile.label}</span>
                </div>
              </label>
            ))}
          </div>
        </section>

        {/* Preferências de Rota */}
        <section>
          <h2 className="text-base font-bold text-gray-900 mb-4">Preferências de Rota</h2>
          
          <div className="space-y-6">
            {/* Prefiro andar menos */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium text-gray-700">Prefiro andar menos</span>
              </div>
              <div className="relative">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={routePreferences.preferLessWalking}
                  onChange={(e) => handleSliderChange('preferLessWalking', e.target.value)}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                  style={{
                    background: `linear-gradient(to right, #0d80f2 0%, #0d80f2 ${routePreferences.preferLessWalking}%, #e5e7eb ${routePreferences.preferLessWalking}%, #e5e7eb 100%)`
                  }}
                />
                <div className="flex justify-between mt-2">
                  <span className="text-xs text-gray-500">Menos</span>
                  <span className="text-xs text-gray-500">Mais</span>
                </div>
              </div>
            </div>

            {/* Prefiro menos transferências */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium text-gray-700">Prefiro menos transferências</span>
              </div>
              <div className="relative">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={routePreferences.preferFewerTransfers}
                  onChange={(e) => handleSliderChange('preferFewerTransfers', e.target.value)}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                  style={{
                    background: `linear-gradient(to right, #0d80f2 0%, #0d80f2 ${routePreferences.preferFewerTransfers}%, #e5e7eb ${routePreferences.preferFewerTransfers}%, #e5e7eb 100%)`
                  }}
                />
                <div className="flex justify-between mt-2">
                  <span className="text-xs text-gray-500">Menos</span>
                  <span className="text-xs text-gray-500">Mais</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Acessibilidade */}
        <section>
          <h2 className="text-base font-bold text-gray-900 mb-4">Acessibilidade</h2>
          
          <div className="space-y-4">
            {/* Aumentar fonte */}
            <label className="flex items-center justify-between p-4 bg-gray-50 rounded-xl cursor-pointer hover:bg-gray-100">
              <span className="text-sm font-medium text-gray-700">Aumentar fonte</span>
              <button
                type="button"
                onClick={() => handleToggle('largeFont')}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  accessibility.largeFont ? 'bg-primary-600' : 'bg-gray-300'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    accessibility.largeFont ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </label>

            {/* Alto contraste */}
            <label className="flex items-center justify-between p-4 bg-gray-50 rounded-xl cursor-pointer hover:bg-gray-100">
              <span className="text-sm font-medium text-gray-700">Alto contraste</span>
              <button
                type="button"
                onClick={() => handleToggle('highContrast')}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  accessibility.highContrast ? 'bg-primary-600' : 'bg-gray-300'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    accessibility.highContrast ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </label>
          </div>
        </section>

        {/* Ajuda */}
        <section>
          <h2 className="text-base font-bold text-gray-900 mb-4">Ajuda</h2>
          
          <button 
            onClick={() => navigate('/faq')}
            className="w-full flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-gray-100"
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                <span className="material-symbols-outlined text-gray-600 text-lg">help</span>
              </div>
              <span className="text-sm font-medium text-gray-700">Perguntas Frequentes</span>
            </div>
            <span className="material-symbols-outlined text-gray-400">chevron_right</span>
          </button>
        </section>
      </main>

      {/* Bottom Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200">
        <BottomNav />
      </div>
    </div>
  );
}
