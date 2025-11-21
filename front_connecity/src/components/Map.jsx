import { useEffect, useState, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, CircleMarker, Polyline } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import api from '../services/api';

// Fix para ícones padrão do Leaflet
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
import iconRetina from 'leaflet/dist/images/marker-icon-2x.png';

let DefaultIcon = L.Icon.Default;

if (typeof window !== 'undefined') {
  delete L.Icon.Default.prototype._getIconUrl;
  DefaultIcon = L.Icon.Default.mergeOptions({
    iconRetinaUrl: iconRetina,
    iconUrl: icon,
    shadowUrl: iconShadow,
  });
}

// Componente para ajustar o mapa quando os marcadores mudam
function MapBounds({ fromNode, toNode, routeCoordinates }) {
  const map = useMap();

  useEffect(() => {
    // Se houver coordenadas da rota, ajustar para mostrar toda a rota
    if (routeCoordinates && routeCoordinates.length > 0) {
      const bounds = L.latLngBounds(routeCoordinates);
      map.fitBounds(bounds, { padding: [50, 50] });
    } else if (fromNode && toNode) {
      const bounds = L.latLngBounds([
        [fromNode.lat, fromNode.lon],
        [toNode.lat, toNode.lon]
      ]);
      map.fitBounds(bounds, { padding: [50, 50] });
    } else if (fromNode) {
      map.setView([fromNode.lat, fromNode.lon], 15);
    } else if (toNode) {
      map.setView([toNode.lat, toNode.lon], 15);
    }
  }, [fromNode, toNode, routeCoordinates, map]);

  return null;
}

