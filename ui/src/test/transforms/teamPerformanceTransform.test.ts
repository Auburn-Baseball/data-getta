import { describe, expect, it } from 'vitest';

import { transformTeamPerformance } from '@/transforms/teamPerformanceTransform';
import {
  makeAdvancedBattingStat as makeBatStat,
  makeAdvancedPitchingStat as makePitchStat,
} from '@/test/mocks/advancedStats';
import type { AdvancedBattingStatsTable, AdvancedPitchingStatsTable } from '@/types/db';

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

  it('averages multiple players per team and handles missing metrics gracefully', () => {
    const batting: AdvancedBattingStatsTable[] = [
      // Team AUB_TIG has two players; avg_exit_velo should average (90 + 100) / 2 = 95
      makeBatStat({ BatterTeam: 'AUB_TIG', avg_exit_velo: 90, k_per: 0.2 }),
      makeBatStat({ BatterTeam: 'AUB_TIG', avg_exit_velo: 100, k_per: 0.3 }),
      // LSU_TIG has one
      makeBatStat({ BatterTeam: 'LSU_TIG', avg_exit_velo: 85, k_per: 0.25 }),
    ];

    const pitching: AdvancedPitchingStatsTable[] = [
      // Missing gb_per for AUB_TIG should skip that metric for AUB
      makePitchStat({ PitcherTeam: 'AUB_TIG', avg_fastball_velo: 94, k_per: 0.28 }),
      makePitchStat({ PitcherTeam: 'LSU_TIG', avg_fastball_velo: 92, k_per: 0.24, gb_per: 0.4 }),
    ];

    const rows = transformTeamPerformance(batting, pitching);

    // Averaged exit velo for AUB should beat LSU and be 100 percentile
    const aubExit = rows.find((r) => r.team === 'AUB_TIG' && r.label === 'Exit Velocity');
    expect(aubExit).toBeDefined();
    expect(aubExit!.raw_value).toBeCloseTo(95, 3);
    expect(aubExit!.percentile).toBe(100);

    // K% lower is better for batting: AUB avg k_per = (0.2+0.3)/2 = 0.25 vs LSU 0.25 → ties map to 0/100 by order but exist
    const aubK = rows.find((r) => r.team === 'AUB_TIG' && r.label === 'K%');
    const lsuK = rows.find((r) => r.team === 'LSU_TIG' && r.label === 'K%');
    expect(aubK).toBeDefined();
    expect(lsuK).toBeDefined();

    // gb_per defaults to 0 in mocks, so AUB appears with 0 and lowest percentile
    const aubGb = rows.find((r) => r.team === 'AUB_TIG' && r.label === 'Pitching GB%');
    const lsuGb = rows.find((r) => r.team === 'LSU_TIG' && r.label === 'Pitching GB%');
    expect(aubGb).toBeDefined();
    expect(aubGb!.raw_value).toBe(0);
    expect(aubGb!.percentile).toBe(0);
    expect(lsuGb).toBeDefined();
    expect(lsuGb!.percentile).toBe(100);
  });

  it('assigns 100th percentile for a single team scenario', () => {
    const batting: AdvancedBattingStatsTable[] = [
      makeBatStat({ BatterTeam: 'ONLY_TEAM', avg_exit_velo: 90 }),
    ];
    const pitching: AdvancedPitchingStatsTable[] = [];

    const rows = transformTeamPerformance(batting, pitching);
    const onlyExit = rows.find((r) => r.team === 'ONLY_TEAM' && r.label === 'Exit Velocity');
    expect(onlyExit).toBeDefined();
    expect(onlyExit!.percentile).toBe(100);
  });
});
