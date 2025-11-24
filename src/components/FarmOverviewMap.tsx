import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Farm, DeviceStatus } from '@/api/hooks';

function statusToColor(status: DeviceStatus): string {
  switch (status) {
    case 'red': return '#dc2626';    // red-600
    case 'amber': return '#d97706';  // amber-600
    case 'green': return '#059669';  // emerald-600
    case 'blue': return '#2563eb';   // blue-600
    case 'stale':
    case 'offline':
    case 'gray':
    default: return '#6b7280';       // gray-500
  }
}

function createFarmIcon(color: string, deviceCount: number): L.DivIcon {
  return L.divIcon({
    className: 'farm-marker',
    html: `<div style="
      width: 40px;
      height: 40px;
      background-color: ${color};
      border: 3px solid white;
      border-radius: 50%;
      box-shadow: 0 3px 8px rgba(0,0,0,0.3);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-weight: 600;
      font-size: 14px;
    ">${deviceCount}</div>`,
    iconSize: [40, 40],
    iconAnchor: [20, 20],
  });
}

function MapCenter({ farms }: { farms: Farm[] }) {
  const map = useMap();

  useEffect(() => {
    const validFarms = farms.filter(f => f.lat != null && f.lon != null);
    if (validFarms.length === 0) return;

    if (validFarms.length === 1) {
      map.setView([validFarms[0].lat!, validFarms[0].lon!], 10);
    } else {
      const bounds = L.latLngBounds(
        validFarms.map(f => [f.lat!, f.lon!] as [number, number])
      );
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [map, farms]);

  return null;
}

interface FarmOverviewMapProps {
  farms: Farm[];
}

export function FarmOverviewMap({ farms }: FarmOverviewMapProps) {
  const navigate = useNavigate();

  const farmsWithLocation = farms.filter(f => f.lat != null && f.lon != null);
  const defaultCenter: [number, number] = [-23.5505, -46.6333]; // São Paulo
  const defaultZoom = 6;

  return (
    <div className="rounded-xl overflow-hidden border-2 border-stone-200 shadow-sm">
      {farmsWithLocation.length === 0 ? (
        <div className="h-72 bg-stone-100 flex items-center justify-center">
          <div className="text-stone-500">Waiting for farm location data...</div>
        </div>
      ) : (
        <MapContainer
          center={defaultCenter}
          zoom={defaultZoom}
          style={{ height: '288px', width: '100%' }}
          scrollWheelZoom={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <MapCenter farms={farmsWithLocation} />

          {farmsWithLocation.map((farm) => {
            const color = statusToColor(farm.status);
            const icon = createFarmIcon(color, farm.device_count);

            return (
              <Marker
                key={farm.id}
                position={[farm.lat!, farm.lon!]}
                icon={icon}
                eventHandlers={{
                  click: () => navigate(`/readings/farm/${farm.id}`),
                }}
              >
                <Popup>
                  <div className="text-sm min-w-[140px]">
                    <div className="font-semibold text-stone-800 mb-1">{farm.name}</div>
                    <div className="text-stone-600">{farm.device_count} devices</div>
                    {farm.last_reading && (
                      <div className="text-stone-500 text-xs mt-1">Last: {farm.last_reading}</div>
                    )}
                    <button
                      onClick={() => navigate(`/readings/farm/${farm.id}`)}
                      className="mt-2 text-xs text-emerald-600 hover:underline font-medium"
                    >
                      View farm details
                    </button>
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>
      )}
    </div>
  );
}
