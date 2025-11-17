export type Range = { from: string; to: string }; // ISO

export function presetToRange(preset: string, now = new Date()): Range {
  const end = now;
  const start = new Date(now);

  if (preset === '24h') {
    start.setHours(start.getHours() - 24);
  } else if (preset === '7d') {
    start.setDate(start.getDate() - 7);
  } else if (preset === '14d') {
    start.setDate(start.getDate() - 14);
  } else if (preset === '30d') {
    start.setDate(start.getDate() - 30);
  } else if (preset === '90d') {
    start.setDate(start.getDate() - 90);
  } else if (preset === 'ytd') {
    start.setMonth(0, 1);
    start.setHours(0, 0, 0, 0);
  }

  return { from: start.toISOString(), to: end.toISOString() };
}

