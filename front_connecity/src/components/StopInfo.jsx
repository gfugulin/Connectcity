/**
 * Componente para exibir informações de parada com previsão de chegada
 */
import { useState, useEffect } from 'react';
import api from '../services/api';

export default function StopInfo({ codigoParada, nomeParada, lat, lon }) {
  const [previsao, setPrevisao] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!codigoParada) return;

    const fetchPrevisao = async () => {
      setLoading(true);
      setError('');
      try {
        const data = await api.obterPrevisaoPorParada(codigoParada);
        setPrevisao(data);
      } catch (err) {
        setError('Erro ao buscar previsão');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchPrevisao();

    // Atualizar a cada 30 segundos
    const interval = setInterval(fetchPrevisao, 30000);
    return () => clearInterval(interval);
  }, [codigoParada]);

  if (!codigoParada) return null;

  return (
    <div className="bg-white rounded-lg p-4 shadow-md mb-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-bold text-lg">{nomeParada || `Parada ${codigoParada}`}</h3>
        {loading && <span className="text-sm text-gray-500">Atualizando...</span>}
      </div>

      {error && (
        <div className="text-red-500 text-sm mb-2">{error}</div>
      )}

      {previsao && previsao.p && previsao.p.l && (
        <div className="space-y-3">
          {previsao.p.l.map((linha, idx) => (
            <div key={idx} className="border-b pb-2 last:border-b-0">
              <div className="flex items-center justify-between mb-1">
                <div>
                  <span className="font-semibold text-blue-600">{linha.c}</span>
                  <span className="text-sm text-gray-600 ml-2">
                    {linha.lt0} → {linha.lt1}
                  </span>
                </div>
                <span className="text-sm text-gray-500">
                  {linha.qv} {linha.qv === 1 ? 'ônibus' : 'ônibus'}
                </span>
              </div>

              {linha.vs && linha.vs.length > 0 && (
                <div className="ml-4 space-y-1">
                  {linha.vs.map((veiculo, vIdx) => (
                    <div key={vIdx} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <span className="font-mono">🚌 {veiculo.p}</span>
                        {veiculo.a && (
                          <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded">
                            Acessível
                          </span>
                        )}
                      </div>
                      <span className="font-semibold text-blue-600">
                        {veiculo.t}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {(!linha.vs || linha.vs.length === 0) && (
                <div className="text-sm text-gray-500 ml-4">
                  Nenhum ônibus previsto no momento
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {previsao && previsao.hr && (
        <div className="text-xs text-gray-400 mt-2">
          Última atualização: {previsao.hr}
        </div>
      )}
    </div>
  );
}

