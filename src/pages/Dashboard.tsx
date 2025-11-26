import { ReactNode, useEffect } from 'react';
import { useSearchParams, useParams, Link } from 'react-router-dom';
import { FilterBar } from '@/components/FilterBar';
import { useSummary } from '@/api/hooks';
import { DevicesCard } from '@/components/DevicesCard';
import { MoistureChart } from '@/components/MoistureChart';
import { TemperatureChart } from '@/components/TemperatureChart';
import { DeviceMap } from '@/components/DeviceMap';
import { presetToRange } from '@/lib/time';

function timeAgo(iso: string) {
  const diff = Date.now() - Date.parse(iso);
  if (!Number.isFinite(diff)) return '–';
  if (diff <= 60000) return 'Just now';
  if (diff < 0) return 'Just now';
  const minutes = Math.floor(diff / 60000);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function Kpi({ title, value, icon, tone = 'default' }: { title: string; value: string; icon: ReactNode; tone?: 'default' | 'alert' }) {
  const toneClasses =
    tone === 'alert'
      ? 'bg-[#fff7ef] border-[#f4c892]'
      : 'bg-white border-[#ece3d2]';
  const labelTone = tone === 'alert' ? 'text-[#b95817]' : 'text-[#706355]';
  return (
    <div className={`p-5 rounded-2xl border ${toneClasses} shadow-sm flex items-start gap-3`}>
      <div className="w-11 h-11 rounded-xl bg-white/80 flex items-center justify-center text-[var(--brand-forest)]">
        {icon}
      </div>
      <div>
        <div className={`text-[0.65rem] uppercase tracking-[0.32em] font-semibold ${labelTone}`}>{title}</div>
        <div className="text-2xl font-semibold text-[#2a2520]">{value}</div>
      </div>
    </div>
  );
}

const DropletIcon = () => (
  <svg viewBox="0 0 24 24" className="w-5 h-5 fill-current">
    <path d="M12 2C12 2 6 9.2 6 13.5 6 16.5 8.5 19 12 19s6-2.5 6-5.5C18 9.2 12 2 12 2z" />
  </svg>
);

const ThermometerIcon = () => (
  <svg viewBox="0 0 24 24" className="w-5 h-5 fill-current">
    <path d="M13 13.414V5a1 1 0 10-2 0v8.414a3.5 3.5 0 102 0z" />
  </svg>
);

const ClockIcon = () => (
  <svg viewBox="0 0 24 24" className="w-5 h-5 fill-current">
    <path d="M12 4a8 8 0 108 8 8.009 8.009 0 00-8-8zm1 8.268l2.4 2.4-1.4 1.4L11 12V7h2z" />
  </svg>
);

const DeviceIcon = () => (
  <svg viewBox="0 0 24 24" className="w-5 h-5 fill-current">
    <path d="M12 4a2 2 0 110 4 2 2 0 010-4zm0 12a2 2 0 110 4 2 2 0 010-4zm8-6a2 2 0 11-2 2 2 2 0 012-2zm-16 0a2 2 0 11-2 2 2 2 0 012-2z" />
    <path d="M12 8v8M8 12h8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const PencilIcon = () => (
  <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current">
    <path d="M3 17.25V21h3.75l11-11.03-3.75-3.75L3 17.25zM20.71 7.04a1.003 1.003 0 000-1.42l-2.34-2.34a1.003 1.003 0 00-1.42 0l-1.83 1.83 3.75 3.75 1.84-1.82z" />
  </svg>
);

export default function Dashboard() {
  const [sp, setSp] = useSearchParams();
  const { farmId } = useParams<{ farmId?: string }>();
  const farmLabel = farmId ? decodeURIComponent(farmId).replace(/-/g, ' ') : null;

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
      <div className="rounded-3xl border border-[#eadfcf] bg-gradient-to-br from-[#fdfaf3] via-[#eef3ee] to-[#ffffff] p-6 md:p-8 shadow-[0_20px_60px_rgba(31,106,78,0.12)]">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-5">
            <Link to="/readings" className="group" aria-label="Back to farms">
              <img
                src="/BRSense_logo.png"
                alt="BRSense logo"
                className="h-36 md:h-40 w-auto drop-shadow-2xl transition-transform duration-200 group-hover:scale-[1.05]"
              />
            </Link>
            <div>
              <p className="text-xs uppercase tracking-[0.5em] text-[#b28428] font-semibold mb-2">
                Precision irrigation
              </p>
              <h1 className="text-3xl font-semibold text-[#1f6a4e] leading-tight">Field Command Center</h1>
              <p className="text-sm text-[#b28428] mt-1">
                Live telemetry, device health, and depth trends for every probe.
              </p>
            </div>
          </div>
          {farmLabel && (
            <div className="self-start flex items-center gap-2">
              <span className="px-4 py-2 text-xs font-semibold tracking-[0.25em] uppercase bg-white/70 text-[#1f6a4e] border border-[#d7eadf] rounded-full shadow-sm">
                Focus · {farmLabel}
              </span>
              <button
                type="button"
                className="p-2 rounded-full border border-[#d7eadf] text-[#1f6a4e] hover:bg-white"
                title="Rename farm"
              >
                <PencilIcon />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Map with device pins */}
      <DeviceMap
        onPick={(id) => {
          sp.set('devices', id);
          setSp(sp, { replace: true });
          document.getElementById('charts')?.scrollIntoView({ behavior: 'smooth' });
        }}
      />

      <div className="mt-3">
        <div className="text-xs uppercase tracking-[0.4em] text-[#b28428] font-semibold mb-2">Date Range</div>
        <FilterBar />
      </div>

      {/* Attention Card (small, left) + KPI tiles */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {/* Small attention card */}
        <div className="p-5 border border-[#f1e4d3] rounded-2xl bg-white shadow-sm">
          <div className="text-xs uppercase tracking-[0.35em] font-semibold text-[#b95817] mb-2">Alerts</div>
          {isLoading ? (
            <div className="h-8 bg-[#f5ede2] rounded animate-pulse"></div>
          ) : (
            <div className="flex items-center gap-3">
              <span className="text-3xl font-semibold text-[#c0392b]">
                {summary?.devices_needing_attention?.filter((d: any) => d.status === 'red').length ?? 0}
              </span>
              {summary?.devices_needing_attention?.some((d: any) => d.status === 'amber') && (
                <span className="text-sm text-[#b28428] font-medium">
                  +{summary?.devices_needing_attention?.filter((d: any) => d.status === 'amber').length}
                </span>
              )}
              <button
                onClick={() => {
                  document.getElementById('charts')?.scrollIntoView({ behavior: 'smooth' });
                }}
                className="text-xs text-[#1f6a4e] hover:underline ml-auto font-semibold"
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
              icon={<DropletIcon />}
            />
            <Kpi
              title="Avg Temp"
              value={`${summary?.avg_temp?.toFixed?.(1) ?? '–'} °C`}
              icon={<ThermometerIcon />}
            />
            <Kpi
              title="Last Reading"
              value={summary?.last_reading_at ? timeAgo(summary.last_reading_at) : '–'}
              icon={<ClockIcon />}
              tone={summary?.last_reading_at ? 'default' : 'alert'}
            />
            <Kpi
              title="Active Devices"
              value={`${summary?.devices_needing_attention?.length ?? 0}`}
              icon={<DeviceIcon />}
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

