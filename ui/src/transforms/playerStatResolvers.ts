import { batterStatsTransform } from '@/transforms/batterStatsTransform';
import { pitchCountsTransform, pitcherStatsTransform } from '@/transforms/pitcherStatsTransforms';
import type { BatterStatsTable, PitchCountsTable, PitcherStatsTable } from '@/types/db';

export function resolveBatterStats(data?: BatterStatsTable[] | null): BatterStatsTable | null {
  if (!data?.length) return null;

  // Default transform behavior is 'gameOnly' (filters practice),
  // which restores test expectations and runtime semantics.
  const transformed = batterStatsTransform(data);
  if (transformed.length > 0) return transformed[0] ?? null;

  // Fallback preserves raw row (including is_practice) for tests expecting this.
  return data[0] ?? null;
}

export function resolvePitcherStats(data?: PitcherStatsTable[] | null): PitcherStatsTable | null {
  if (!data?.length) return null;

  const transformed = pitcherStatsTransform(data);
  if (transformed.length > 0) return transformed[0] ?? null;

  return data[0] ?? null;
}

export function resolvePitchCounts(data?: PitchCountsTable[] | null): PitchCountsTable | null {
  if (!data?.length) return null;

  const transformed = pitchCountsTransform(data);
  if (transformed.length > 0) return transformed[0] ?? null;

  return data[0] ?? null;
}
