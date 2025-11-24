import { Link } from 'react-router-dom';
import { Farm, DeviceStatus } from '@/api/hooks';

function statusConfig(status: DeviceStatus): { bg: string; border: string; text: string; label: string } {
  switch (status) {
    case 'red':
      return { bg: 'bg-red-50', border: 'border-red-300', text: 'text-red-700', label: 'Needs Attention' };
    case 'amber':
      return { bg: 'bg-amber-50', border: 'border-amber-300', text: 'text-amber-700', label: 'Monitor' };
    case 'stale':
    case 'offline':
      return { bg: 'bg-gray-50', border: 'border-gray-300', text: 'text-gray-600', label: 'Offline' };
    case 'gray':
      return { bg: 'bg-gray-50', border: 'border-gray-300', text: 'text-gray-600', label: 'No Data' };
    case 'blue':
      return { bg: 'bg-blue-50', border: 'border-blue-300', text: 'text-blue-700', label: 'Too Wet' };
    case 'green':
    default:
      return { bg: 'bg-emerald-50', border: 'border-emerald-300', text: 'text-emerald-700', label: 'Healthy' };
  }
}

function StatusBadge({ status }: { status: DeviceStatus }) {
  const config = statusConfig(status);
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
      <span className={`w-2 h-2 rounded-full ${status === 'green' ? 'bg-emerald-500' : status === 'red' ? 'bg-red-500' : status === 'amber' ? 'bg-amber-500' : status === 'blue' ? 'bg-blue-500' : 'bg-gray-400'}`} />
      {config.label}
    </span>
  );
}

interface FarmCardProps {
  farm: Farm;
}

export function FarmCard({ farm }: FarmCardProps) {
  const config = statusConfig(farm.status);

  return (
    <Link
      to={`/readings/farm/${farm.id}`}
      className={`block p-5 rounded-xl border-2 ${config.border} ${config.bg} hover:shadow-lg transition-all duration-200 cursor-pointer group`}
    >
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-lg font-semibold text-stone-800 group-hover:text-stone-900">
          {farm.name}
        </h3>
        <StatusBadge status={farm.status} />
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <div className="text-stone-500 mb-0.5">Devices</div>
          <div className="font-medium text-stone-800">{farm.device_count}</div>
        </div>
        <div>
          <div className="text-stone-500 mb-0.5">Last Reading</div>
          <div className="font-medium text-stone-800">{farm.last_reading || 'No data'}</div>
        </div>
      </div>

      {farm.attention_count > 0 && (
        <div className="mt-3 pt-3 border-t border-stone-200">
          <span className="text-sm text-red-600 font-medium">
            {farm.attention_count} device{farm.attention_count > 1 ? 's' : ''} need{farm.attention_count === 1 ? 's' : ''} attention
          </span>
        </div>
      )}
    </Link>
  );
}
