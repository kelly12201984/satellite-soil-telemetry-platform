import { useAttention } from '@/api/hooks';

type Status = 'red' | 'amber' | 'green' | 'blue' | 'stale' | 'offline' | 'gray';

function statusColor(s: Status): string {
  switch (s) {
    case 'red': return 'bg-red-500';
    case 'amber': return 'bg-amber-500';
    case 'green': return 'bg-green-500';
    case 'blue': return 'bg-blue-500';
    case 'stale': return 'bg-yellow-400';
    case 'offline': return 'bg-gray-400';
    case 'gray': return 'bg-gray-300';
    default: return 'bg-gray-300';
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
  const { data, isLoading } = useAttention();

  if (isLoading) {
    return (
      <div className="p-4 border rounded-lg bg-white">
        <div className="font-semibold mb-2">Irrigation Alerts</div>
        <div className="animate-pulse text-gray-400 text-sm">Loading devices…</div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="p-4 border rounded-lg bg-white">
        <div className="font-semibold mb-2">Irrigation Alerts</div>
        <div className="text-gray-400 text-sm">No devices found</div>
      </div>
    );
  }

  return (
    <div className="p-4 border rounded-lg bg-white">
      <div className="font-semibold mb-3 text-gray-900">Irrigation Alerts</div>
      <ul className="divide-y divide-gray-200">
        {data.map((d: any) => (
          <li
            key={d.device_id}
            className="py-3 flex items-center justify-between cursor-pointer hover:bg-gray-50 transition-colors"
            onClick={() => onPick(String(d.device_id))}
          >
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <span className={`h-3 w-3 rounded-full flex-shrink-0 ${statusColor(d.status as Status)}`} />
              <span className="font-medium text-gray-900 truncate">{d.alias}</span>
              <BatteryBars hint={d.battery_hint || 'unknown'} />
              <span className="text-xs text-gray-500 whitespace-nowrap">Last reading {d.last_seen}</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

