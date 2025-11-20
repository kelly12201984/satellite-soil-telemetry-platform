import { useEffect, useState } from 'react';
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
    <div className="p-3 border rounded-lg bg-white">
      <div className="text-sm text-gray-500">{title}</div>
      <div className="text-2xl font-semibold">{value}</div>
    </div>
  );
}

export default function Dashboard() {
  const [sp, setSp] = useSearchParams();
  const [activeChart, setActiveChart] = useState<'moisture' | 'temperature'>('moisture');

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

  const hasDevices = summary?.devices_needing_attention?.length > 0;
  const hasReadings = summary?.last_reading_at != null;

  return (
    <div className="space-y-3 p-4 max-w-7xl mx-auto">
      {/* Header - logo only, no "Olho no Solo" */}
      <div className="flex items-center gap-3">
        <img src="/BRSense_logo.png" alt="BR Sense logo" className="h-10 w-auto" />
        <h1 className="text-3xl font-bold text-gray-900 leading-tight">BR Sense</h1>
      </div>

      {/* Filter Bar - Only farm selector + time range */}
      <FilterBar />

      {/* Map Section */}
      <DeviceMap
        onPick={(id) => {
          sp.set('devices', id);
          setSp(sp, { replace: true });
          document.getElementById('charts')?.scrollIntoView({ behavior: 'smooth' });
        }}
      />

      {/* Stats Cards - 4 cards, removed "Devices needing attention" duplicate */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        {isLoading ? (
          <>
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="p-3 border rounded-lg bg-white animate-pulse">
                <div className="h-4 bg-gray-200 rounded mb-2"></div>
                <div className="h-8 bg-gray-200 rounded"></div>
              </div>
            ))}
          </>
        ) : (
          <>
            <Kpi
              title="Avg Moisture"
              value={hasReadings ? `${summary?.avg_moisture?.toFixed?.(1) ?? '–'} %` : '–'}
            />
            <Kpi
              title="Avg Temp"
              value={hasReadings ? `${summary?.avg_temp?.toFixed?.(1) ?? '–'} °C` : '–'}
            />
            <Kpi
              title="Last Reading"
              value={summary?.last_reading_at ? timeAgo(summary.last_reading_at) : (hasDevices ? 'No recent readings' : 'No probes registered')}
            />
            <Kpi
              title="Active Devices"
              value={hasDevices ? `${summary?.devices_needing_attention?.length ?? 0}` : '0'}
            />
          </>
        )}
      </div>

      {/* Main row - Device list left, Charts right */}
      <div className="grid md:grid-cols-3 gap-3" id="charts">
        {/* Device List - Left column */}
        <DevicesCard
          onPick={(id) => {
            sp.set('devices', id);
            setSp(sp, { replace: true });
            document.getElementById('charts')?.scrollIntoView({ behavior: 'smooth' });
          }}
        />

        {/* Charts - Right 2 columns */}
        <div className="md:col-span-2">
          {activeChart === 'moisture' ? (
            <MoistureChart
              q={q}
              onToggle={() => setActiveChart('temperature')}
            />
          ) : (
            <TemperatureChart
              q={q}
              onToggle={() => setActiveChart('moisture')}
            />
          )}
        </div>
      </div>
    </div>
  );
}
