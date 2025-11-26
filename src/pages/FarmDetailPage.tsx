import { useEffect } from 'react';
import { useParams, useSearchParams, Link } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useFarmDetail, useSummary, Device, DeviceStatus } from '@/api/hooks';
import { MoistureChart } from '@/components/MoistureChart';
import { TemperatureChart } from '@/components/TemperatureChart';
import { presetToRange } from '@/lib/time';

// Status color utilities
function statusToColor(status: DeviceStatus): string {
  switch (status) {
    case 'red': return '#dc2626';
    case 'amber': return '#d97706';
    case 'green': return '#059669';
    case 'blue': return '#2563eb';
    case 'stale':
    case 'offline':
    case 'gray':
    default: return '#6b7280';
  }
}

function statusToBgClass(status: DeviceStatus): string {
  switch (status) {
    case 'red': return 'bg-red-500';
    case 'amber': return 'bg-amber-500';
    case 'green': return 'bg-emerald-500';
    case 'blue': return 'bg-blue-500';
    default: return 'bg-gray-400';
  }
}

function statusLabel(status: DeviceStatus): string {
  switch (status) {
    case 'red': return 'Needs Water';
    case 'amber': return 'Monitor';
    case 'green': return 'Optimal';
    case 'blue': return 'Too Wet';
    case 'stale': return 'Stale';
    case 'offline': return 'Offline';
    default: return 'Unknown';
  }
}

