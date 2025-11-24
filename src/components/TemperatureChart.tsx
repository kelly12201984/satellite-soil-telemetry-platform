import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useSearchParams } from 'react-router-dom';
import { presetToRange } from '@/lib/time';
import { TempSeries, useTempSeries } from '@/api/hooks';

export function TemperatureChart({ q, onToggle }: { q: any; onToggle: () => void }) {
  const [sp, setSp] = useSearchParams();
  const { data = [], isLoading } = useTempSeries(q);

  if (isLoading) return (
    <div className="border-2 border-stone-200 rounded-xl p-4 bg-white min-h-[28rem] flex items-center justify-center">
      <div className="text-stone-500">Loading chart data...</div>
    </div>
  );

  if (!data || data.length === 0) return (
    <div className="border-2 border-stone-200 rounded-xl p-4 bg-white min-h-[28rem] flex items-center justify-center">
      <div className="text-stone-500">No temperature data available</div>
    </div>
  );

  // Flatten series to chart rows
  const timeMap = new Map<string, any>();
  const seriesMeta: Array<{ key: string; color: string; device: string }> = [];
  // Warm earthy palette for temperature
  const colors = ['#dc2626', '#ea580c', '#d97706', '#ca8a04', '#65a30d', '#16a34a', '#0d9488', '#0891b2'];

  data.forEach((series: TempSeries, idx: number) => {
    const key = series.device_name;
    seriesMeta.push({
      key,
      color: colors[idx % colors.length],
      device: series.device_name,
    });

    series.points.forEach((point) => {
      if (!timeMap.has(point.t)) {
        timeMap.set(point.t, { t: new Date(point.t).toLocaleString() });
      }
      timeMap.get(point.t)[key] = point.v;
    });
  });

  const rows = Array.from(timeMap.values()).sort((a, b) =>
    new Date(a.t).getTime() - new Date(b.t).getTime()
  );

  const visibleSeries = seriesMeta.slice(0, 8);

  return (
    <div className="border-2 border-stone-200 rounded-xl p-4 bg-white">
      {/* Header with title and toggle */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-stone-800 text-lg">Soil Temperature</h3>
        <button
          onClick={onToggle}
          className="px-4 py-2 text-sm font-medium border-2 border-stone-200 rounded-lg hover:bg-stone-50 transition-colors text-stone-700"
        >
          View Moisture
        </button>
      </div>

      {/* Depth selector */}
      <div className="flex flex-wrap gap-2 mb-4">
        {[10, 20, 30, 40, 50, 60].map(cm => {
          const active = (sp.get('depths') ?? '').split(',').includes(String(cm));
          return (
            <button
              key={cm}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                active
                  ? 'bg-emerald-600 text-white'
                  : 'bg-stone-200 text-stone-700 hover:bg-stone-300'
              }`}
              onClick={() => {
                const list = (sp.get('depths') ?? '').split(',').filter(Boolean);
                const i = list.indexOf(String(cm));
                if (i >= 0) list.splice(i, 1);
                else list.push(String(cm));
                list.length ? sp.set('depths', list.join(',')) : sp.delete('depths');
                setSp(sp, { replace: true });
              }}
            >
              {cm}cm
            </button>
          );
        })}
        <button
          onClick={() => {
            const { from, to } = presetToRange('7d');
            sp.delete('devices');
            sp.delete('depths');
            sp.set('preset', '7d');
            sp.set('from', from);
            sp.set('to', to);
            setSp(sp, { replace: true });
          }}
          className="px-3 py-2 text-sm font-medium border-2 border-stone-300 rounded-lg hover:bg-stone-50 transition-colors text-stone-600"
          title="Reset filters"
        >
          Reset
        </button>
      </div>

      {/* Chart */}
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows}>
            <XAxis dataKey="t" tick={{ fontSize: 11 }} stroke="#78716c" />
            <YAxis domain={[10, 40]} tick={{ fontSize: 11 }} stroke="#78716c" />
            <Tooltip
              contentStyle={{
                borderRadius: '8px',
                border: '2px solid #e7e5e4',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
              }}
            />
            <Legend />
            {visibleSeries.map(s => (
              <Line
                key={s.key}
                dataKey={s.key}
                dot={false}
                stroke={s.color}
                strokeWidth={2}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
        {seriesMeta.length > 8 && (
          <div className="text-xs text-stone-500 mt-2">+ {seriesMeta.length - 8} more series</div>
        )}
      </div>
    </div>
  );
}
