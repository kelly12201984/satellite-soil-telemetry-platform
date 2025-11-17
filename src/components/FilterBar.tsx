import { useSearchParams } from 'react-router-dom';
import { presetToRange } from '@/lib/time';
import { useDevices } from '@/api/hooks';

export function FilterBar() {
  const [sp, setSp] = useSearchParams();
  const preset = sp.get('preset') ?? '7d';
  const custom = sp.get('preset') === 'custom';
  const { data: devices } = useDevices();

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
    <div className="flex flex-wrap gap-2 items-center">
      {/* Devices multi-select */}
      <select
        multiple
        value={(sp.get('devices')?.split(',') ?? [])}
        onChange={e => {
          const vals = Array.from(e.target.selectedOptions).map(o => o.value);
          if (vals.length) sp.set('devices', vals.join(','));
          else sp.delete('devices');
          setSp(sp, { replace: true });
        }}
        className="px-3 py-2 border rounded"
      >
        {(Array.isArray(devices) ? devices : []).map((d: any) => (
          <option key={d.id} value={d.id}>{d.alias}</option>
        ))}
      </select>

      {/* Depth chips */}
      {[10, 20, 30, 40, 50, 60].map(cm => {
        const active = (sp.get('depths') ?? '').split(',').includes(String(cm));
        return (
          <button
            key={cm}
            className={`px-3 py-1 rounded transition-colors ${active ? 'bg-purple-600 text-white' : 'bg-gray-200 hover:bg-gray-300'
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

      {/* Period select */}
      <select
        value={preset}
        onChange={e => setPreset(e.target.value)}
        className="px-3 py-2 border rounded"
      >
        <option value="24h">24h</option>
        <option value="7d">7 days</option>
        <option value="14d">14 days</option>
        <option value="30d">30 days</option>
        <option value="90d">90 days</option>
        <option value="ytd">YTD</option>
        <option value="custom">Custom…</option>
      </select>

      {/* Custom date range */}
      {custom && (
        <>
          <input
            type="datetime-local"
            value={sp.get('from') ? new Date(sp.get('from')!).toISOString().slice(0, 16) : ''}
            onChange={e => {
              sp.set('from', new Date(e.target.value).toISOString());
              setSp(sp, { replace: true });
            }}
            className="px-3 py-2 border rounded"
          />
          <input
            type="datetime-local"
            value={sp.get('to') ? new Date(sp.get('to')!).toISOString().slice(0, 16) : ''}
            onChange={e => {
              sp.set('to', new Date(e.target.value).toISOString());
              setSp(sp, { replace: true });
            }}
            className="px-3 py-2 border rounded"
          />
        </>
      )}

      {/* Reset pill */}
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
        className="px-3 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50 transition-colors"
        title="Reset filters to defaults"
      >
        Reset
      </button>
    </div>
  );
}

