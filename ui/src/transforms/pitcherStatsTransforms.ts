import { PitchCountsTable, PitcherStatsTable } from '@/types/db';
import { inningsToOuts } from '@/transforms/pitching/utils';
import { aggregatePitcherStats } from '@/transforms/pitching/aggregatePitcher';
import { aggregatePitchCounts } from '@/transforms/pitching/aggregatePitchCounts';

export function pitcherStatsTransform(data: PitcherStatsTable[]): PitcherStatsTable[] {
  if (!data || data.length === 0) {
    return [];
  }

  const playerMap = new Map<string, PitcherStatsTable[]>();

  for (const stat of data) {
    const key = `${stat.Pitcher}|${stat.PitcherTeam}`;
    if (!playerMap.has(key)) {
      playerMap.set(key, []);
    }
    playerMap.get(key)!.push(stat);
  }

  const results: PitcherStatsTable[] = [];

  for (const playerStats of playerMap.values()) {
    const aggregated = aggregatePitcherStats(playerStats);
    if (aggregated) {
      results.push(aggregated);
    }
  }

  return results.sort((a, b) => {
    const outsDiff =
      inningsToOuts(b.total_innings_pitched) - inningsToOuts(a.total_innings_pitched);
    if (outsDiff !== 0) {
      return outsDiff;
    }
    return a.Pitcher.localeCompare(b.Pitcher);
  });
}

export function pitchCountsTransform(data: PitchCountsTable[]): PitchCountsTable[] {
  if (!data || data.length === 0) {
    return [];
  }

  const pitcherMap = new Map<string, PitchCountsTable[]>();

  for (const entry of data) {
    const key = `${entry.Pitcher}|${entry.PitcherTeam}`;
    if (!pitcherMap.has(key)) {
      pitcherMap.set(key, []);
    }
    pitcherMap.get(key)!.push(entry);
  }

  const results: PitchCountsTable[] = [];

  for (const counts of pitcherMap.values()) {
    const aggregated = aggregatePitchCounts(counts);
    if (aggregated) {
      results.push(aggregated);
    }
  }

  return results.sort((a, b) => {
    const pitchDiff = (b.total_pitches ?? 0) - (a.total_pitches ?? 0);
    if (pitchDiff !== 0) {
      return pitchDiff;
    }
    return a.Pitcher.localeCompare(b.Pitcher);
  });
}
