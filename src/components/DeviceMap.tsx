import { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useDevices } from '@/api/hooks';

// Fix default marker icons for Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

type Status = 'red' | 'amber' | 'green' | 'blue' | 'stale' | 'offline' | 'gray';

function statusToColor(status: Status): string {
  switch (status) {
    case 'red': return '#ef4444'; // red-500
    case 'amber': return '#f59e0b'; // amber-500
    case 'green': return '#10b981'; // green-500
    case 'blue': return '#3b82f6'; // blue-500
    case 'stale': return '#facc15'; // yellow-400
    case 'offline': return '#9ca3af'; // gray-400
    case 'gray': return '#d1d5db'; // gray-300
    default: return '#d1d5db';
  }
}

function createCustomIcon(color: string): L.DivIcon {
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="
      width: 24px;
      height: 24px;
      background-color: ${color};
      border: 2px solid white;
      border-radius: 50%;
      box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    "></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
}

// Component to center map on devices
function MapCenter({ devices }: { devices: any[] }) {
  const map = useMap();
  
  useEffect(() => {
    const validDevices = devices.filter(d => d.lat != null && d.lon != null);
    if (validDevices.length === 0) return;
    
    if (validDevices.length === 1) {
      map.setView([validDevices[0].lat, validDevices[0].lon], 13);
    } else {
      const bounds = L.latLngBounds(
        validDevices.map(d => [d.lat, d.lon] as [number, number])
      );
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [map, devices]);
  
  return null;
}

interface DeviceMapProps {
  onPick: (deviceId: string) => void;
}

export function DeviceMap({ onPick }: DeviceMapProps) {
  const { data: devices = [], isLoading } = useDevices();
  
  // Filter devices that have coordinates (lat/lon from device_config, or use farm centroid if available)
  const devicesWithLocation = (devices as any[]).filter(
    d => d.lat != null && d.lon != null
  );
  
  // Default center (Brazil - São Paulo region)
  const defaultCenter: [number, number] = [-23.5505, -46.6333];
  const defaultZoom = 6;
  
  if (isLoading) {
    return (
      <div className="h-64 border rounded-lg bg-gray-100 flex items-center justify-center">
        <div className="text-gray-500">Loading map...</div>
      </div>
    );
  }
  
  if (devicesWithLocation.length === 0) {
    return (
      <div className="h-64 border rounded-lg bg-gray-100 flex items-center justify-center">
        <div className="text-gray-500">No devices with location data</div>
      </div>
    );
  }
  
  return (
    <div className="h-64 border rounded-lg overflow-hidden">
      <MapContainer
        center={defaultCenter}
        zoom={defaultZoom}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        <MapCenter devices={devicesWithLocation} />
        
        {devicesWithLocation.map((device: any) => {
          const color = statusToColor(device.status || 'gray');
          const icon = createCustomIcon(color);
          
          return (
            <Marker
              key={device.id}
              position={[device.lat, device.lon]}
              icon={icon}
              eventHandlers={{
                click: () => {
                  onPick(String(device.id));
                },
              }}
            >
              <Popup>
                <div className="text-sm">
                  <div className="font-semibold">{device.alias}</div>
                  <div className="text-gray-600">Status: {device.status}</div>
                  <div className="text-gray-600">Last seen: {device.last_seen}</div>
                  <button
                    onClick={() => onPick(String(device.id))}
                    className="mt-2 text-xs text-blue-600 hover:underline"
                  >
                    View details →
                  </button>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
}

