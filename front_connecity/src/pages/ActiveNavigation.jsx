import { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Polyline, useMap, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import api from '../services/api';
import { formatTime } from '../utils';

// Fix para ícones padrão do Leaflet
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
import iconRetina from 'leaflet/dist/images/marker-icon-2x.png';

// Configurar ícone padrão globalmente (sem guardar em variável)
if (typeof window !== 'undefined') {
  delete L.Icon.Default.prototype._getIconUrl;
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: iconRetina,
    iconUrl: icon,
    shadowUrl: iconShadow,
  });
}

// Componente para centralizar o mapa na posição atual
function MapCenter({ position }) {
  const map = useMap();
  useEffect(() => {
    if (position) {
      map.setView(position, 16);
    }
  }, [position, map]);
  return null;
}

export default function ActiveNavigation() {
  const navigate = useNavigate();
  const [route, setRoute] = useState(null);
  const [details, setDetails] = useState(null);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [remainingTime, setRemainingTime] = useState(0);
  const [currentPosition, setCurrentPosition] = useState(null);
  const [showBarrierReport, setShowBarrierReport] = useState(false);
  const [audioEnabled, setAudioEnabled] = useState(false);
  
  // Estados para o formulário de reportar barreira
  const [barrierType, setBarrierType] = useState('');
  const [barrierLocation, setBarrierLocation] = useState('');
  const [barrierDescription, setBarrierDescription] = useState('');
  const [barrierPhoto, setBarrierPhoto] = useState(null);
  const [submittingBarrier, setSubmittingBarrier] = useState(false);
  const [dragActive, setDragActive] = useState(false);

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
          profile: params.profile || 'padrao',
        });
        setDetails(routeDetails);
        
        // Calcular tempo restante inicial
        if (routeDetails.total_time_min) {
          setRemainingTime(Math.round(routeDetails.total_time_min));
        }
      } catch (error) {
        console.error('Erro ao buscar detalhes:', error);
        // Usar dados básicos da rota
        setDetails({
          path: storedRoute.path || [],
          total_time_min: storedRoute.tempo_total_min,
          steps: [],
        });
        setRemainingTime(Math.round(storedRoute.tempo_total_min || 0));
      }
    };

    fetchDetails();

    // Simular atualização de tempo restante (a cada minuto)
    const timeInterval = setInterval(() => {
      setRemainingTime(prev => Math.max(0, prev - 1));
    }, 60000);

    return () => clearInterval(timeInterval);
  }, [navigate]);

  // Efeito separado para GPS e atualização de passo baseado em localização
  useEffect(() => {
    if (!details?.steps || details.steps.length === 0) return;

    // Função para atualizar passo atual baseado na localização
    const updateCurrentStepBasedOnLocation = (userPos) => {
      if (!details?.steps || details.steps.length === 0) return;

      // Calcular distância para cada passo e encontrar o mais próximo
      let closestStepIndex = currentStepIndex;
      let minDistance = Infinity;

      details.steps.forEach((step, index) => {
        if (step.to_lat && step.to_lon) {
          // Calcular distância usando fórmula de Haversine (simplificada)
          const latDiff = step.to_lat - userPos[0];
          const lonDiff = step.to_lon - userPos[1];
          const distance = Math.sqrt(latDiff * latDiff + lonDiff * lonDiff) * 111; // Aproximação em km

          // Se estiver próximo (menos de 100m) e for um passo futuro, atualizar
          if (distance < 0.1 && index >= currentStepIndex && distance < minDistance) {
            minDistance = distance;
            closestStepIndex = index;
          }
        }
      });

      if (closestStepIndex !== currentStepIndex && closestStepIndex > currentStepIndex) {
        setCurrentStepIndex(closestStepIndex);
        // Atualizar tempo restante
        const remainingSteps = details.steps.slice(closestStepIndex);
        const remainingTime = remainingSteps.reduce((sum, step) => sum + (step.time_min || 0), 0);
        setRemainingTime(Math.round(remainingTime));
      }
    };

    // Obter posição GPS atual
    let watchId = null;

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setCurrentPosition([position.coords.latitude, position.coords.longitude]);
        },
        (error) => {
          console.warn('Erro ao obter localização:', error);
          // Fallback: usar primeira coordenada da rota se disponível
          if (details?.steps?.[0]) {
            const firstStep = details.steps[0];
            if (firstStep.from_lat && firstStep.from_lon) {
              setCurrentPosition([firstStep.from_lat, firstStep.from_lon]);
            } else {
              setCurrentPosition([-23.5505, -46.6333]); // Default SP
            }
          } else {
            setCurrentPosition([-23.5505, -46.6333]); // Default SP
          }
        },
        { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
      );

      // Atualizar posição periodicamente durante navegação
      watchId = navigator.geolocation.watchPosition(
        (position) => {
          const newPos = [position.coords.latitude, position.coords.longitude];
          setCurrentPosition(newPos);
          updateCurrentStepBasedOnLocation(newPos);
        },
        (error) => {
          console.warn('Erro ao atualizar localização:', error);
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 5000 }
      );
    } else {
      // Fallback se geolocation não estiver disponível
      if (details?.steps?.[0]) {
        const firstStep = details.steps[0];
        if (firstStep.from_lat && firstStep.from_lon) {
          setCurrentPosition([firstStep.from_lat, firstStep.from_lon]);
        } else {
          setCurrentPosition([-23.5505, -46.6333]);
        }
      } else {
        setCurrentPosition([-23.5505, -46.6333]);
      }
    }

    return () => {
      if (watchId !== null && navigator.geolocation) {
        navigator.geolocation.clearWatch(watchId);
      }
    };
  }, [details, currentStepIndex]);

  // Obter passo atual
  const currentStep = details?.steps?.[currentStepIndex] || null;
  const nextStep = details?.steps?.[currentStepIndex + 1] || null;

  // Obter instrução de navegação
  const getNavigationInstruction = () => {
    if (!currentStep) return 'Siga a rota';
    
    const mode = currentStep.mode || 'pe';
    const instruction = currentStep.instruction || '';
    
    if (instruction) return instruction;
    
    if (mode === 'pe' || mode === 'walk') {
      if (currentStep.to_name) {
        return `Caminhe até ${currentStep.to_name}`;
      }
      return 'Continue caminhando';
    }
    
    if (mode === 'onibus' || mode === 'bus') {
      return `Pegue o ônibus até ${currentStep.to_name || currentStep.to}`;
    }
    
    if (mode === 'metro' || mode === 'subway') {
      return `Pegue o metrô até ${currentStep.to_name || currentStep.to}`;
    }
    
    return 'Continue seguindo a rota';
  };

  // Obter ícone de direção
  const getDirectionIcon = () => {
    if (!currentStep) return 'straight';
    const instruction = (currentStep.instruction || '').toLowerCase();
    if (instruction.includes('direita') || instruction.includes('right')) return 'turn_right';
    if (instruction.includes('esquerda') || instruction.includes('left')) return 'turn_left';
    if (instruction.includes('retorno') || instruction.includes('u-turn')) return 'u_turn_right';
    return 'straight';
  };

  // Obter coordenadas da rota para o mapa
  const routeCoordinates = useMemo(() => {
    if (!details?.steps) return [];
    const coords = [];
    details.steps.forEach(step => {
      if (step.segments && step.segments.length > 0) {
        step.segments.forEach(segment => {
          if (segment.from_lat && segment.from_lon) {
            coords.push([segment.from_lat, segment.from_lon]);
          }
          if (segment.to_lat && segment.to_lon) {
            coords.push([segment.to_lat, segment.to_lon]);
          }
        });
      } else if (step.from_lat && step.from_lon) {
        coords.push([step.from_lat, step.from_lon]);
      }
      if (step.to_lat && step.to_lon) {
        coords.push([step.to_lat, step.to_lon]);
      }
    });
    return coords;
  }, [details]);

  const handleReportBarrier = () => {
    // Preencher localização com a posição atual se disponível
    if (currentPosition && details?.steps?.[currentStepIndex]) {
      const step = details.steps[currentStepIndex];
      if (step.to_name) {
        setBarrierLocation(`Próximo a ${step.to_name}`);
      }
    }
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
      const step = details?.steps?.[currentStepIndex] || null;
      const params = JSON.parse(sessionStorage.getItem('routeParams') || '{}');
      
      // Montar descrição combinando localização e observações
      let description = '';
      if (barrierLocation) {
        description += `Localização: ${barrierLocation}`;
      }
      if (barrierDescription) {
        description += description ? `\n\n${barrierDescription}` : barrierDescription;
      }

      const report = {
        route_id: route?.id || null,
        from_node: params.fromId || null,
        to_node: params.toId || null,
        step_index: step ? currentStepIndex : null,
        node_id: step ? (step.to || step.from) : null,
        profile: params.profile || 'padrao',
        type: barrierType,
        severity: 3, // Default severity
        description: description || null,
        lat: currentPosition ? currentPosition[0] : (step?.to_lat || step?.from_lat || null),
        lon: currentPosition ? currentPosition[1] : (step?.to_lon || step?.from_lon || null),
        app_version: '1.0.0',
        platform: 'web',
        created_at: new Date().toISOString(),
      };

      const res = await api.reportBarrier(report);
      
      // Limpar formulário e fechar modal
      setBarrierType('');
      setBarrierLocation('');
      setBarrierDescription('');
      setBarrierPhoto(null);
      setShowBarrierReport(false);
      
      alert(res.message || 'Obrigado! Seu relato de barreira foi registrado.');
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

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.size > 10 * 1024 * 1024) {
        alert('O arquivo deve ter no máximo 10MB.');
        return;
      }
      const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif'];
      if (!validTypes.includes(file.type)) {
        alert('Por favor, selecione uma imagem PNG, JPG ou GIF.');
        return;
      }
      setBarrierPhoto(file);
    }
  };

  const handleStopNavigation = () => {
    if (window.confirm('Deseja parar a navegação?')) {
      navigate(-1);
    }
  };

  if (!route || !details) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p>Carregando navegação...</p>
      </div>
    );
  }

  const steps = details.steps || [];
  const nextStop = nextStep || null;
  const nextStopTime = nextStep?.time_min || 0;

  return (
    <div className="relative h-screen w-full overflow-hidden bg-gray-100">
      {/* Header com tempo restante */}
      <header className="absolute top-0 left-0 right-0 z-30 bg-gray-900/80 backdrop-blur-sm text-white">
        <div className="flex items-center justify-between px-4 py-3">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center justify-center w-10 h-10 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
          >
            <span className="material-symbols-outlined text-white">arrow_back</span>
          </button>
          
          <div className="flex-1 text-center">
            <p className="text-xs text-gray-300">Tempo restante</p>
            <p className="text-2xl font-bold">{remainingTime} min</p>
          </div>
          
          <button
            onClick={handleStopNavigation}
            className="flex items-center justify-center w-10 h-10 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
          >
            <span className="material-symbols-outlined text-white">close</span>
          </button>
        </div>
      </header>

      {/* Mapa em destaque */}
      <div className="absolute inset-0 z-0">
        <MapContainer
          center={currentPosition || [-23.5505, -46.6333]}
          zoom={16}
          style={{ height: '100%', width: '100%' }}
          zoomControl={false}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          
          {currentPosition && (
            <Marker position={currentPosition}>
              <Popup>Você está aqui</Popup>
            </Marker>
          )}
          
          {routeCoordinates.length > 0 && (
            <Polyline
              positions={routeCoordinates}
              color="#4285F4"
              weight={5}
              opacity={0.7}
            />
          )}
          
          {currentPosition && <MapCenter position={currentPosition} />}
        </MapContainer>
      </div>

      {/* Badge de chegada (quando chegar ao ponto) */}
      {currentStepIndex >= steps.length - 1 && (
        <div className="absolute top-20 right-4 z-30 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2">
          <span className="material-symbols-outlined">check_circle</span>
          <span className="font-bold">Chegou ao ponto!</span>
        </div>
      )}

      {/* Card de navegação na parte inferior */}
      <div className="absolute bottom-0 left-0 right-0 z-30 bg-white rounded-t-3xl shadow-2xl">
        <div className="px-6 py-4">
          {/* Instrução atual */}
          <div className="flex items-start gap-4 mb-4">
            <div className="flex-1">
              <p className="text-lg font-semibold text-gray-900">
                {getNavigationInstruction()}
              </p>
            </div>
            <div className="flex items-center justify-center w-16 h-16 rounded-full bg-blue-100">
              <span className="material-symbols-outlined text-blue-600 text-3xl">
                {getDirectionIcon()}
              </span>
            </div>
          </div>

          {/* Próxima parada */}
          {nextStop && (
            <div className="mb-4 pb-4 border-b border-gray-200">
              <p className="text-sm text-gray-600 mb-1">Próxima parada</p>
              <div className="flex items-center justify-between">
                <p className="text-base font-medium text-gray-900">
                  {nextStop.to_name || nextStop.to || 'Próximo ponto'}
                </p>
                {nextStopTime > 0 && (
                  <p className="text-sm font-semibold text-blue-600">
                    {Math.round(nextStopTime)} min
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Barra de progresso */}
          <div className="mb-4">
            <div className="h-1 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-600 transition-all duration-300"
                style={{
                  width: `${((currentStepIndex + 1) / Math.max(steps.length, 1)) * 100}%`,
                }}
              />
            </div>
          </div>

          {/* Botões de ação */}
          <div className="flex gap-3">
            <button
              onClick={handleReportBarrier}
              className="flex-1 flex items-center justify-center gap-2 rounded-xl border-2 border-gray-300 bg-white px-4 py-3 text-gray-700 font-medium hover:bg-gray-50 transition-colors"
            >
              <span className="material-symbols-outlined">report</span>
              <span>Reportar</span>
            </button>
            <button
              onClick={() => setAudioEnabled(!audioEnabled)}
              className={`flex-1 flex items-center justify-center gap-2 rounded-xl px-4 py-3 font-medium transition-colors ${
                audioEnabled
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-blue-100 text-blue-600 hover:bg-blue-200'
              }`}
            >
              <span className="material-symbols-outlined">
                {audioEnabled ? 'volume_up' : 'volume_off'}
              </span>
              <span>Áudio</span>
            </button>
          </div>
        </div>
      </div>

      {/* Modal completo de reportar barreira */}
      {showBarrierReport && (
        <div
          className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50"
          onClick={() => {
            setShowBarrierReport(false);
            setBarrierType('');
            setBarrierLocation('');
            setBarrierDescription('');
            setBarrierPhoto(null);
          }}
        >
          <div
            className="w-full max-w-md rounded-t-xl sm:rounded-xl bg-white shadow-lg max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10">
              <h2 className="text-xl font-bold text-gray-900">Reportar Barreira</h2>
              <button
                onClick={() => {
                  setShowBarrierReport(false);
                  setBarrierType('');
                  setBarrierLocation('');
                  setBarrierDescription('');
                  setBarrierPhoto(null);
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            {/* Formulário */}
            <form onSubmit={handleSubmitBarrierReport} className="px-6 py-4">
              <p className="text-sm text-gray-600 mb-6">
                Descreva o impedimento para ajudar outros usuários.
              </p>

              {/* Tipo de barreira */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tipo de barreira
                </label>
                <select
                  value={barrierType}
                  onChange={(e) => setBarrierType(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none bg-white"
                  required
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
              </div>

              {/* Localização precisa */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Localização precisa
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
                    <span className="material-symbols-outlined text-xl">location_on</span>
                  </span>
                  <input
                    type="text"
                    value={barrierLocation}
                    onChange={(e) => setBarrierLocation(e.target.value)}
                    placeholder="Ex: Em frente ao nº 123"
                    className="w-full rounded-lg border border-gray-300 pl-12 pr-4 py-3 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Observações adicionais */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Observações adicionais
                </label>
                <textarea
                  value={barrierDescription}
                  onChange={(e) => setBarrierDescription(e.target.value)}
                  placeholder="Descreva mais detalhes sobre a barreira..."
                  rows={4}
                  className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                />
              </div>

              {/* Anexar foto */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Anexar foto (opcional)
                </label>
                <div
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                    dragActive
                      ? 'border-blue-500 bg-blue-50'
                      : barrierPhoto
                      ? 'border-green-500 bg-green-50'
                      : 'border-gray-300 bg-gray-50'
                  }`}
                >
                  <input
                    type="file"
                    id="barrier-photo"
                    accept="image/png,image/jpeg,image/jpg,image/gif"
                    onChange={handleBarrierPhotoChange}
                    className="hidden"
                  />
                  {barrierPhoto ? (
                    <div>
                      <span className="material-symbols-outlined text-4xl text-green-600 mb-2 block">
                        check_circle
                      </span>
                      <p className="text-sm font-medium text-gray-900 mb-1">
                        {barrierPhoto.name}
                      </p>
                      <button
                        type="button"
                        onClick={() => setBarrierPhoto(null)}
                        className="text-sm text-blue-600 hover:text-blue-700 mt-2"
                      >
                        Remover foto
                      </button>
                    </div>
                  ) : (
                    <div>
                      <span className="material-symbols-outlined text-4xl text-gray-400 mb-2 block">
                        add_a_photo
                      </span>
                      <label
                        htmlFor="barrier-photo"
                        className="cursor-pointer text-blue-600 hover:text-blue-700 font-medium block mb-1"
                      >
                        Carregue um arquivo ou arraste e solte
                      </label>
                      <p className="text-xs text-gray-500">
                        PNG, JPG, GIF até 10MB
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Botões */}
              <div className="flex gap-3 pb-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowBarrierReport(false);
                    setBarrierType('');
                    setBarrierLocation('');
                    setBarrierDescription('');
                    setBarrierPhoto(null);
                  }}
                  className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                  disabled={submittingBarrier}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="flex-1 rounded-lg bg-blue-600 px-4 py-3 text-sm font-medium text-white hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={submittingBarrier}
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

