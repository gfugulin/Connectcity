import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, CircleMarker } from 'react-leaflet';
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
function MapBounds({ fromNode, toNode }) {
  const map = useMap();

  useEffect(() => {
    if (fromNode && toNode) {
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
  }, [fromNode, toNode, map]);

  return null;
}

export default function Map({ fromNode, toNode, routePath = null, showRealtime = false, codigoLinha = null }) {
  // Coordenadas padrão (São Paulo)
  const defaultCenter = [-23.5505, -46.6333];
  const defaultZoom = 12;
  
  // Estado para dados em tempo real
  const [veiculos, setVeiculos] = useState([]);
  const [previsoes, setPrevisoes] = useState([]);
  const [loadingRealtime, setLoadingRealtime] = useState(false);

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
        if (data && data.vs) {
          setVeiculos(data.vs);
        }
      } catch (error) {
        console.error('Erro ao buscar posições dos veículos:', error);
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
      
      <MapBounds fromNode={fromNode} toNode={toNode} />

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
      {showRealtime && veiculos.map((veiculo, index) => (
        <Marker
          key={`bus-${veiculo.p}-${index}`}
          position={[veiculo.py, veiculo.px]}
          icon={busIcon}
        >
          <Popup>
            <div>
              <strong>Ônibus {veiculo.p}</strong>
              <br />
              {veiculo.a ? '✅ Acessível' : '❌ Não acessível'}
              <br />
              <small>Atualizado em tempo real</small>
            </div>
          </Popup>
        </Marker>
      ))}

    </MapContainer>
  );
}

