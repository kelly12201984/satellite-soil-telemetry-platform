import { useQuery } from '@tanstack/react-query';
import { API_BASE, api } from './client';

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
  moisture30?: number;
  battery_hint?: string;
}

export interface Farm {
  id: string;
  name: string;
  device_count: number;
  status: DeviceStatus;
  attention_count: number;
  last_reading: string | null;
  last_reading_at: string | null;
  lat: number | null;
  lon: number | null;
}

export interface FarmDetail {
  id: string;
  name: string;
  device_count: number;
  devices: Device[];
  lat: number | null;
  lon: number | null;
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

export function useFarms() {
  return useQuery<Farm[]>({
    queryKey: ['farms'],
    queryFn: async () => {
      const url = new URL('/v1/farms', API_BASE);
      const res = await fetch(url.toString());
      if (res.status === 404) {
        return [];
      }
      if (!res.ok) {
        throw new Error(await res.text());
      }
      return res.json();
    },
    staleTime: 60000,
    retry: 0,
  });
}

export function useFarmDetail(farmId: string) {
  return useQuery<FarmDetail>({
    queryKey: ['farm', farmId],
    queryFn: () => api(`/v1/farms/${farmId}`),
    enabled: !!farmId
  });
}

