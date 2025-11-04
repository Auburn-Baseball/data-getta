import { BatterStatsTable } from '@/types/db';
import { aggregateBatterStats } from '@/transforms/batting/aggregate';
export { createBatterStatsSummary } from './batting/summary';

export function batterStatsTransform(
  data: BatterStatsTable[],
  opts?: { mode?: 'all' | 'practiceOnly' | 'gameOnly' },
): BatterStatsTable[] {
  if (!data || data.length === 0) return [];

  // Single source of truth for default behavior:
  const mode: 'all' | 'practiceOnly' | 'gameOnly' = opts?.mode ?? 'gameOnly';

  const playerMap = new Map<string, BatterStatsTable[]>();

  for (const stat of data) {
    if (mode === 'gameOnly' && stat.is_practice) continue;
    if (mode === 'practiceOnly' && !stat.is_practice) continue;

    const key = `${stat.Batter}|${stat.BatterTeam}`;
    if (!playerMap.has(key)) playerMap.set(key, []);
    playerMap.get(key)!.push(stat);
  }

  const results: BatterStatsTable[] = [];
  for (const playerStats of playerMap.values()) {
    const aggregated = aggregateBatterStats(playerStats);
    if (aggregated) results.push(aggregated);
  }

  // Sort by batting average (desc), then name for stability
  return results.sort((a, b) => {
    const aAvg = a.batting_average ?? 0;
    const bAvg = b.batting_average ?? 0;
    if (bAvg !== aAvg) return bAvg - aAvg;
    return (a.Batter || '').localeCompare(b.Batter || '');
  });
}

// Optional team summary row helper (unchanged API)
