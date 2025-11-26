import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from 'recharts';
import { useSearchParams } from 'react-router-dom';
import { presetToRange } from '@/lib/time';
import { TempSeries, useTempSeries } from '@/api/hooks';

export function TemperatureChart({ q }: { q: any }) {
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
        timeMap.set(point.t, { t: point.t });
      }
      timeMap.get(point.t)[key] = point.v;
    });
  });

  const rows = Array.from(timeMap.values()).sort((a, b) =>
    new Date(a.t).getTime() - new Date(b.t).getTime()
  );

  const visibleSeries = seriesMeta.slice(0, 8);

  const formatTick = (value: string) =>
    new Date(value).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });

  return (
    <div className="border border-[#ede2d3] rounded-2xl p-5 bg-white/95 shadow-sm">
      <h3 className="font-semibold text-stone-800 text-lg mb-4">Soil Temperature</h3>

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
            <CartesianGrid stroke="#f0e7db" vertical={false} />
            <XAxis
              dataKey="t"
              tickFormatter={formatTick}
              tick={{ fontSize: 11, fill: '#6b5f52' }}
              stroke="#d7c9b6"
              tickLine={false}
              interval="preserveStartEnd"
              minTickGap={32}
            />
            <YAxis domain={[10, 40]} tick={{ fontSize: 11, fill: '#6b5f52' }} stroke="#d7c9b6" tickLine={false} />
            <Tooltip
              labelFormatter={formatTick}
              contentStyle={{
                borderRadius: '8px',
                border: '2px solid #f0e5d8',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
              }}
            />
            <Legend
              wrapperStyle={{ paddingTop: 12 }}
              formatter={(value) => <span style={{ color: '#5f4f3f' }}>{value}</span>}
            />
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
