import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../services/api';
import { formatTime, calculateRouteScore, saveFavorite } from '../utils';
import BottomNav from '../components/BottomNav';
import StopInfo from '../components/StopInfo';
import Map from '../components/Map';
import ReportBarrier from '../components/ReportBarrier';

export default function RouteDetail() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [route, setRoute] = useState(null);
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showFavoritePopup, setShowFavoritePopup] = useState(false);
  const [favoriteName, setFavoriteName] = useState('');
  const [showRealtime, setShowRealtime] = useState(false);
  const [paradasComPrevisao, setParadasComPrevisao] = useState([]);
  const [showReportBarrier, setShowReportBarrier] = useState(false);

  useEffect(() => {
    const storedRoute = JSON.parse(sessionStorage.getItem('selectedRoute') || 'null');
    const params = JSON.parse(sessionStorage.getItem('routeParams') || '{}');
    
    if (!storedRoute) {
      navigate('/routes');
      return;
    }

    setRoute(storedRoute);

    // Buscar detalhes completos
    const fetchDetails = async () => {
      try {
        const routeDetails = await api.getRouteDetails({
          path: storedRoute.path,
          profile: params.profile || 'padrao'
        });
        setDetails(routeDetails);
      } catch (error) {
        console.error('Erro ao buscar detalhes:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDetails();
  }, [id, navigate]);

  // Extrair paradas dos steps para previsão de chegada
  useEffect(() => {
    if (!details || !showRealtime) {
      setParadasComPrevisao([]);
      return;
    }

    // Extrair paradas de ônibus dos steps
    const paradas = [];
    details.steps?.forEach(step => {
      if (step.mode === 'onibus' || step.mode === 'bus') {
        // Tentar extrair código de parada do step
        // Nota: Isso requer que os nós tenham código Olho Vivo mapeado
        // Por enquanto, vamos usar coordenadas para buscar paradas próximas
        if (step.to_lat && step.to_lon) {
          paradas.push({
            codigo: step.to_olho_vivo_code || null, // Código Olho Vivo se disponível
            nome: step.to_name || step.to,
            lat: step.to_lat,
            lon: step.to_lon
          });
        }
      }
    });

    setParadasComPrevisao(paradas);
  }, [details, showRealtime]);

  const handleSaveFavorite = (e) => {
    e.preventDefault();
    if (favoriteName.trim() && route) {
      saveFavorite(route, favoriteName.trim());
      setShowFavoritePopup(false);
      setFavoriteName('');
      alert('Rota salva com sucesso!');
    }
  };

  const getStepIcon = (mode) => {
    const icons = {
      'metro': 'directions_subway',
      'onibus': 'directions_bus',
      'pe': 'directions_walk',
      'trem': 'train',
      'bus': 'directions_bus',
      'subway': 'directions_subway',
      'walk': 'directions_walk',
      'train': 'train'
    };
    return icons[mode?.toLowerCase()] || 'directions_walk';
  };

  const getStepInstruction = (step, mode) => {
    if (step.instruction) {
      return step.instruction;
    }
    
    const modeNames = {
      'metro': 'Pegue o metrô',
      'onibus': 'Pegue o ônibus',
      'pe': 'Caminhe',
      'trem': 'Pegue o trem',
      'bus': 'Pegue o ônibus',
      'subway': 'Pegue o metrô',
      'walk': 'Caminhe',
      'train': 'Pegue o trem'
    };
    
    const modeName = modeNames[mode?.toLowerCase()] || 'Continue';
    
    if (step.type === 'walk') {
      return 'Caminhe até o ponto de partida';
    }
    
    return `${modeName} até ${step.to_name || step.to}`;
  };

  if (loading || !route) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p>Carregando...</p>
      </div>
    );
  }

  const score = calculateRouteScore(route);
  const steps = details?.steps || [];
  const totalTime = details?.total_time_min || route.tempo_total_min;
  const transfers = details?.transfers || route.transferencias || 0;
  const barriers = details?.barriers_avoided || route.barreiras_evitas || [];

  return (
    <div className="relative flex h-auto min-h-screen w-full flex-col justify-between overflow-x-hidden bg-white">
      <div>
        <header className="sticky top-0 z-10 bg-white shadow-sm">
          <div className="flex items-center p-4">
            <button
              onClick={() => navigate(-1)}
              className="text-[var(--text-primary)]"
            >
              <span className="material-symbols-outlined">arrow_back_ios_new</span>
            </button>
            <h1 className="flex-1 text-center text-lg font-bold text-[var(--text-primary)]">
              Rota Detalhada
            </h1>
            <button
              onClick={() => setShowFavoritePopup(true)}
              className="text-[var(--text-primary)]"
            >
              <span className="material-symbols-outlined">bookmark_add</span>
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto pb-24">
          {/* Mapa com rota */}
          <div className="px-4 py-3">
            <div className="aspect-video w-full rounded-xl overflow-hidden shadow-md relative">
              <Map 
                routePath={route?.path || []}
                showRealtime={showRealtime}
              />
            </div>
            <div className="mt-2 flex items-center justify-between">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={showRealtime}
                  onChange={(e) => setShowRealtime(e.target.checked)}
                  className="rounded"
                />
                <span>Mostrar ônibus em tempo real</span>
              </label>
            </div>
          </div>

          {/* Previsões de Chegada (se tempo real ativado) */}
          {showRealtime && paradasComPrevisao.length > 0 && (
            <section className="px-4 py-4">
              <h2 className="text-xl font-bold text-[var(--text-primary)] mb-4">
                Previsão de Chegada
              </h2>
              <div className="space-y-3">
                {paradasComPrevisao.map((parada, idx) => (
                  <StopInfo
                    key={idx}
                    codigoParada={parada.codigo}
                    nomeParada={parada.nome}
                    lat={parada.lat}
                    lon={parada.lon}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Passo a Passo */}
          <section className="px-4 py-4">
            <h2 className="text-xl font-bold text-[var(--text-primary)]">Passo a Passo</h2>
            <div className="mt-4 space-y-2">
              {steps.length > 0 ? (
                steps.map((step, index) => {
                  const isLast = index === steps.length - 1;
                  const mode = step.mode || 'pe';
                  const icon = getStepIcon(mode);
                  const instruction = getStepInstruction(step, mode);

                  return (
                    <div key={index} className="relative flex items-start gap-4">
                      {!isLast && (
                        <div className="absolute left-6 top-12 h-full w-0.5 bg-gray-300"></div>
                      )}
                      <div className="relative z-10 flex size-12 shrink-0 items-center justify-center rounded-full bg-[var(--secondary-color)]">
                        <span className="material-symbols-outlined text-[var(--text-primary)]">
                          {icon}
                        </span>
                      </div>
                      <div className="flex-1 pt-2.5">
                        <p className="text-base font-medium text-[var(--text-primary)]">
                          {instruction}
                        </p>
                        <p className="text-sm text-[var(--text-secondary)]">
                          {step.from_name || step.from} → {step.to_name || step.to}
                        </p>
                        {step.time_min > 0 && (
                          <p className="text-xs text-[var(--text-secondary)] mt-1">
                            {formatTime(step.time_min)}
                          </p>
                        )}
                      </div>
                    </div>
                  );
                })
              ) : (
                <p className="text-gray-500">Nenhum passo disponível</p>
              )}
            </div>
          </section>

          {/* Detalhes */}
          <section className="px-4 py-4">
            <h2 className="text-xl font-bold text-[var(--text-primary)]">Detalhes</h2>
            <div className="mt-4 rounded-lg bg-white p-4 shadow-sm">
              <div className="grid grid-cols-2 gap-x-6 gap-y-4">
                <div className="flex justify-between border-b border-gray-200 py-3">
                  <p className="text-sm text-[var(--text-secondary)]">Tempo total</p>
                  <p className="text-sm font-medium text-[var(--text-primary)]">
                    {formatTime(totalTime)}
                  </p>
                </div>
                <div className="flex justify-between border-b border-gray-200 py-3">
                  <p className="text-sm text-[var(--text-secondary)]">Transferências</p>
                  <p className="text-sm font-medium text-[var(--text-primary)]">
                    {transfers}
                  </p>
                </div>
                <div className="flex justify-between border-b border-gray-200 py-3">
                  <p className="text-sm text-[var(--text-secondary)]">Pontuação</p>
                  <p className="text-sm font-medium text-[var(--text-primary)]">
                    {score}
                  </p>
                </div>
                <div className="flex justify-between py-3">
                  <p className="text-sm text-[var(--text-secondary)]">Barreiras evitadas</p>
                  <p className="text-sm font-medium text-[var(--text-primary)]">
                    {barriers.length}
                  </p>
                </div>
              </div>
            </div>
            <div className="mt-4">
              <button
                onClick={() => setShowFavoritePopup(true)}
                className="flex w-full items-center justify-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm font-bold text-[var(--text-primary)] shadow-sm"
              >
                <span className="material-symbols-outlined text-lg">download</span>
                <span>Salvar para acesso offline</span>
              </button>
            </div>
          </section>
        </main>
      </div>

      {/* Footer */}
      <footer className="fixed bottom-0 z-10 w-full bg-white shadow-[0_-1px_3px_rgba(0,0,0,0.1)]">
        <div className="flex gap-4 p-4">
          <button
            onClick={() => setShowReportBarrier(true)}
            className="flex flex-1 cursor-pointer items-center justify-center gap-2 rounded-lg bg-gray-100 px-4 py-3 text-sm font-bold text-gray-700 hover:bg-gray-200 transition-colors"
          >
            <span className="material-symbols-outlined text-lg">report</span>
            <span className="truncate">Reportar Barreira</span>
          </button>
          <button
            onClick={() => {
              // Salvar rota atual no sessionStorage para navegação ativa
              sessionStorage.setItem('activeRoute', JSON.stringify({
                route,
                details,
                currentStep: 0
              }));
              navigate('/navigation');
            }}
            className="flex-1 cursor-pointer rounded-lg bg-blue-600 px-4 py-3 text-sm font-bold text-white hover:bg-blue-700 transition-colors"
          >
            <span className="truncate">Iniciar Rota</span>
          </button>
        </div>
        <BottomNav />
        <div className="h-safe-area-bottom bg-white"></div>
      </footer>

      {/* Modal Reportar Barreira */}
      <ReportBarrier
        isOpen={showReportBarrier}
        onClose={() => setShowReportBarrier(false)}
        onReport={(reporte) => {
          console.log('Barreira reportada:', reporte);
          // Aqui você salvaria o reporte no backend
          alert('Barreira reportada com sucesso! Obrigado por ajudar outros usuários.');
        }}
      />

      {/* Popup de Favorito */}
      {showFavoritePopup && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          onClick={() => setShowFavoritePopup(false)}
        >
          <div
            className="mx-4 w-full max-w-sm rounded-xl bg-white p-6 shadow-lg"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-center text-lg font-bold text-[var(--text-primary)]">
              Adicionar aos Favoritos
            </h3>
            <p className="mt-2 text-center text-sm text-[var(--text-secondary)]">
              Dê um nome para esta rota para salvá-la.
            </p>
            <form onSubmit={handleSaveFavorite} className="mt-6 space-y-4">
              <div>
                <label
                  className="text-sm font-medium text-[var(--text-primary)]"
                  htmlFor="routeName"
                >
                  Nome da Rota
                </label>
                <input
                  id="routeName"
                  type="text"
                  value={favoriteName}
                  onChange={(e) => setFavoriteName(e.target.value)}
                  placeholder="Ex: Casa, Trabalho"
                  className="mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-[var(--primary-color)] focus:ring-[var(--primary-color)]"
                  autoFocus
                />
              </div>
              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowFavoritePopup(false)}
                  className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-[var(--text-primary)]"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-[var(--primary-color)] px-4 py-2 text-sm font-medium text-white"
                >
                  Salvar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

