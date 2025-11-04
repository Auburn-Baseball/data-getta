import { describe, expect, it } from 'vitest';

import {
  resolveBatterStats,
  resolvePitchCounts,
  resolvePitcherStats,
} from '@/transforms/playerStatResolvers';
import { makeBatterStat as makeBatter } from '@/test/mocks/batterStats';
import { makePitchCount, makePitcherStat as makePitcher } from '@/test/mocks/pitcherStats';

describe('playerStatResolvers', () => {
  it('returns transformed batter stats when data exists', () => {
    const batterStats = resolveBatterStats([
      makeBatter({ hits: 2, at_bats: 4, batting_average: 0.5 }),
      makeBatter({ Date: '2024-02-17', hits: 1, at_bats: 3, batting_average: 0.333 }),
    ]);
    expect(batterStats).not.toBeNull();
    expect(batterStats!.hits).toBe(3);
    expect(batterStats!.games).toBe(2);
  });

  it('falls back to raw batter stats when transform yields nothing', () => {
    const fallback = resolveBatterStats([makeBatter({ is_practice: true })]);
    expect(fallback).not.toBeNull();
    expect(fallback!.is_practice).toBe(true);
  });

  it('returns transformed pitcher stats and pitch counts', () => {
    const pitcher = resolvePitcherStats([
      makePitcher({ total_innings_pitched: 1.0 }),
      makePitcher({ Date: '2024-02-17', total_innings_pitched: 0.2 }),
    ]);
    expect(pitcher).not.toBeNull();
    expect(pitcher!.total_innings_pitched).toBeCloseTo(1.2, 1);

    const counts = resolvePitchCounts([
      makePitchCount({ total_pitches: 20, fourseam_count: 6 }),
      makePitchCount({ Date: '2024-02-17', total_pitches: 30, fourseam_count: 10 }),
    ]);
    expect(counts).not.toBeNull();
    expect(counts!.total_pitches).toBe(50);
    expect(counts!.fourseam_count).toBe(16);
  });
});
