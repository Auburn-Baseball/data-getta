import { describe, expect, it } from 'vitest';

import { pitchCountsTransform, pitcherStatsTransform } from '@/transforms/pitcherStatsTransforms';
import { makePitchCount, makePitcherStat } from '@/test/mocks/pitcherStats';

describe('pitcherStatsTransform', () => {
  it('aggregates pitcher stats across games', () => {
    const game1 = makePitcherStat({
      Date: '2024-02-16',
      total_innings_pitched: 1.2,
      total_strikeouts_pitcher: 3,
      total_walks_pitcher: 1,
      total_out_of_zone_pitches: 10,
      total_in_zone_pitches: 12,
      misses_in_zone: 4,
      swings_in_zone: 8,
      total_num_chases: 3,
      pitches: 40,
      games_started: 1,
      total_batters_faced: 15,
      hits: 2,
      runs_allowed: 1,
      earned_runs: 1,
    });

    const game2 = makePitcherStat({
      Date: '2024-02-17',
      total_innings_pitched: 0.2,
      total_strikeouts_pitcher: 1,
      total_walks_pitcher: 0,
      total_out_of_zone_pitches: 5,
      total_in_zone_pitches: 8,
      misses_in_zone: 1,
      swings_in_zone: 5,
      total_num_chases: 2,
      pitches: 30,
      games_started: 0,
      total_batters_faced: 10,
      hits: 3,
      runs_allowed: 2,
      earned_runs: 2,
    });

    const result = pitcherStatsTransform([game1, game2]);
    expect(result).toHaveLength(1);
    const aggregated = result[0];

    expect(aggregated.total_innings_pitched).toBeCloseTo(2.1, 1);
    expect(aggregated.total_strikeouts_pitcher).toBe(4);
    expect(aggregated.total_walks_pitcher).toBe(1);
    expect(aggregated.total_out_of_zone_pitches).toBe(15);
    expect(aggregated.total_in_zone_pitches).toBe(20);
    expect(aggregated.misses_in_zone).toBe(5);
    expect(aggregated.total_num_chases).toBe(5);
    expect(aggregated.pitches).toBe(70);
    expect(aggregated.hits).toBe(5);
    expect(aggregated.games_started).toBe(1);
    expect(aggregated.games).toBe(2);
    expect(aggregated.total_batters_faced).toBe(25);
    expect(aggregated.k_percentage).toBeCloseTo(0.16, 2);
    expect(aggregated.base_on_ball_percentage).toBeCloseTo(0.04, 2);
    expect(aggregated.chase_percentage).toBeCloseTo(0.333, 3);
    expect(aggregated.in_zone_whiff_percentage).toBeCloseTo(5 / 13, 3);
    expect(aggregated.k_per_9).toBeCloseTo(15.4, 1);
    expect(aggregated.bb_per_9).toBeCloseTo(3.9, 1);
    expect(aggregated.whip).toBeCloseTo(2.57, 2);
  });
});

describe('pitchCountsTransform', () => {
  it('aggregates pitch counts across games', () => {
    const game1 = makePitchCount({
      Date: '2024-02-16',
      total_pitches: 40,
      curveball_count: 5,
      fourseam_count: 10,
      sinker_count: 4,
      slider_count: 8,
      twoseam_count: 3,
      changeup_count: 5,
      cutter_count: 4,
      splitter_count: 1,
      other_count: 0,
    });

    const game2 = makePitchCount({
      Date: '2024-02-17',
      total_pitches: 30,
      curveball_count: 4,
      fourseam_count: 8,
      sinker_count: 3,
      slider_count: 6,
      twoseam_count: 2,
      changeup_count: 3,
      cutter_count: 2,
      splitter_count: 1,
      other_count: 3,
    });

    const result = pitchCountsTransform([game1, game2]);
    expect(result).toHaveLength(1);
    const aggregated = result[0];

    expect(aggregated.total_pitches).toBe(70);
    expect(aggregated.curveball_count).toBe(9);
    expect(aggregated.fourseam_count).toBe(18);
    expect(aggregated.sinker_count).toBe(7);
    expect(aggregated.slider_count).toBe(14);
    expect(aggregated.twoseam_count).toBe(5);
    expect(aggregated.changeup_count).toBe(8);
    expect(aggregated.cutter_count).toBe(6);
    expect(aggregated.splitter_count).toBe(2);
    expect(aggregated.other_count).toBe(3);
    expect(aggregated.games).toBe(2);
  });
});
