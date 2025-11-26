import { Link } from 'react-router-dom';
import { useFarms, useDevices, useAttention, Farm, Device } from '@/api/hooks';
import { FarmCard } from '@/components/FarmCard';
import { FarmOverviewMap } from '@/components/FarmOverviewMap';

const MOCK_FARMS: Farm[] = [
  {
    id: 'test-farm',
    name: 'Test Field',
    device_count: 4,
    status: 'green',
    attention_count: 1,
    last_reading: '27 days ago',
    last_reading_at: null,
    lat: -23.5505,
    lon: -46.6333,
  },
  {
    id: 'cerrado-south',
    name: 'Cerrado South',
    device_count: 3,
    status: 'amber',
    attention_count: 2,
    last_reading: '12 hours ago',
    last_reading_at: null,
    lat: -22.9035,
    lon: -47.0596,
  },
  {
    id: 'valley-demo',
    name: 'Valley Demo',
    device_count: 5,
    status: 'red',
    attention_count: 3,
    last_reading: '2 hours ago',
    last_reading_at: null,
    lat: -21.1704,
    lon: -47.8103,
  },
];

function LoadingSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="h-72 bg-stone-200 rounded-xl mb-6" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-36 bg-stone-200 rounded-xl" />
        ))}
      </div>
    </div>
  );
}

function deriveFarmFromDevices(devices: Device[], attentionCount: number): Farm | null {
  if (!devices.length) return null;
  const withLocation = devices.filter(d => d.lat != null && d.lon != null);
  const avgLat = withLocation.length ? withLocation.reduce((sum, d) => sum + (d.lat || 0), 0) / withLocation.length : null;
  const avgLon = withLocation.length ? withLocation.reduce((sum, d) => sum + (d.lon || 0), 0) / withLocation.length : null;

  const status =
    attentionCount > 0
      ? 'amber'
      : devices.some(d => d.status === 'red')
        ? 'red'
        : devices.some(d => d.status === 'blue')
          ? 'blue'
          : 'green';

  return {
    id: 'test-farm',
    name: 'Test Field',
    device_count: devices.length,
    status,
    attention_count: attentionCount,
    last_reading: devices[0]?.last_seen ?? 'Just now',
    last_reading_at: devices[0]?.last_seen ?? null,
    lat: avgLat,
    lon: avgLon,
  };
}

export default function LandingPage() {
  const { data: farms = [], isLoading } = useFarms();
  const { data: devices = [] } = useDevices();
  const { data: attention = [] } = useAttention();

  const derivedFarm = deriveFarmFromDevices(devices, attention.length);
  const hasApiFarms = farms.length > 0;
  const showSample = !hasApiFarms && !derivedFarm;
  const displayFarms = hasApiFarms ? farms : derivedFarm ? [derivedFarm] : MOCK_FARMS;

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_#fdfaf3,_#f6f1e5_55%,_#efe3d1)]">
      <div className="px-6 lg:px-10 py-8 space-y-10">
        <div className="w-full rounded-3xl border border-[#eadfcf] bg-gradient-to-r from-[#fdfaf3] via-[#eef3ee] to-[#ffffff] p-8 shadow-[0_25px_70px_rgba(31,106,78,0.12)]">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <Link to="/readings" className="group" aria-label="Back to dashboard">
              <img
                src="/BRSense_logo.png"
                alt="BRSense logo"
                className="h-48 w-auto drop-shadow-2xl transition-transform duration-200 group-hover:scale-[1.05]"
              />
            </Link>
            <div>
              <p className="text-sm uppercase tracking-[0.55em] text-[#b28428] font-semibold mb-3">
                Network overview
              </p>
              <h1 className="text-4xl lg:text-5xl font-semibold text-[#1f6a4e] leading-tight">Fields & Fleet Health</h1>
              <p className="text-lg text-[#b28428] mt-2">
                Live telemetry and device health for every field.
              </p>
            </div>
          </div>
        </div>

        {isLoading ? (
          <LoadingSkeleton />
        ) : (
          <>
            <div className="space-y-8">
              {showSample && (
                <div className="rounded-2xl border border-dashed border-[#d4c6b4] bg-white/80 px-4 py-3 text-sm text-[#5b5044] text-center">
                  No farm data yet – showing sample layout. Replay the captured test messages or seed data to see live farms.
                </div>
              )}

              <div className="grid gap-6 lg:grid-cols-5 items-start">
                <div className="lg:col-span-3 space-y-3">
                  <h2 className="text-sm uppercase tracking-[0.4em] text-[#b28428] font-semibold">Field Locations</h2>
                  <div className="border border-[#eadfcf] rounded-3xl overflow-hidden shadow-sm bg-white/80 min-h-[420px]">
                    <FarmOverviewMap farms={displayFarms} />
                  </div>
                </div>

                <div className="lg:col-span-2 space-y-4">
                  <div className="flex items-center justify-between">
                    <h2 className="text-sm uppercase tracking-[0.35em] text-[#1f6a4e] font-semibold">Fields</h2>
                    <span className="text-sm font-normal text-stone-500">
                      ({displayFarms.length} total)
                    </span>
                  </div>
                  <div className="grid grid-cols-1 gap-4">
                    {displayFarms.map(farm => (
                      <FarmCard key={farm.id} farm={farm} />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
