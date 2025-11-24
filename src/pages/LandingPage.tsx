import { useFarms } from '@/api/hooks';
import { FarmCard } from '@/components/FarmCard';
import { FarmOverviewMap } from '@/components/FarmOverviewMap';

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

export default function LandingPage() {
  const { data: farms = [], isLoading } = useFarms();

  return (
    <div className="min-h-screen bg-stone-50">
      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* Header with logo */}
        <div className="flex items-center justify-center mb-8">
          <img
            src="/BRSense_logo.png"
            alt="BRSense"
            className="h-14 w-auto"
          />
        </div>

        {isLoading ? (
          <LoadingSkeleton />
        ) : farms.length === 0 ? (
          <div className="text-center py-16">
            <div className="text-stone-500 text-lg mb-2">No farms registered yet</div>
            <div className="text-stone-400 text-sm">
              Devices will be grouped by field when they start reporting
            </div>
          </div>
        ) : (
          <>
            {/* Overview Map */}
            <div className="mb-8">
              <h2 className="text-lg font-semibold text-stone-700 mb-3">Farm Locations</h2>
              <FarmOverviewMap farms={farms} />
            </div>

            {/* Farm Cards Grid */}
            <div>
              <h2 className="text-lg font-semibold text-stone-700 mb-3">
                Your Farms
                <span className="ml-2 text-sm font-normal text-stone-500">
                  ({farms.length} total)
                </span>
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {farms.map(farm => (
                  <FarmCard key={farm.id} farm={farm} />
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
