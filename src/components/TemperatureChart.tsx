import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TempSeries, useTempSeries } from '@/api/hooks';

export function TemperatureChart({ q }: { q: any }) {
  const { data = [], isLoading } = useTempSeries(q);
  
  if (isLoading) return <div className="h-80 flex items-center justify-center">Loading...</div>;
  if (!data || data.length === 0) return <div className="h-80 flex items-center justify-center text-gray-500">No data</div>;

  // Flatten series to chart rows
  const timeMap = new Map<string, any>();
  const seriesMeta: Array<{ key: string; color: string; device: string }> = [];
  const colors = ['#e74c3c', '#f39c12', '#3498db', '#9b59b6', '#1abc9c', '#e67e22', '#2d8659', '#27ae60'];
  
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
    <div className="h-80 border rounded-lg p-4 bg-white">
      <div className="font-semibold px-2 pb-2">Soil Temperature Over Time</div>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rows}>
          <XAxis dataKey="t" />
          <YAxis domain={[10, 40]} />
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
  );
}

