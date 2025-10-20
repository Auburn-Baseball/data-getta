import { describe, expect, it } from 'vitest';

import { batterStatsTransform, createBatterStatsSummary } from '@/transforms/batterStatsTransform';
import type { BatterStatsTable } from '@/types/db';

const makeStat = (overrides: Partial<BatterStatsTable>): BatterStatsTable => ({
  Batter: 'Doe, John',
  BatterTeam: 'AUB_TIG',
  Date: '2024-02-16',
  hits: 0,
  doubles: 0,
  triples: 0,
  singles: 0,
  at_bats: 0,
  strikes: 0,
  walks: 0,
  strikeouts: 0,
  homeruns: 0,
  extra_base_hits: 0,
  plate_appearances: 0,
  hit_by_pitch: 0,
  sacrifice: 0,
  total_bases: 0,
  batting_average: 0,
  on_base_percentage: 0,
  slugging_percentage: 0,
  onbase_plus_slugging: 0,
  isolated_power: 0,
  k_percentage: 0,
  base_on_ball_percentage: 0,
  chase_percentage: 0,
  in_zone_whiff_percentage: 0,
  games: 1,
  k_per: 0,
  bb_per: 0,
  avg_exit_velo: 0,
  ...overrides,
});

describe('batterStatsTransform', () => {
  it('aggregates batter statistics across games and ignores practice data', () => {
    const game1 = makeStat({
      hits: 2,
      doubles: 1,
      singles: 1,
      at_bats: 4,
      strikes: 3,
      walks: 1,
      strikeouts: 1,
      homeruns: 0,
      extra_base_hits: 1,
      plate_appearances: 5,
      total_bases: 5,
      batting_average: 0.5,
      on_base_percentage: 0.6,
      slugging_percentage: 1.25,
      onbase_plus_slugging: 1.85,
      isolated_power: 0.75,
      k_percentage: 0.2,
      base_on_ball_percentage: 0.2,
      chase_percentage: 0.2,
      in_zone_whiff_percentage: 0.25,
      k_per: 1,
      bb_per: 1,
      avg_exit_velo: 92,
      batted_balls: 3,
      total_exit_velo: 276,
    });

    const game2 = makeStat({
      Date: '2024-02-17',
      hits: 1,
      singles: 1,
      at_bats: 3,
      strikes: 2,
      walks: 0,
      strikeouts: 1,
      plate_appearances: 3,
      total_bases: 1,
      batting_average: 0.333,
      on_base_percentage: 0.333,
      slugging_percentage: 0.333,
      onbase_plus_slugging: 0.666,
      isolated_power: 0,
      k_percentage: 0.333,
      base_on_ball_percentage: 0,
      chase_percentage: 0.1,
      in_zone_whiff_percentage: 0.3,
      k_per: 1,
      bb_per: 0,
      avg_exit_velo: 88,
      batted_balls: 2,
      total_exit_velo: 176,
    });

    const practiceGame = makeStat({
      Date: '2024-02-18',
      hits: 4,
      at_bats: 4,
      is_practice: true,
    });

    const result = batterStatsTransform([game1, game2, practiceGame]);
    expect(result).toHaveLength(1);
    const aggregated = result[0];

    expect(aggregated.hits).toBe(3);
    expect(aggregated.at_bats).toBe(7);
    expect(aggregated.walks).toBe(1);
    expect(aggregated.strikeouts).toBe(2);
    expect(aggregated.total_bases).toBe(6);
    expect(aggregated.plate_appearances).toBe(8);
    expect(aggregated.games).toBe(2);
    expect(aggregated.batted_balls).toBe(5);
    expect(aggregated.total_exit_velo).toBe(452);
    expect(aggregated.avg_exit_velo).toBeCloseTo(90.4, 1);
    expect(aggregated.batting_average).toBeCloseTo(0.429, 3);
    expect(aggregated.on_base_percentage).toBeCloseTo(0.5, 3);
    expect(aggregated.slugging_percentage).toBeCloseTo(0.857, 3);
    expect(aggregated.onbase_plus_slugging).toBeCloseTo(1.357, 3);
    expect(aggregated.isolated_power).toBeCloseTo(0.429, 3);
    expect(aggregated.k_percentage).toBeCloseTo(0.25, 3);
    expect(aggregated.base_on_ball_percentage).toBeCloseTo(0.125, 3);
    expect(aggregated.chase_percentage).toBeCloseTo(0.1625, 3);
    expect(aggregated.in_zone_whiff_percentage).toBeCloseTo(0.27, 3);
    expect(aggregated.k_per).toBeCloseTo(1);
    expect(aggregated.bb_per).toBeCloseTo(0.5);
  });

  it('creates a summary row with combined totals', () => {
    const players: BatterStatsTable[] = [
      makeStat({
        Batter: 'Doe, John',
        hits: 10,
        at_bats: 30,
        total_bases: 40,
        walks: 5,
        strikeouts: 6,
        plate_appearances: 38,
        hit_by_pitch: 1,
        sacrifice: 2,
      }),
      makeStat({
        Batter: 'Smith, Alex',
        BatterTeam: 'AUB_PRC',
        hits: 5,
        at_bats: 20,
        total_bases: 22,
        walks: 4,
        strikeouts: 4,
        plate_appearances: 26,
        hit_by_pitch: 0,
        sacrifice: 1,
      }),
    ];

    const summary = createBatterStatsSummary(players);
    expect(summary.hits).toBe(15);
    expect(summary.at_bats).toBe(50);
    expect(summary.total_bases).toBe(62);
    expect(summary.walks).toBe(9);
    expect(summary.strikeouts).toBe(10);
    expect(summary.batting_average).toBeCloseTo(0.3, 3);
    expect(summary.on_base_percentage).toBeCloseTo((15 + 9 + 1) / (50 + 9 + 1 + 3), 3);
    expect(summary.slugging_percentage).toBeCloseTo(62 / 50, 3);
    expect(summary.k_percentage).toBeCloseTo(10 / 64, 3);
  });
});
