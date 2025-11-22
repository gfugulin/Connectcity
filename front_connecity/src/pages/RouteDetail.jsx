import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../services/api';
import { formatTime, calculateRouteScore, saveFavorite, getFavoriteIcon } from '../utils';
import BottomNav from '../components/BottomNav';
import StopInfo from '../components/StopInfo';
import Map from '../components/Map';

export default function RouteDetail() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [route, setRoute] = useState(null);
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showFavoritePopup, setShowFavoritePopup] = useState(false);
  const [favoriteName, setFavoriteName] = useState('');
  const [selectedIcon, setSelectedIcon] = useState('');
  const [showRealtime, setShowRealtime] = useState(false);
  const [paradasComPrevisao, setParadasComPrevisao] = useState([]);
  const [navigationActive, setNavigationActive] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [detailsError, setDetailsError] = useState('');
  const [showBarrierReport, setShowBarrierReport] = useState(false);
  const [barrierType, setBarrierType] = useState('');
  const [barrierLocation, setBarrierLocation] = useState('');
  const [barrierDescription, setBarrierDescription] = useState('');
  const [barrierPhoto, setBarrierPhoto] = useState(null);
  const [submittingBarrier, setSubmittingBarrier] = useState(false);

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
        setDetailsError('');
        const routeDetails = await api.getRouteDetails({
          path: storedRoute.path,
          profile: params.profile || 'padrao',
        });
        setDetails(routeDetails);
      } catch (error) {
        console.error('Erro ao buscar detalhes:', error);
        
        // Fallback: usar informações básicas da rota para não quebrar a tela
        const fallback = {
          path: storedRoute.path || [],
          total_time_min: storedRoute.tempo_total_min,
          transfers: storedRoute.transferencias || 0,
          barriers_avoided: storedRoute.barreiras_evitas || [],
          steps: [], // sem passo a passo detalhado
        };
        
        setDetails(fallback);
        setDetailsError(
          'Não foi possível carregar o passo a passo detalhado. O mapa ainda mostra o trajeto aproximado.'
        );
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
      const params = JSON.parse(sessionStorage.getItem('routeParams') || '{}');
      
      // Salvar favorito com informações completas
      const favoriteData = {
        ...route,
        from: params.from || params.fromName || route.from_name || '',
        to: params.to || params.toName || route.to_name || '',
        fromId: params.fromId || null,
        toId: params.toId || null,
        profile: params.profile || 'padrao',
        modes: details?.modes || route.modes || [],
        icon: selectedIcon || getFavoriteIcon(favoriteName.trim()),
        // Salvar também os steps se disponíveis para ter os nomes
        steps: details?.steps || route.steps || []
      };
      
      saveFavorite(favoriteData, favoriteName.trim(), selectedIcon);
      setShowFavoritePopup(false);
      setFavoriteName('');
      setSelectedIcon('');
      alert('Rota salva com sucesso!');
    }
  };

  const iconOptions = [
    { id: 'home', label: 'Casa', icon: 'home' },
    { id: 'work', label: 'Trabalho', icon: 'work' },
    { id: 'school', label: 'Faculdade', icon: 'school' },
    { id: 'fitness_center', label: 'Academia', icon: 'fitness_center' },
    { id: 'shopping_cart', label: 'Mercado', icon: 'shopping_cart' },
    { id: 'place', label: 'Outro', icon: 'place' }
  ];

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

  const handleStartNavigation = () => {
    if (!details || !details.steps || details.steps.length === 0) {
      alert(
        'Não foi possível carregar o passo a passo detalhado desta rota. Use o mapa para se orientar.'
      );
      return;
    }
    
    // Navegar para a tela de navegação ativa
    navigate('/navigation');
  };

  const handleStepClick = (index) => {
    setCurrentStepIndex(index);
    // Rolar para o passo clicado
    setTimeout(() => {
      const stepElement = document.querySelector(`[data-step-index="${index}"]`);
      if (stepElement) {
        stepElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }, 100);
  };

  // Rolar automaticamente para o passo ativo quando a navegação está ativa
  useEffect(() => {
    if (navigationActive && currentStepIndex >= 0) {
      const stepElement = document.querySelector(`[data-step-index="${currentStepIndex}"]`);
      if (stepElement) {
        stepElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [currentStepIndex, navigationActive]);

  const handleReportBarrier = () => {
    // Abrir modal de reportar barreira
    setShowBarrierReport(true);
  };

  const handleSubmitBarrierReport = async (e) => {
    e.preventDefault();
    
    if (!barrierType) {
      alert('Por favor, selecione um tipo de barreira.');
      return;
    }

    setSubmittingBarrier(true);

    try {
      const steps = details?.steps || [];
      const step =
        steps && steps.length > 0
          ? steps[currentStepIndex] || steps[steps.length - 1]
          : null;

      const params = JSON.parse(sessionStorage.getItem('routeParams') || '{}');

      const report = {
        route_id: route?.id || null,
        from_node: params.fromId || null,
        to_node: params.toId || null,
        step_index: step ? currentStepIndex : null,
        node_id: step ? (step.to || step.from) : null,
        profile: params.profile || 'padrao',
        type: barrierType,
        severity: 3,
        description: barrierDescription || (barrierLocation ? `Localização: ${barrierLocation}` : null),
        lat: step?.to_lat || step?.from_lat || null,
        lon: step?.to_lon || step?.from_lon || null,
        app_version: '1.0.0',
        platform: 'web',
      };

      const res = await api.reportBarrier(report);
      
      // Limpar formulário e fechar modal
      setBarrierType('');
      setBarrierLocation('');
      setBarrierDescription('');
      setBarrierPhoto(null);
      setShowBarrierReport(false);
      
      alert(res.message || 'Obrigado! Barreira registrada.');
    } catch (err) {
      console.error('Erro ao reportar barreira:', err);
      alert(
        err.response?.data?.detail || err.message ||
          'Não foi possível registrar a barreira. Tente novamente mais tarde.'
      );
    } finally {
      setSubmittingBarrier(false);
    }
  };

  const handleBarrierPhotoChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validar tamanho (10MB)
      if (file.size > 10 * 1024 * 1024) {
        alert('O arquivo deve ter no máximo 10MB.');
        return;
      }
      // Validar tipo
      const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif'];
      if (!validTypes.includes(file.type)) {
        alert('Por favor, selecione uma imagem PNG, JPG ou GIF.');
        return;
      }
      setBarrierPhoto(file);
    }
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
                routeDetails={details}
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
            {detailsError && (
              <p className="mt-2 text-sm text-red-600">{detailsError}</p>
            )}
            <div className="mt-4 space-y-2">
              {steps.length > 0 ? (
                steps.map((step, index) => {
                  const isLast = index === steps.length - 1;
                  const mode = step.mode || 'pe';
                  const icon = getStepIcon(mode);
                  const instruction = getStepInstruction(step, mode);
                  const isActive = navigationActive && index === currentStepIndex;

                  return (
                    <div
                      key={index}
                      data-step-index={index}
                      className={
                        'relative flex items-start gap-4 rounded-lg px-2 py-2 cursor-pointer transition-colors ' +
                        (isActive
                          ? 'bg-[var(--secondary-color)]/20 ring-2 ring-[var(--primary-color)]'
                          : 'hover:bg-gray-50')
                      }
                      onClick={() => handleStepClick(index)}
                    >
                      {!isLast && (
                        <div className="absolute left-6 top-12 h-full w-0.5 bg-gray-300"></div>
                      )}
                      <div className="relative z-10 flex size-12 shrink-0 items-center justify-center rounded-full bg-[var(--secondary-color)]">
                        <span className="material-symbols-outlined text-[var(--text-primary)]">
                          {icon}
                        </span>
                      </div>
                      <div className="flex-1 pt-2.5">
                        <p
                          className={
                            'text-base font-medium ' +
                            (isActive
                              ? 'text-[var(--primary-color)] text-lg'
                              : 'text-[var(--text-primary)]')
                          }
                        >
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
            onClick={handleReportBarrier}
            className="flex flex-1 cursor-pointer items-center justify-center gap-2 rounded-lg bg-[var(--secondary-color)] px-4 py-3 text-sm font-bold text-[var(--text-primary)] hover:bg-[var(--secondary-color)]/80 transition-colors"
          >
            <span className="material-symbols-outlined text-lg">report</span>
            <span className="truncate">Reportar Barreira</span>
          </button>
          <button
            onClick={handleStartNavigation}
            className="flex-1 cursor-pointer rounded-lg px-4 py-3 text-sm font-bold text-white hover:opacity-90 transition-colors flex items-center justify-center gap-2"
            style={{
              backgroundColor: navigationActive ? '#ef4444' : 'var(--primary-color)'
            }}
          >
            <span className="material-symbols-outlined text-lg">
              {navigationActive ? 'stop' : 'navigation'}
            </span>
            <span className="truncate">
              {navigationActive ? 'Parar Navegação' : 'Iniciar Rota'}
            </span>
          </button>
        </div>
        <BottomNav />
        <div className="h-safe-area-bottom bg-white"></div>
      </footer>

      {/* Popup de Favorito */}
      {showFavoritePopup && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          onClick={() => {
            setShowFavoritePopup(false);
            setFavoriteName('');
            setSelectedIcon('');
          }}
        >
          <div
            className="mx-4 w-full max-w-sm rounded-xl bg-white shadow-lg"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
              <h2 className="text-lg font-bold text-[var(--text-primary)]">
                Adicionar Favorito
              </h2>
              <button
                onClick={() => {
                  setShowFavoritePopup(false);
                  setFavoriteName('');
                  setSelectedIcon('');
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            {/* Formulário */}
            <form onSubmit={handleSaveFavorite} className="px-6 py-6 space-y-6">
              {/* Nome do favorito */}
              <div>
                <label
                  className="block text-sm font-medium text-[var(--text-primary)] mb-2"
                  htmlFor="favoriteName"
                >
                  Nome do favorito
                </label>
                <input
                  id="favoriteName"
                  type="text"
                  value={favoriteName}
                  onChange={(e) => setFavoriteName(e.target.value)}
                  placeholder="Ex: Casa, Trabalho..."
                  className="w-full rounded-lg border border-gray-300 px-4 py-3 text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  autoFocus
                  required
                />
              </div>

              {/* Escolha um ícone */}
              <div>
                <label className="block text-sm font-bold text-[var(--text-primary)] mb-3">
                  Escolha um ícone
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {iconOptions.map((option) => (
                    <button
                      key={option.id}
                      type="button"
                      onClick={() => setSelectedIcon(option.id)}
                      className={`flex flex-col items-center justify-center gap-2 rounded-lg border-2 p-4 transition-all ${
                        selectedIcon === option.id
                          ? 'border-blue-600 bg-blue-50'
                          : 'border-gray-200 bg-white hover:border-gray-300'
                      }`}
                    >
                      <span
                        className={`material-symbols-outlined text-2xl ${
                          selectedIcon === option.id
                            ? 'text-blue-600'
                            : 'text-gray-600'
                        }`}
                      >
                        {option.icon}
                      </span>
                      <span
                        className={`text-xs font-medium ${
                          selectedIcon === option.id
                            ? 'text-blue-600'
                            : 'text-gray-600'
                        }`}
                      >
                        {option.label}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Botão Salvar */}
              <div className="pt-2">
                <button
                  type="submit"
                  disabled={!favoriteName.trim()}
                  className="w-full rounded-lg bg-blue-600 px-4 py-3 text-sm font-medium text-white hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Salvar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal de Reportar Barreira */}
      {showBarrierReport && (
        <div
          className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50"
          onClick={() => {
            if (!submittingBarrier) {
              setShowBarrierReport(false);
            }
          }}
        >
          <div
            className="w-full max-w-md rounded-t-xl sm:rounded-xl bg-white shadow-lg max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header do Modal */}
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <h2 className="text-xl font-bold text-[var(--text-primary)]">
                Reportar Barreira
              </h2>
              <button
                onClick={() => {
                  if (!submittingBarrier) {
                    setShowBarrierReport(false);
                  }
                }}
                className="text-gray-500 hover:text-gray-700"
                disabled={submittingBarrier}
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            {/* Conteúdo do Modal */}
            <form onSubmit={handleSubmitBarrierReport} className="px-6 py-4 space-y-6">
              <p className="text-sm text-[var(--text-secondary)]">
                Descreva o impedimento para ajudar outros usuários.
              </p>

              {/* Tipo de Barreira */}
              <div>
                <label
                  className="block text-sm font-medium text-[var(--text-primary)] mb-2"
                  htmlFor="barrier-type"
                >
                  Tipo de barreira
                </label>
                <div className="relative">
                  <select
                    id="barrier-type"
                    value={barrierType}
                    onChange={(e) => setBarrierType(e.target.value)}
                    className="w-full appearance-none rounded-lg border border-gray-300 bg-white px-4 py-3 pr-10 text-sm focus:border-[var(--primary-color)] focus:ring-[var(--primary-color)]"
                    required
                    disabled={submittingBarrier}
                  >
                    <option value="">Selecione um tipo</option>
                    <option value="escada">Escada</option>
                    <option value="calcada_ruim">Calçada ruim</option>
                    <option value="alagamento">Alagamento</option>
                    <option value="obstaculo">Obstáculo</option>
                    <option value="iluminacao_ruim">Iluminação ruim</option>
                    <option value="seguranca">Segurança</option>
                    <option value="sinalizacao_ruim">Sinalização ruim</option>
                    <option value="outro">Outro</option>
                  </select>
                  <span className="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
                    arrow_drop_down
                  </span>
                </div>
              </div>

              {/* Localização Precisa */}
              <div>
                <label
                  className="block text-sm font-medium text-[var(--text-primary)] mb-2"
                  htmlFor="barrier-location"
                >
                  Localização precisa
                </label>
                <div className="relative">
                  <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                    location_on
                  </span>
                  <input
                    id="barrier-location"
                    type="text"
                    value={barrierLocation}
                    onChange={(e) => setBarrierLocation(e.target.value)}
                    placeholder="Ex: Em frente ao nº 123"
                    className="w-full rounded-lg border border-gray-300 bg-white pl-10 pr-4 py-3 text-sm focus:border-[var(--primary-color)] focus:ring-[var(--primary-color)]"
                    disabled={submittingBarrier}
                  />
                </div>
              </div>

              {/* Observações Adicionais */}
              <div>
                <label
                  className="block text-sm font-medium text-[var(--text-primary)] mb-2"
                  htmlFor="barrier-description"
                >
                  Observações adicionais
                </label>
                <textarea
                  id="barrier-description"
                  value={barrierDescription}
                  onChange={(e) => setBarrierDescription(e.target.value)}
                  placeholder="Descreva mais detalhes sobre a barreira..."
                  rows={3}
                  maxLength={500}
                  className="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm focus:border-[var(--primary-color)] focus:ring-[var(--primary-color)] resize-none"
                  disabled={submittingBarrier}
                />
                <p className="mt-1 text-xs text-gray-500 text-right">
                  {barrierDescription.length}/500
                </p>
              </div>

              {/* Anexar Foto */}
              <div>
                <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                  Anexar foto (opcional)
                </label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-[var(--primary-color)] transition-colors">
                  <input
                    type="file"
                    id="barrier-photo"
                    accept="image/png,image/jpeg,image/jpg,image/gif"
                    onChange={handleBarrierPhotoChange}
                    className="hidden"
                    disabled={submittingBarrier}
                  />
                  <label
                    htmlFor="barrier-photo"
                    className="cursor-pointer flex flex-col items-center gap-2"
                  >
                    <span className="material-symbols-outlined text-3xl text-gray-400">
                      add_a_photo
                    </span>
                    <div className="text-sm text-[var(--text-secondary)]">
                      {barrierPhoto ? (
                        <span className="text-[var(--primary-color)] font-medium">
                          {barrierPhoto.name}
                        </span>
                      ) : (
                        <>
                          <p className="font-medium">Carregue um arquivo ou arraste e solte</p>
                          <p className="text-xs mt-1">PNG, JPG, GIF até 10MB</p>
                        </>
                      )}
                    </div>
                  </label>
                </div>
              </div>

              {/* Botões */}
              <div className="flex gap-3 pt-2 pb-4">
                <button
                  type="button"
                  onClick={() => {
                    if (!submittingBarrier) {
                      setShowBarrierReport(false);
                    }
                  }}
                  className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm font-medium text-[var(--text-primary)] hover:bg-gray-50 transition-colors"
                  disabled={submittingBarrier}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="flex-1 rounded-lg bg-[var(--primary-color)] px-4 py-3 text-sm font-bold text-white hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={submittingBarrier || !barrierType}
                >
                  {submittingBarrier ? 'Enviando...' : 'Enviar Reporte'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

