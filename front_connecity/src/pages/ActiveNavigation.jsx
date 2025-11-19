import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Map from '../components/Map';
import ReportBarrier from '../components/ReportBarrier';
import { formatTime } from '../utils';

export default function ActiveNavigation() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [timeRemaining, setTimeRemaining] = useState(18); // minutos (mock - para demo, diminui a cada segundo)
  const [showReportBarrier, setShowReportBarrier] = useState(false);
  const [audioEnabled, setAudioEnabled] = useState(false);

  // Mock de steps da navegação ativa
  const navigationSteps = [
    {
      instruction: 'Vire à direita na Rua Guajajaras',
      nextStop: 'Av. Álvares Cabral, 400',
      nextStopTime: 2,
      progress: 60,
      turnDirection: 'right'
    },
    {
      instruction: 'Continue em frente na Av. Washington Luiz',
      nextStop: 'Parada 1/Mac-Usp',
      nextStopTime: 5,
      progress: 30,
      turnDirection: 'straight'
    },
    {
      instruction: 'Vire à esquerda na Alameda dos Maracatins',
      nextStop: 'Parque Ibirapuera',
      nextStopTime: 8,
      progress: 10,
      turnDirection: 'left'
    }
  ];

  const currentInstruction = navigationSteps[currentStep] || navigationSteps[0];

  // Simular contagem regressiva do tempo (mock - atualiza a cada segundo para demonstração)
  useEffect(() => {
    const interval = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 0) {
          // Avançar para próximo step quando tempo acabar
          if (currentStep < navigationSteps.length - 1) {
            setCurrentStep((prevStep) => prevStep + 1);
            return 18; // Resetar tempo para próximo step
          }
          return 0;
        }
        return prev - 1;
      });
    }, 1000); // Atualizar a cada segundo para demonstração (em produção seria a cada minuto)

    return () => clearInterval(interval);
  }, [currentStep]);

  const handleReportBarrier = (reporte) => {
    console.log('Barreira reportada:', reporte);
    // Aqui você salvaria o reporte no backend
  };

  const getTurnIcon = (direction) => {
    switch (direction) {
      case 'right':
        return 'turn_right';
      case 'left':
        return 'turn_left';
      case 'straight':
        return 'straight';
      default:
        return 'navigation';
    }
  };

  return (
    <div className="relative h-screen w-full overflow-hidden bg-white">
      {/* Header */}
      <header className="absolute top-0 left-0 right-0 z-20 flex items-center justify-between bg-white/90 backdrop-blur-sm px-4 py-3">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center justify-center rounded-full bg-white p-2 shadow-md"
        >
          <span className="material-symbols-outlined text-gray-700">my_location</span>
        </button>
        <div className="flex flex-col items-center">
          <span className="text-xs text-gray-600">Tempo restante</span>
          <span className="text-lg font-bold text-gray-900">
            {timeRemaining > 0 ? `${timeRemaining} min` : '0 min'}
          </span>
        </div>
        <button
          onClick={() => navigate('/')}
          className="flex items-center justify-center rounded-full bg-white p-2 shadow-md"
        >
          <span className="material-symbols-outlined text-gray-700">close</span>
        </button>
      </header>

      {/* Mapa */}
      <div className="absolute inset-0 z-0">
        <Map showRealtime={true} />
      </div>

      {/* Banner de chegada (mock) */}
      {currentStep === navigationSteps.length - 1 && timeRemaining < 2 && (
        <div className="absolute top-20 right-4 z-30 rounded-lg border-2 border-green-500 bg-green-50 px-4 py-2 shadow-lg">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-green-600">check_circle</span>
            <span className="text-sm font-medium text-green-900">Chegou ao ponto!</span>
          </div>
        </div>
      )}

      {/* Card de Instruções */}
      <div className="absolute bottom-0 left-0 right-0 z-20 rounded-t-3xl bg-white shadow-2xl">
        <div className="p-6 space-y-4">
          {/* Instrução Principal */}
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-100">
                <span className="material-symbols-outlined text-3xl text-blue-600">
                  {getTurnIcon(currentInstruction.turnDirection)}
                </span>
              </div>
            </div>
            <div className="flex-1">
              <p className="text-xl font-bold text-gray-900">
                {currentInstruction.instruction}
              </p>
            </div>
          </div>

          {/* Separador */}
          <div className="h-px bg-gray-200"></div>

          {/* Próxima Parada */}
          <div className="space-y-2">
            <p className="text-xs text-gray-500">Próxima parada</p>
            <div className="flex items-center justify-between">
              <p className="text-base font-semibold text-gray-900">
                {currentInstruction.nextStop}
              </p>
              <p className="text-sm font-medium text-blue-600">
                {currentInstruction.nextStopTime} min
              </p>
            </div>
            {/* Barra de Progresso */}
            <div className="h-2 w-full rounded-full bg-gray-200">
              <div
                className="h-full rounded-full bg-blue-600 transition-all duration-300"
                style={{ width: `${currentInstruction.progress}%` }}
              ></div>
            </div>
          </div>

          {/* Botões de Ação */}
          <div className="flex gap-3 pt-2">
            <button
              onClick={() => setShowReportBarrier(true)}
              className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 flex items-center justify-center gap-2"
            >
              <span className="material-symbols-outlined text-lg">report</span>
              <span>Reportar</span>
            </button>
            <button
              onClick={() => setAudioEnabled(!audioEnabled)}
              className={`flex-1 rounded-lg px-4 py-3 text-sm font-medium flex items-center justify-center gap-2 ${
                audioEnabled
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <span className="material-symbols-outlined text-lg">
                {audioEnabled ? 'volume_up' : 'volume_off'}
              </span>
              <span>Áudio</span>
            </button>
          </div>
        </div>
      </div>

      {/* Modal Reportar Barreira */}
      <ReportBarrier
        isOpen={showReportBarrier}
        onClose={() => setShowReportBarrier(false)}
        onReport={handleReportBarrier}
      />
    </div>
  );
}

