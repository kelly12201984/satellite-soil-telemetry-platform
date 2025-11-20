import { AttentionDevice, DeviceStatus, useAttention } from '@/api/hooks';

// Global status color rules:
// Blue = too wet, Green = optimal, Yellow = irrigate soon, Red = irrigate now, Gray = offline/stale
function statusColor(s: DeviceStatus): string {
  switch (s) {
    case 'red': return 'bg-red-500';  // Irrigate now
    case 'amber': return 'bg-yellow-500';  // Irrigate soon (using yellow per global rules)
    case 'green': return 'bg-green-500';  // Optimal
    case 'blue': return 'bg-blue-500';  // Too wet
    case 'stale':
    case 'offline':
    case 'gray': return 'bg-gray-400';  // Offline/stale
    default: return 'bg-gray-400';
  }
}

// Sorting priority: RED → YELLOW → GRAY → BLUE → GREEN
function statusPriority(s: DeviceStatus): number {
  switch (s) {
    case 'red': return 1;
    case 'amber': return 2;  // Yellow/amber
    case 'stale':
    case 'offline':
    case 'gray': return 3;
    case 'blue': return 4;
    case 'green': return 5;
    default: return 6;
  }
}

function BatteryBars({ hint }: { hint: string }) {
  // 4 bars = OK, 2 bars = Low, 1 bar + outline = Critical
  if (hint === 'critical') {
    return (
      <span className="flex gap-0.5 items-center">
        <span className="w-1 h-3 bg-red-500 border border-red-700 rounded"></span>
        <span className="w-1 h-3 bg-gray-300 rounded"></span>
        <span className="w-1 h-3 bg-gray-300 rounded"></span>
        <span className="w-1 h-3 bg-gray-300 rounded"></span>
      </span>
    );
  }
  if (hint === 'low') {
    return (
      <span className="flex gap-0.5 items-center">
        <span className="w-1 h-3 bg-amber-500 rounded"></span>
        <span className="w-1 h-3 bg-amber-500 rounded"></span>
        <span className="w-1 h-3 bg-gray-300 rounded"></span>
        <span className="w-1 h-3 bg-gray-300 rounded"></span>
      </span>
    );
  }
  // OK (4 bars) or unknown
  return (
    <span className="flex gap-0.5 items-center">
      <span className="w-1 h-3 bg-green-500 rounded"></span>
      <span className="w-1 h-3 bg-green-500 rounded"></span>
      <span className="w-1 h-3 bg-green-500 rounded"></span>
      <span className="w-1 h-3 bg-green-500 rounded"></span>
    </span>
  );
}

export function DevicesCard({ onPick }: { onPick: (id: string) => void }) {
  const { data = [], isLoading } = useAttention();

  if (isLoading) {
    return (
      <div className="p-3 border rounded-lg bg-white">
        <div className="font-semibold mb-2">Irrigation Alerts</div>
        <div className="animate-pulse text-gray-400 text-sm">Loading devices…</div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="p-3 border rounded-lg bg-white">
        <div className="font-semibold mb-2">Irrigation Alerts</div>
        <div className="text-gray-400 text-sm">No devices found</div>
      </div>
    );
  }

  // Filter: Only show red, yellow (amber), or gray in alerts (never green or blue)
  // Sort: RED → YELLOW → GRAY → BLUE → GREEN
  const sortedData = [...data]
    .filter((d: AttentionDevice) => {
      const s = d.status as DeviceStatus;
      return s === 'red' || s === 'amber' || s === 'stale' || s === 'offline' || s === 'gray';
    })
    .sort((a, b) => {
      return statusPriority(a.status as DeviceStatus) - statusPriority(b.status as DeviceStatus);
    });

  if (sortedData.length === 0) {
    return (
      <div className="p-3 border rounded-lg bg-white">
        <div className="font-semibold mb-2">Irrigation Alerts</div>
        <div className="text-gray-400 text-sm">No alerts - all probes optimal</div>
      </div>
    );
  }

  return (
    <div className="p-3 border rounded-lg bg-white">
      <div className="font-semibold mb-3 text-gray-900">Irrigation Alerts</div>
      <ul className="divide-y divide-gray-200">
        {sortedData.map((d: AttentionDevice) => (
          <li
            key={d.device_id}
            className="py-2 flex items-center justify-between cursor-pointer hover:bg-gray-50 transition-colors"
            onClick={() => onPick(String(d.device_id))}
          >
            <div className="flex items-center gap-2 flex-1 min-w-0">
              <span className={`h-3 w-3 rounded-full flex-shrink-0 ${statusColor(d.status as DeviceStatus)}`} />
              <span className="font-medium text-gray-900 truncate text-sm">{d.alias}</span>
              <BatteryBars hint={d.battery_hint || 'unknown'} />
              <span className="text-xs text-gray-500 whitespace-nowrap ml-auto">{d.last_seen}</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

