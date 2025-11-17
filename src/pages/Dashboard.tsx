import { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { FilterBar } from '@/components/FilterBar';
import { useSummary } from '@/api/hooks';
import { DevicesCard } from '@/components/DevicesCard';
import { MoistureChart } from '@/components/MoistureChart';
import { TemperatureChart } from '@/components/TemperatureChart';
import { DeviceMap } from '@/components/DeviceMap';
import { presetToRange } from '@/lib/time';

function timeAgo(iso: string) {
  const d = (Date.now() - Date.parse(iso)) / 60000;
  return d < 60 ? `${Math.floor(d)}m ago` : `${Math.floor(d / 60)}h ago`;
}

function Kpi({ title, value }: { title: string; value: string }) {
  return (
    <div className="p-4 border rounded-lg bg-white">
      <div className="text-sm text-gray-500">{title}</div>
      <div className="text-2xl font-semibold">{value}</div>
    </div>
  );
}

export default function Dashboard() {
  const [sp, setSp] = useSearchParams();

  // Initialize default params if missing
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

  const q = {
    from: sp.get('from') || undefined,
    to: sp.get('to') || undefined,
    'device_ids[]': sp.get('devices')?.split(',').filter(Boolean).map(Number),
    'depths[]': sp.get('depths')?.split(',').filter(Boolean).map(Number),
  };

  const { data: summary, isLoading } = useSummary(q);

  return (
    <div className="space-y-4 p-4 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900">🌱 Olho no Solo</h1>

      <FilterBar />

      {/* Map with device pins */}
      <DeviceMap
        onPick={(id) => {
          sp.set('devices', id);
          setSp(sp, { replace: true });
          document.getElementById('charts')?.scrollIntoView({ behavior: 'smooth' });
        }}
      />

      {/* Attention Card (small, left) + KPI tiles */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        {/* Small attention card */}
        <div className="p-4 border rounded-lg bg-white">
          <div className="text-sm text-gray-500 mb-1">Devices needing attention</div>
          {isLoading ? (
            <div className="h-8 bg-gray-200 rounded animate-pulse"></div>
          ) : (
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-semibold text-red-600">
                {summary?.devices_needing_attention?.filter((d: any) => d.status === 'red').length ?? 0}
              </span>
              {summary?.devices_needing_attention?.some((d: any) => d.status === 'amber') && (
                <span className="text-sm text-amber-600 font-medium">
                  +{summary.devices_needing_attention.filter((d: any) => d.status === 'amber').length}
                </span>
              )}
              <button
                onClick={() => {
                  document.getElementById('charts')?.scrollIntoView({ behavior: 'smooth' });
                }}
                className="text-xs text-blue-600 hover:underline ml-auto"
              >
                View →
              </button>
            </div>
          )}
        </div>

        {/* KPI tiles */}
        {isLoading ? (
          <>
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="p-4 border rounded-lg bg-white animate-pulse">
                <div className="h-4 bg-gray-200 rounded mb-2"></div>
                <div className="h-8 bg-gray-200 rounded"></div>
              </div>
            ))}
          </>
        ) : (
          <>
            <Kpi
              title="Avg Moisture"
              value={`${summary?.avg_moisture?.toFixed?.(1) ?? '–'} %`}
            />
            <Kpi
              title="Avg Temp"
              value={`${summary?.avg_temp?.toFixed?.(1) ?? '–'} °C`}
            />
            <Kpi
              title="Last Reading"
              value={summary?.last_reading_at ? timeAgo(summary.last_reading_at) : '–'}
            />
            <Kpi
              title="Active Devices"
              value={`${summary?.devices_needing_attention?.length ?? 0}`}
            />
          </>
        )}
      </div>

      {/* Main row */}
      <div className="grid md:grid-cols-3 gap-4" id="charts">
        <div className="md:col-span-2 space-y-4">
          <MoistureChart q={q} />
          <TemperatureChart q={q} />
        </div>
        <DevicesCard
          onPick={(id) => {
            sp.set('devices', id);
            setSp(sp, { replace: true });
            document.getElementById('charts')?.scrollIntoView({ behavior: 'smooth' });
          }}
        />
      </div>
    </div>
  );
}