export default function Map({ fromNode, toNode, routePath = null, routeDetails = null, showRealtime = false, codigoLinha = null }) {
  // Coordenadas padrão (São Paulo)
  const defaultCenter = [-23.5505, -46.6333];
  const defaultZoom = 12;
  
  // Estado para dados em tempo real
  const [veiculos, setVeiculos] = useState([]);
  const [previsoes, setPrevisoes] = useState([]);
  const [loadingRealtime, setLoadingRealtime] = useState(false);
  const [routeCoordinates, setRouteCoordinates] = useState([]);
  const [routeSegments, setRouteSegments] = useState([]);

  // Criar ícones customizados (usando SVG inline para cores diferentes)
  const originIcon = new L.DivIcon({
    className: 'custom-marker',
    html: `<div style="background-color: #ef4444; width: 30px; height: 30px; border-radius: 50% 50% 50% 0; transform: rotate(-45deg); border: 3px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>`,
    iconSize: [30, 30],
    iconAnchor: [15, 30],
  });

  const destinationIcon = new L.DivIcon({
    className: 'custom-marker',
    html: `<div style="background-color: #3b82f6; width: 30px; height: 30px; border-radius: 50% 50% 50% 0; transform: rotate(-45deg); border: 3px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>`,
    iconSize: [30, 30],
    iconAnchor: [15, 30],
  });

  // Ícone para ônibus em tempo real
  const busIcon = new L.DivIcon({
    className: 'custom-marker',
    html: `<div style="background-color: #10b981; width: 24px; height: 24px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 12px;">🚌</div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });

  // Buscar posição dos veículos em tempo real
  useEffect(() => {
    if (!showRealtime) {
      setVeiculos([]);
      return;
    }

    const fetchPosicoes = async () => {
      setLoadingRealtime(true);
      try {
        const data = await api.obterPosicaoVeiculos(codigoLinha);
        
        // A estrutura de dados varia dependendo se codigoLinha foi fornecido:
        // - Com codigoLinha: { hr: "...", vs: [...] }
        // - Sem codigoLinha: { hr: "...", l: [{ vs: [...] }] }
        let veiculosList = [];
        
        if (data) {
          if (data.vs && Array.isArray(data.vs)) {
            // Caso 1: codigoLinha fornecido - vs está diretamente no objeto
            veiculosList = data.vs;
          } else if (data.l && Array.isArray(data.l)) {
            // Caso 2: codigoLinha não fornecido - vs está dentro de cada item em l
            veiculosList = data.l.flatMap(linha => linha.vs || []);
          }
        }
        
        // Filtrar veículos com coordenadas válidas
        veiculosList = veiculosList.filter(v => 
          v && 
          typeof v.py === 'number' && 
          typeof v.px === 'number' &&
          !isNaN(v.py) && 
          !isNaN(v.px)
        );
        
        setVeiculos(veiculosList);
      } catch (error) {
        console.error('Erro ao buscar posições dos veículos:', error);
        // Não limpar veiculos em caso de erro, manter última posição conhecida
      } finally {
        setLoadingRealtime(false);
      }
    };

    // Buscar imediatamente
    fetchPosicoes();

    // Atualizar a cada 30 segundos
    const interval = setInterval(fetchPosicoes, 30000);

    return () => clearInterval(interval);
  }, [showRealtime, codigoLinha]);

  // Buscar coordenadas da rota quando routePath ou routeDetails mudarem
  useEffect(() => {
    if (!routePath || routePath.length === 0) {
      setRouteCoordinates([]);
      setRouteSegments([]);
      return;
    }

    // Se routeDetails estiver disponível, usar coordenadas dos steps
    if (routeDetails && routeDetails.steps) {
      const coordinates = [];
      const segments = [];
      
      routeDetails.steps.forEach(step => {
        if (step.segments && step.segments.length > 0) {
          // Agrupar segmentos por modo de transporte
          const segmentCoords = [];
          step.segments.forEach(segment => {
            if (segment.from_lat && segment.from_lon) {
              segmentCoords.push([segment.from_lat, segment.from_lon]);
            }
            if (segment.to_lat && segment.to_lon) {
              segmentCoords.push([segment.to_lat, segment.to_lon]);
            }
          });
          
          if (segmentCoords.length > 0) {
            segments.push({
              coordinates: segmentCoords,
              mode: step.mode || 'pe',
              color: getModeColor(step.mode || 'pe')
            });
            coordinates.push(...segmentCoords);
          }
        } else if (step.from_lat && step.from_lon && step.to_lat && step.to_lon) {
          // Fallback: usar coordenadas diretas do step
          const stepCoords = [
            [step.from_lat, step.from_lon],
            [step.to_lat, step.to_lon]
          ];
          segments.push({
            coordinates: stepCoords,
            mode: step.mode || 'pe',
            color: getModeColor(step.mode || 'pe')
          });
          coordinates.push(...stepCoords);
        }
      });
      
      // Remover duplicatas consecutivas
      const uniqueCoords = coordinates.filter((coord, index) => {
        if (index === 0) return true;
        const prev = coordinates[index - 1];
        return coord[0] !== prev[0] || coord[1] !== prev[1];
      });
      
      setRouteCoordinates(uniqueCoords);
      setRouteSegments(segments);
    } else {
      // Fallback: buscar coordenadas dos nós via API
      const fetchCoordinates = async () => {
        try {
          const coords = [];
          for (const nodeId of routePath) {
            try {
              const nodes = await api.searchNodes(nodeId);
              if (nodes && nodes.length > 0) {
                const node = nodes[0];
                if (node.lat && node.lon) {
                  coords.push([node.lat, node.lon]);
                }
              }
            } catch (error) {
              console.warn(`Erro ao buscar coordenadas do nó ${nodeId}:`, error);
            }
          }
          setRouteCoordinates(coords);
          // Criar segmento único com cor padrão
          if (coords.length > 0) {
            setRouteSegments([{
              coordinates: coords,
              mode: 'pe',
              color: getModeColor('pe')
            }]);
          }
        } catch (error) {
          console.error('Erro ao buscar coordenadas da rota:', error);
        }
      };
      
      fetchCoordinates();
    }
  }, [routePath, routeDetails]);

  // Função para obter cor baseada no modo de transporte
  const getModeColor = (mode) => {
    const modeColors = {
      'onibus': '#FF6600',      // Laranja
      'bus': '#FF6600',
      'metro': '#0066CC',       // Azul
      'subway': '#0066CC',
      'trem': '#CC0066',        // Roxo
      'train': '#CC0066',
      'pe': '#00CC66',          // Verde
      'walk': '#00CC66',
      'default': '#0d80f2'      // Azul padrão
    };
    return modeColors[mode?.toLowerCase()] || modeColors['default'];
  };

  // Buscar previsões de chegada se houver paradas na rota
  useEffect(() => {
    if (!showRealtime || !routePath || routePath.length === 0) {
      setPrevisoes([]);
      return;
    }

    // Buscar previsões para paradas relevantes (simplificado - pode ser melhorado)
    // Por enquanto, apenas busca se houver código de parada nos nós
  }, [showRealtime, routePath]);

  return (
    <MapContainer
      center={defaultCenter}
      zoom={defaultZoom}
      style={{ height: '100%', width: '100%', zIndex: 0 }}
      scrollWheelZoom={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      
      <MapBounds fromNode={fromNode} toNode={toNode} routeCoordinates={routeCoordinates} />

      {/* Desenhar rota no mapa */}
      {routeSegments.length > 0 && routeSegments.map((segment, index) => (
        <Polyline
          key={`route-segment-${index}`}
          positions={segment.coordinates}
          color={segment.color}
          weight={5}
          opacity={0.7}
          smoothFactor={1}
        />
      ))}
      
      {/* Desenhar rota única se não houver segmentos (fallback) */}
      {routeSegments.length === 0 && routeCoordinates.length > 0 && (
        <Polyline
          positions={routeCoordinates}
          color="#0d80f2"
          weight={5}
          opacity={0.7}
          smoothFactor={1}
        />
      )}

      {/* Marcadores intermediários para paradas importantes */}
      {routeDetails && routeDetails.steps && routeDetails.steps.map((step, index) => {
        // Mostrar marcador apenas para paradas de transporte público
        if (step.mode && step.mode !== 'pe' && step.mode !== 'walk' && step.to_lat && step.to_lon) {
          return (
            <CircleMarker
              key={`stop-${index}`}
              center={[step.to_lat, step.to_lon]}
              radius={6}
              fillColor={getModeColor(step.mode)}
              color="#ffffff"
              weight={2}
              opacity={1}
              fillOpacity={0.8}
            >
              <Popup>
                <div>
                  <strong>{step.to_name || step.to}</strong>
                  <br />
                  <small>Modo: {step.mode}</small>
                  {step.time_min > 0 && (
                    <>
                      <br />
                      <small>Tempo: {Math.round(step.time_min)} min</small>
                    </>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          );
        }
        return null;
      })}

      {fromNode && (
        <Marker position={[fromNode.lat, fromNode.lon]} icon={originIcon}>
          <Popup>
            <div>
              <strong>Origem</strong>
              <br />
              {fromNode.name || fromNode.id}
            </div>
          </Popup>
        </Marker>
      )}

      {toNode && (
        <Marker position={[toNode.lat, toNode.lon]} icon={destinationIcon}>
          <Popup>
            <div>
              <strong>Destino</strong>
              <br />
              {toNode.name || toNode.id}
            </div>
          </Popup>
        </Marker>
      )}

      {/* Ônibus em tempo real */}
      {showRealtime && veiculos.length > 0 && veiculos.map((veiculo, index) => {
        // Validar coordenadas antes de renderizar
        if (!veiculo || typeof veiculo.py !== 'number' || typeof veiculo.px !== 'number') {
          return null;
        }
        
        return (
          <Marker
            key={`bus-${veiculo.p || index}-${index}`}
            position={[veiculo.py, veiculo.px]}
            icon={busIcon}
          >
            <Popup>
              <div>
                <strong>Ônibus {veiculo.p || 'N/A'}</strong>
                <br />
                {veiculo.a ? '✅ Acessível' : '❌ Não acessível'}
                <br />
                <small>Atualizado em tempo real</small>
              </div>
            </Popup>
          </Marker>
        );
      })}

    </MapContainer>
  );
}

