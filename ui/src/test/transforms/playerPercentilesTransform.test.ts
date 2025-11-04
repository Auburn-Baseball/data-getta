import { describe, expect, it } from 'vitest';

import { transformPercentileStats } from '@/transforms/playerPercentilesTransform';
import { makeAdvancedBattingStat as makeStat } from '@/test/mocks/advancedStats';

describe('transformPercentileStats', () => {
  it('aggregates player stats and calculates percentile ranks', () => {
    const stats: AdvancedBattingStatsTable[] = [
      makeStat({
        avg_exit_velo: 90,
        k_per: 0.2,
        bb_per: 0.1,
        la_sweet_spot_per: 0.3,
        hard_hit_per: 0.4,
        whiff_per: 0.25,
        chase_per: 0.2,
        infield_left_slice: 1,
        infield_center_slice: 2,
      }),
      makeStat({
        avg_exit_velo: 95,
        k_per: 0.18,
        bb_per: 0.12,
        la_sweet_spot_per: 0.35,
        hard_hit_per: 0.45,
        whiff_per: 0.22,
        chase_per: 0.18,
        infield_right_slice: 1,
      }),
      makeStat({
        Batter: 'Smith, Alex',
        BatterTeam: 'AUB_TIG',
        avg_exit_velo: 85,
        k_per: 0.25,
        bb_per: 0.08,
        la_sweet_spot_per: 0.2,
        hard_hit_per: 0.3,
        whiff_per: 0.3,
        chase_per: 0.25,
        infield_left_slice: 0,
        infield_center_slice: 1,
      }),
    ];

    const result = transformPercentileStats(stats, 'Doe, John');
    expect(result).not.toBeNull();
    const player = result!;

    expect(player.avg_exit_velo).toBeCloseTo((90 + 95) / 2, 3);
    expect(player.k_per).toBeCloseTo((0.2 + 0.18) / 2, 3);
    expect(player.bb_per).toBeCloseTo((0.1 + 0.12) / 2, 3);
    expect(player.infield_left_slice).toBe(1);
    expect(player.infield_right_slice).toBe(1);
    expect(player.avg_exit_velo_rank).toBe(100);
    expect(player.k_per_rank).toBe(100);
    expect(player.bb_per_rank).toBe(100);
    expect(player.whiff_per_rank).toBe(100);
    expect(player.chase_per_rank).toBe(100);
  });

  it('returns null when player is missing', () => {
    const stats = [makeStat({ Batter: 'Someone Else', avg_exit_velo: 90 })];
    expect(transformPercentileStats(stats, 'Doe, John')).toBeNull();
  });
});
