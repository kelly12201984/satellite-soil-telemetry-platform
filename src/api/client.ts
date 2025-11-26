export const API_BASE = import.meta.env.VITE_API_BASE || window.location.origin;

export async function api<T>(path: string, params: Record<string, any> = {}): Promise<T> {
  const url = new URL(path, API_BASE);
  
  Object.entries(params).forEach(([k, v]) => {
    if (Array.isArray(v)) {
      v.forEach(x => url.searchParams.append(k, String(x)));
    } else if (v !== undefined && v !== null) {
      url.searchParams.set(k, String(v));
    }
  });
  
  const r = await fetch(url.toString());
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

