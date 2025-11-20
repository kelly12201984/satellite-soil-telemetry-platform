import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, ReferenceArea } from 'recharts';
import { useSearchParams } from 'react-router-dom';
import { presetToRange } from '@/lib/time';
import { MoistureSeries, useMoistureSeries } from '@/api/hooks';

export function MoistureChart({ q, onToggle }: { q: any; onToggle: () => void }) {
  const [sp, setSp] = useSearchParams();
  const { data = [], isLoading } = useMoistureSeries(q);

  if (isLoading) return <div className="min-h-[32rem] flex items-center justify-center">Loading...</div>;
  if (!data || data.length === 0) return <div className="min-h-[32rem] flex items-center justify-center text-gray-500">No data</div>;

  // Flatten series to chart rows
  const timeMap = new Map<string, any>();
  const seriesMeta: Array<{ key: string; color: string; device: string; depth: number }> = [];
  const colors = ['#2d8659', '#27ae60', '#f39c12', '#e74c3c', '#3498db', '#9b59b6', '#1abc9c', '#e67e22'];
  
  data.forEach((series: MoistureSeries, idx: number) => {
    const key = `${series.device_name}@${series.depth_cm}cm`;
    seriesMeta.push({
      key,
      color: colors[idx % colors.length],
      device: series.device_name,
      depth: series.depth_cm,
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
    <div className="border rounded-lg p-3 bg-white">
      {/* Header with title and toggle */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-900">Soil Moisture</h3>
        <button
          onClick={onToggle}
          className="px-3 py-1 text-sm border rounded hover:bg-gray-50 transition-colors"
        >
          View Temperature →
        </button>
      </div>

      {/* Depth selector */}
      <div className="flex flex-wrap gap-2 mb-3">
        {[10, 20, 30, 40, 50, 60].map(cm => {
          const active = (sp.get('depths') ?? '').split(',').includes(String(cm));
          return (
            <button
              key={cm}
              className={`px-3 py-1 rounded text-sm transition-colors ${
                active ? 'bg-purple-600 text-white' : 'bg-gray-200 hover:bg-gray-300'
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
          className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 transition-colors"
          title="Reset filters"
        >
          Reset
        </button>
      </div>

      {/* Chart */}
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows}>
            {/* Threshold bands */}
            <ReferenceArea y1={0} y2={25} fill="#fee2e2" />
            <ReferenceArea y1={25} y2={30} fill="#fef3c7" />
            <XAxis dataKey="t" />
            <YAxis domain={[0, 60]} />
            <Tooltip />
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
          <div className="text-xs text-gray-500 mt-2">+ {seriesMeta.length - 8} more series</div>
        )}
      </div>
    </div>
  );
}

