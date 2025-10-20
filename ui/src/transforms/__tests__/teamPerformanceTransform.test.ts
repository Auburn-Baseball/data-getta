import { describe, expect, it } from 'vitest';

import { transformTeamPerformance } from '@/transforms/teamPerformanceTransform';
import type { AdvancedBattingStatsTable, AdvancedPitchingStatsTable } from '@/types/db';

const makeBatStat = (overrides: Partial<AdvancedBattingStatsTable>): AdvancedBattingStatsTable => ({
  Batter: 'Sample',
  BatterTeam: 'AUB_TIG',
  Year: 2024,
  avg_exit_velo: 0,
  k_per: 0,
  bb_per: 0,
  la_sweet_spot_per: 0,
  hard_hit_per: 0,
  whiff_per: 0,
  chase_per: 0,
  xba_per: 0,
  xslg_per: 0,
  barrel_per: 0,
  avg_exit_velo_rank: null,
  k_per_rank: null,
  bb_per_rank: null,
  la_sweet_spot_per_rank: null,
  hard_hit_per_rank: null,
  whiff_per_rank: null,
  chase_per_rank: null,
  ...overrides,
});

const makePitchStat = (
  overrides: Partial<AdvancedPitchingStatsTable>,
): AdvancedPitchingStatsTable => ({
  Pitcher: 'Sample',
  PitcherTeam: 'AUB_TIG',
  Year: 2024,
  avg_exit_velo: 0,
  avg_fastball_velo: 0,
  k_per: 0,
  bb_per: 0,
  la_sweet_spot_per: 0,
  hard_hit_per: 0,
  gb_per: 0,
  whiff_per: 0,
  chase_per: 0,
  xba_per: 0,
  xslg_per: 0,
  xwoba_per: 0,
  avg_exit_velo_rank: null,
  k_per_rank: null,
  bb_per_rank: null,
  la_sweet_spot_per_rank: null,
  hard_hit_per_rank: null,
  whiff_per_rank: null,
  chase_per_rank: null,
  ...overrides,
});

describe('transformTeamPerformance', () => {
  it('computes team level percentiles for batting and pitching metrics', () => {
    const batting: AdvancedBattingStatsTable[] = [
      makeBatStat({
        BatterTeam: 'AUB_TIG',
        avg_exit_velo: 90,
        k_per: 0.2,
        bb_per: 0.1,
        la_sweet_spot_per: 0.3,
        hard_hit_per: 0.4,
        whiff_per: 0.25,
        chase_per: 0.2,
        xba_per: 0.28,
        xslg_per: 0.45,
        barrel_per: 0.1,
      }),
      makeBatStat({
        BatterTeam: 'LSU_TIG',
        avg_exit_velo: 85,
        k_per: 0.3,
        bb_per: 0.05,
        la_sweet_spot_per: 0.2,
        hard_hit_per: 0.3,
        whiff_per: 0.3,
        chase_per: 0.25,
        xba_per: 0.24,
        xslg_per: 0.4,
        barrel_per: 0.05,
      }),
    ];

    const pitching: AdvancedPitchingStatsTable[] = [
      makePitchStat({
        PitcherTeam: 'AUB_TIG',
        avg_fastball_velo: 94,
        k_per: 0.28,
        bb_per: 0.07,
        gb_per: 0.48,
        whiff_per: 0.32,
        chase_per: 0.27,
        xba_per: 0.22,
        xslg_per: 0.35,
        xwoba_per: 0.3,
      }),
      makePitchStat({
        PitcherTeam: 'LSU_TIG',
        avg_fastball_velo: 92,
        k_per: 0.24,
        bb_per: 0.1,
        gb_per: 0.4,
        whiff_per: 0.28,
        chase_per: 0.22,
        xba_per: 0.26,
        xslg_per: 0.4,
        xwoba_per: 0.35,
      }),
    ];

    const rows = transformTeamPerformance(batting, pitching);
    expect(rows.length).toBeGreaterThan(0);

    const exitVelocity = rows.find((r) => r.team === 'AUB_TIG' && r.label === 'Exit Velocity');
    expect(exitVelocity).toBeDefined();
    expect(exitVelocity!.percentile).toBe(100);

    const aubKPercent = rows.find((r) => r.team === 'AUB_TIG' && r.label === 'K%');
    expect(aubKPercent).toBeDefined();
    expect(aubKPercent!.percentile).toBe(100);

    const lsuChase = rows.find((r) => r.team === 'LSU_TIG' && r.label === 'Chase%');
    expect(lsuChase).toBeDefined();
    expect(lsuChase!.percentile).toBe(0);

    const pitchingFbVelo = rows.find((r) => r.team === 'AUB_TIG' && r.label === 'Pitching FB Velo');
    expect(pitchingFbVelo).toBeDefined();
    expect(pitchingFbVelo!.percentile).toBe(100);

    const pitchingXba = rows.find((r) => r.team === 'LSU_TIG' && r.label === 'Pitching xBA');
    expect(pitchingXba).toBeDefined();
    expect(pitchingXba!.percentile).toBe(0);
  });
});
