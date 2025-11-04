import { describe, expect, it } from 'vitest';

import {
  resolveBatterStats,
  resolvePitchCounts,
  resolvePitcherStats,
} from '@/transforms/playerStatResolvers';
import type { BatterStatsTable, PitchCountsTable, PitcherStatsTable } from '@/types/db';

const makeBatter = (overrides: Partial<BatterStatsTable>): BatterStatsTable => ({
  Batter: 'Doe, John',
  BatterTeam: 'AUB_TIG',
  Date: '2024-02-16',
  is_practice: false,
  hits: 1,
  doubles: 0,
  triples: 0,
  singles: 1,
  at_bats: 3,
  strikes: 2,
  walks: 1,
  strikeouts: 0,
  homeruns: 0,
  extra_base_hits: 0,
  plate_appearances: 4,
  hit_by_pitch: 0,
  sacrifice: 0,
  total_bases: 1,
  batting_average: 0.333,
  on_base_percentage: 0.5,
  slugging_percentage: 0.333,
  onbase_plus_slugging: 0.833,
  isolated_power: 0,
  k_percentage: 0,
  base_on_ball_percentage: 0.25,
  chase_percentage: 0.1,
  in_zone_whiff_percentage: 0.1,
  games: 1,
  k_per: 0,
  bb_per: 1,
  avg_exit_velo: 90,
  ...overrides,
});

const makePitcher = (overrides: Partial<PitcherStatsTable>): PitcherStatsTable => ({
  Pitcher: 'Ace, John',
  PitcherTeam: 'AUB_TIG',
  Date: '2024-02-16',
  Year: 2024,
  total_innings_pitched: 1.0,
  total_strikeouts_pitcher: 2,
  total_walks_pitcher: 1,
  total_out_of_zone_pitches: 5,
  total_in_zone_pitches: 6,
  misses_in_zone: 2,
  swings_in_zone: 4,
  total_num_chases: 1,
  pitches: 30,
  games_started: 1,
  total_batters_faced: 10,
  k_percentage: 0.2,
  base_on_ball_percentage: 0.1,
  in_zone_whiff_percentage: 0.3,
  chase_percentage: 0.2,
  games: 1,
  k_per_9: 18,
  bb_per_9: 9,
  whip: 1.0,
  hits: 2,
  runs_allowed: 1,
  homeruns: 0,
  earned_runs: 1,
  is_practice: false,
  ...overrides,
});

const makePitchCount = (overrides: Partial<PitchCountsTable>): PitchCountsTable => ({
  Pitcher: 'Ace, John',
  PitcherTeam: 'AUB_TIG',
  Date: '2024-02-16',
  Year: 2024,
  total_pitches: 25,
  curveball_count: 4,
  fourseam_count: 8,
  sinker_count: 3,
  slider_count: 5,
  twoseam_count: 0,
  changeup_count: 3,
  cutter_count: 1,
  splitter_count: 1,
  other_count: 0,
  games: 1,
  is_practice: false,
  ...overrides,
});

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
