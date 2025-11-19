import { useQuery } from '@tanstack/react-query';
import { api } from './client';

export type DeviceStatus = 'red' | 'amber' | 'green' | 'blue' | 'stale' | 'offline' | 'gray';

export interface SummaryResponse {
  devices_needing_attention?: Array<{ status: DeviceStatus; alias?: string; device_id?: number }>;
  avg_moisture?: number;
  avg_temp?: number;
  last_reading_at?: string;
}

interface TimeSeriesPoint {
  t: string;
  v: number;
}

export interface MoistureSeries {
  device_name: string;
  depth_cm: number;
  points: TimeSeriesPoint[];
}

export interface TempSeries {
  device_name: string;
  points: TimeSeriesPoint[];
}

export interface AttentionDevice {
  device_id: number;
  alias: string;
  status: DeviceStatus;
  battery_hint?: string;
  last_seen?: string;
}

export interface Device {
  id: number;
  alias: string;
  status?: DeviceStatus;
  last_seen?: string;
  lat?: number;
  lon?: number;
}

export function useSummary(q: any) {
  return useQuery<SummaryResponse>({
    queryKey: ['summary', q],
    queryFn: () => api('/v1/metrics/summary', q)
  });
}

export function useMoistureSeries(q: any) {
  return useQuery<MoistureSeries[]>({
    queryKey: ['moisture', q],
    queryFn: () => api('/v1/metrics/moisture-series', { ...q, max_points: 800 })
  });
}

export function useTempSeries(q: any) {
  return useQuery<TempSeries[]>({
    queryKey: ['temp', q],
    queryFn: () => api('/v1/metrics/temp-series', { ...q, max_points: 800 })
  });
}

export function useAttention() {
  return useQuery<AttentionDevice[]>({
    queryKey: ['attention'],
    queryFn: () => api('/v1/devices/attention', { limit: 20 })
  });
}

export function useDevices(farmId?: string) {
  return useQuery<Device[]>({
    queryKey: ['devices', farmId],
    queryFn: () => api('/v1/devices', { farm_id: farmId })
  });
}

