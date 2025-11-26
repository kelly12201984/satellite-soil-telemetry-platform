import { useSearchParams } from 'react-router-dom';
import { presetToRange } from '@/lib/time';
export function FilterBar() {
  const [sp, setSp] = useSearchParams();
  const preset = sp.get('preset') ?? '7d';
  const custom = preset === 'custom';

  function setPreset(p: string) {
    const { from, to } =
      p === 'custom'
        ? {
            from: sp.get('from') ?? '',
            to: sp.get('to') ?? '',
          }
        : presetToRange(p);

    sp.set('preset', p);

    if (p !== 'custom') {
      sp.set('from', from);
      sp.set('to', to);
    }

    setSp(sp, { replace: true });
  }

  return (
    <div className="flex flex-wrap gap-2 items-center bg-white/90 border border-[#ede2d3] rounded-2xl p-3 shadow-sm">
      {/* Time range presets */}
      <select
        value={preset}
        onChange={(e) => setPreset(e.target.value)}
        className="px-3 py-2 border rounded bg-white"
      >
        <option value="24h">24h</option>
        <option value="7d">7d</option>
        <option value="14d">14d</option>
        <option value="30d">30d</option>
        <option value="90d">90d</option>
        <option value="custom">Custom</option>
      </select>

      {/* Custom date inputs */}
      {custom && (
        <>
          <input
            type="datetime-local"
            value={
              sp.get('from')
                ? new Date(sp.get('from')!).toISOString().slice(0, 16)
                : ''
            }
            onChange={(e) => {
              sp.set('from', new Date(e.target.value).toISOString());
              setSp(sp, { replace: true });
            }}
            className="px-3 py-2 border rounded bg-white"
          />

          <input
            type="datetime-local"
            value={
              sp.get('to')
                ? new Date(sp.get('to')!).toISOString().slice(0, 16)
                : ''
            }
            onChange={(e) => {
              sp.set('to', new Date(e.target.value).toISOString());
              setSp(sp, { replace: true });
            }}
            className="px-3 py-2 border rounded bg-white"
          />
        </>
      )}
    </div>
  );
}