function createDeviceIcon(color: string): L.DivIcon {
  return L.divIcon({
    className: 'device-marker',
    html: `<div style="
      width: 28px;
      height: 28px;
      background-color: ${color};
      border: 3px solid white;
      border-radius: 50%;
      box-shadow: 0 2px 6px rgba(0,0,0,0.3);
    "></div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

// Map center component
function MapCenter({ devices }: { devices: Device[] }) {
  const map = useMap();

  useEffect(() => {
    const validDevices = devices.filter(d => d.lat != null && d.lon != null);
    if (validDevices.length === 0) return;

    if (validDevices.length === 1) {
      map.setView([validDevices[0].lat!, validDevices[0].lon!], 14);
    } else {
      const bounds = L.latLngBounds(
        validDevices.map(d => [d.lat!, d.lon!] as [number, number])
      );
      map.fitBounds(bounds, { padding: [40, 40] });
    }
  }, [map, devices]);

  return null;
}

// Farm Map Component
function FarmMap({ devices, onSelectDevice, selectedDeviceId }: {
  devices: Device[];
  onSelectDevice: (id: string) => void;
  selectedDeviceId?: string;
}) {
  const devicesWithLocation = devices.filter(d => d.lat != null && d.lon != null);
  const defaultCenter: [number, number] = [-23.5505, -46.6333];

  return (
    <div className="rounded-xl overflow-hidden border-2 border-stone-200">
      {devicesWithLocation.length === 0 ? (
        <div className="h-56 bg-stone-100 flex items-center justify-center">
          <div className="text-stone-500">Waiting for device GPS data...</div>
        </div>
      ) : (
        <MapContainer
          center={defaultCenter}
          zoom={12}
          style={{ height: '224px', width: '100%' }}
          scrollWheelZoom={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <MapCenter devices={devicesWithLocation} />
          {devicesWithLocation.map((device) => {
            const color = statusToColor(device.status || 'gray');
            const icon = createDeviceIcon(color);
            const isSelected = String(device.id) === selectedDeviceId;

            return (
              <Marker
                key={device.id}
                position={[device.lat!, device.lon!]}
                icon={icon}
                opacity={isSelected ? 1 : 0.8}
                eventHandlers={{
                  click: () => onSelectDevice(String(device.id)),
                }}
              >
                <Popup>
                  <div className="text-sm">
                    <div className="font-semibold">{device.alias}</div>
                    <div className="text-stone-600">{statusLabel(device.status || 'gray')}</div>
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

// KPI Card Component
function KpiCard({ title, value, accent }: { title: string; value: string; accent?: boolean }) {
  return (
    <div className={`p-4 rounded-xl border-2 ${accent ? 'border-red-200 bg-red-50' : 'border-stone-200 bg-white'}`}>
      <div className="text-sm text-stone-500 mb-1">{title}</div>
      <div className={`text-2xl font-semibold ${accent ? 'text-red-700' : 'text-stone-800'}`}>{value}</div>
    </div>
  );
}

// Filter Bar Component
function FilterBar() {
  const [sp, setSp] = useSearchParams();
  const preset = sp.get('preset') ?? '7d';
  const custom = preset === 'custom';

  function setPreset(p: string) {
    const { from, to } = p === 'custom'
      ? { from: sp.get('from') ?? '', to: sp.get('to') ?? '' }
      : presetToRange(p);
    sp.set('preset', p);
    if (!custom) {
      sp.set('from', from);
      sp.set('to', to);
    }
    setSp(sp, { replace: true });
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      {['24h', '7d', '14d', '30d'].map(p => (
        <button
          key={p}
          onClick={() => setPreset(p)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            preset === p
              ? 'bg-emerald-600 text-white'
              : 'bg-stone-200 text-stone-700 hover:bg-stone-300'
          }`}
        >
          {p}
        </button>
      ))}
      <button
        onClick={() => setPreset('custom')}
        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
          preset === 'custom'
            ? 'bg-emerald-600 text-white'
            : 'bg-stone-200 text-stone-700 hover:bg-stone-300'
        }`}
      >
        Custom
      </button>
      {custom && (
        <>
          <input
            type="datetime-local"
            value={sp.get('from') ? new Date(sp.get('from')!).toISOString().slice(0, 16) : ''}
            onChange={e => {
              sp.set('from', new Date(e.target.value).toISOString());
              setSp(sp, { replace: true });
            }}
            className="px-3 py-2 border-2 border-stone-200 rounded-lg bg-white text-sm"
          />
          <input
            type="datetime-local"
            value={sp.get('to') ? new Date(sp.get('to')!).toISOString().slice(0, 16) : ''}
            onChange={e => {
              sp.set('to', new Date(e.target.value).toISOString());
              setSp(sp, { replace: true });
            }}
            className="px-3 py-2 border-2 border-stone-200 rounded-lg bg-white text-sm"
          />
        </>
      )}
    </div>
  );
}

// Device List Component
function DeviceList({ devices, onSelect, selectedId }: {
  devices: Device[];
  onSelect: (id: string) => void;
  selectedId?: string;
}) {
  return (
    <div className="border-2 border-stone-200 rounded-xl bg-white overflow-hidden">
      <div className="px-4 py-3 bg-stone-50 border-b border-stone-200">
        <h3 className="font-semibold text-stone-800">Devices</h3>
      </div>
      <ul className="divide-y divide-stone-100 max-h-96 overflow-y-auto">
        {devices.map(device => {
          const isSelected = String(device.id) === selectedId;
          return (
            <li
              key={device.id}
              onClick={() => onSelect(String(device.id))}
              className={`px-4 py-3 cursor-pointer transition-colors ${
                isSelected ? 'bg-emerald-50' : 'hover:bg-stone-50'
              }`}
            >
              <div className="flex items-center gap-3">
                <span className={`w-3 h-3 rounded-full flex-shrink-0 ${statusToBgClass(device.status || 'gray')}`} />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-stone-800 truncate">{device.alias}</div>
                  <div className="text-xs text-stone-500">{statusLabel(device.status || 'gray')}</div>
                </div>
                {device.moisture30 != null && (
                  <div className="text-sm text-stone-600">{device.moisture30}%</div>
                )}
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

// Main Page Component
export default function FarmDetailPage() {
  const { farmId } = useParams<{ farmId: string }>();
  const [sp, setSp] = useSearchParams();
  // Initialize default time range
  useEffect(() => {
    if (!sp.get('preset') && !sp.get('from')) {
      const preset = '7d';
      const { from, to } = presetToRange(preset);
      sp.set('preset', preset);
      sp.set('from', from);
      sp.set('to', to);
      setSp(sp, { replace: true });
    }
  }, [sp, setSp]);

  const { data: farm, isLoading: farmLoading } = useFarmDetail(farmId || '');

  // Build query for metrics
  const selectedDeviceId = sp.get('devices');
  const deviceIds = farm?.devices.map(d => d.id) || [];
  const q = {
    from: sp.get('from') || undefined,
    to: sp.get('to') || undefined,
    'device_ids[]': selectedDeviceId ? [Number(selectedDeviceId)] : deviceIds,
    'depths[]': sp.get('depths')?.split(',').filter(Boolean).map(Number),
  };

  const { data: summary, isLoading: summaryLoading } = useSummary(q);

  const handleSelectDevice = (id: string) => {
    if (sp.get('devices') === id) {
      sp.delete('devices');
    } else {
      sp.set('devices', id);
    }
    setSp(sp, { replace: true });
  };

  if (farmLoading) {
    return (
      <div className="min-h-screen bg-stone-50 flex items-center justify-center">
        <div className="animate-pulse text-stone-500">Loading farm data...</div>
      </div>
    );
  }

  if (!farm || 'error' in farm) {
    return (
      <div className="min-h-screen bg-stone-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-stone-500 mb-4">Farm not found</div>
          <Link to="/readings" className="text-emerald-600 hover:underline">
            Back to farms
          </Link>
        </div>
      </div>
    );
  }

  const attentionCount = farm.devices.filter(d =>
    ['red', 'amber', 'stale', 'offline'].includes(d.status || '')
  ).length;

  return (
    <div className="min-h-screen bg-stone-50">
      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <Link
            to="/readings"
            className="p-2 rounded-lg hover:bg-stone-200 transition-colors"
            title="Back to farms"
          >
            <svg className="w-6 h-6 text-stone-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-stone-800">{farm.name}</h1>
            <div className="text-sm text-stone-500">{farm.device_count} devices</div>
          </div>
        </div>

        {/* Filter Bar */}
        <div className="mb-6">
          <FilterBar />
        </div>

        {/* Map */}
        <div className="mb-6">
          <FarmMap
            devices={farm.devices}
            onSelectDevice={handleSelectDevice}
            selectedDeviceId={selectedDeviceId || undefined}
          />
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <KpiCard
            title="Avg Moisture"
            value={summaryLoading ? '...' : summary?.avg_moisture ? `${summary.avg_moisture.toFixed(1)}%` : '-'}
          />
          <KpiCard
            title="Avg Temperature"
            value={summaryLoading ? '...' : summary?.avg_temp ? `${summary.avg_temp.toFixed(1)}°C` : '-'}
          />
          <KpiCard
            title="Active Devices"
            value={String(farm.device_count)}
          />
          <KpiCard
            title="Need Attention"
            value={String(attentionCount)}
            accent={attentionCount > 0}
          />
        </div>

        {/* Main Content: Device List + Charts */}
        <div className="grid md:grid-cols-3 gap-6">
          {/* Device List */}
          <div>
            <DeviceList
              devices={farm.devices}
              onSelect={handleSelectDevice}
              selectedId={selectedDeviceId || undefined}
            />
          </div>

          {/* Charts */}
          <div className="md:col-span-2 space-y-4">
            <MoistureChart q={q} />
            <TemperatureChart q={q} />
          </div>
        </div>
      </div>
    </div>
  );
}
