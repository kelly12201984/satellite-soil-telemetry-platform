import { useQuery } from '@tanstack/react-query';
import { api } from './client';

export function useSummary(q: any) {
  return useQuery({ 
    queryKey: ['summary', q], 
    queryFn: () => api('/v1/metrics/summary', q) 
  });
}

export function useMoistureSeries(q: any) {
  return useQuery({ 
    queryKey: ['moisture', q], 
    queryFn: () => api('/v1/metrics/moisture-series', { ...q, max_points: 800 })
  });
}

export function useTempSeries(q: any) {
  return useQuery({ 
    queryKey: ['temp', q], 
    queryFn: () => api('/v1/metrics/temp-series', { ...q, max_points: 800 })
  });
}

export function useAttention() {
  return useQuery({ 
    queryKey: ['attention'], 
    queryFn: () => api('/v1/devices/attention', { limit: 20 })
  });
}

export function useDevices(farmId?: string) {
  return useQuery({ 
    queryKey: ['devices', farmId], 
    queryFn: () => api('/v1/devices', { farm_id: farmId })
  });
}

