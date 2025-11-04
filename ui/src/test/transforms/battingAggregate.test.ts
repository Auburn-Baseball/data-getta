import { describe, it, expect } from 'vitest';

import {
  aggregateBatterStats,
  computeTotals,
  computeRatesFromTotals,
} from '@/transforms/batting/aggregate';
import { createBatterStatsSummary } from '@/transforms/batting/summary';
import type { BatterStatsTable } from '@/types/db';
import { makeBatterStat } from '@/test/mocks/batterStats';

describe('aggregateBatterStats and helpers', () => {
  describe('Basic Aggregation', () => {
    it('sums counting stats and excludes practice rows by pre-filter', () => {
      // Arrange
      const game1 = makeBatterStat({
        hits: 2,
        at_bats: 4,
        walks: 1,
        strikeouts: 1,
        plate_appearances: 5,
        total_bases: 5,
        games: 1,
        batted_balls: 3,
        total_exit_velo: 270,
        chase_percentage: 0.2,
        in_zone_whiff_percentage: 0.25,
        k_per: 1,
        bb_per: 1,
        avg_exit_velo: 90,
      });
      const game2Practice = makeBatterStat({
        is_practice: true,
        hits: 10,
        at_bats: 10,
        walks: 5,
        strikeouts: 0,
        plate_appearances: 15,
        total_bases: 10,
        games: 1,
      });

      const input = [game1, game2Practice];
      const filtered = input.filter((r) => r.is_practice !== true);

      // Act
      const agg = aggregateBatterStats(filtered)!;

      // Assert
      expect(agg.hits).toBe(2);
      expect(agg.at_bats).toBe(4);
      expect(agg.walks).toBe(1);
      expect(agg.strikeouts).toBe(1);
      expect(agg.total_bases).toBe(5);
      expect(agg.plate_appearances).toBe(5);
      expect(agg.games).toBe(1);
    });
  });

  describe('Weighted Metrics', () => {
    it('uses plate_appearances for chase%, strikes for whiff%, and batted_balls for avg EV', () => {
      // Arrange
      const a = makeBatterStat({
        plate_appearances: 10,
        strikes: 8,
        batted_balls: 2,
        total_exit_velo: 180,
        chase_percentage: 0.2,
        in_zone_whiff_percentage: 0.25,
      }); // ev=90
      const b = makeBatterStat({
        plate_appearances: 5,
        strikes: 2,
        batted_balls: 1,
        total_exit_velo: 100,
        chase_percentage: 0.1,
        in_zone_whiff_percentage: 0.5,
      }); // ev=100

      // Act
      const totals = computeTotals([a, b]);
      const rates = computeRatesFromTotals(totals);

      // Assert
      // chase% = (0.2*10 + 0.1*5) / (10+5) = (2 + 0.5)/15 = 0.1666..
      expect(rates.chasePercentage).toBeCloseTo(0.1667, 4);
      // whiff% = (0.25*8 + 0.5*2) / (8+2) = (2 + 1)/10 = 0.3
      expect(rates.whiffPercentage).toBeCloseTo(0.3, 4);
      // avg EV = (180 + 100) / (2 + 1) = 280/3 ≈ 93.333
      expect(rates.averageExitVelo).toBeCloseTo(93.3333, 3);
    });

    it('falls back to weighted avg EV when batted_balls = 0 (uses PA/AB/games as weight)', () => {
      // Arrange: both have zero batted_balls; use PA to weight
      const a = makeBatterStat({
        plate_appearances: 10,
        batted_balls: 0,
        avg_exit_velo: 90,
      });
      const b = makeBatterStat({
        plate_appearances: 20,
        batted_balls: 0,
        avg_exit_velo: 100,
      });

      // Act
      const totals = computeTotals([a, b]);
      const rates = computeRatesFromTotals(totals);

      // Assert: weighted by PA => (90*10 + 100*20) / (10+20) = (900 + 2000)/30 = 96.6667
      expect(rates.averageExitVelo).toBeCloseTo(96.6667, 3);
    });
  });

  describe('Rate Calculations', () => {
    it('computes AVG, OBP, SLG, OPS, ISO with HBP and sacrifices present', () => {
      // Arrange
      const row = makeBatterStat({
        hits: 3,
        at_bats: 10,
        walks: 2,
        hit_by_pitch: 1,
        sacrifice: 1,
        total_bases: 7, // e.g., 1B + 2B + HR => 1 + 2 + 4 = 7
        plate_appearances: 14, // AB + BB + HBP + SF
        games: 1,
      });

      // Act
      const totals = computeTotals([row]);
      const r = computeRatesFromTotals(totals);

      // Assert
      const avg = 3 / 10; // 0.3
      const obp = (3 + 2 + 1) / (10 + 2 + 1 + 1); // 6 / 14 = 0.42857
      const slg = 7 / 10; // 0.7
      const ops = obp + slg; // 1.12857
      const iso = slg - avg; // 0.4

      expect(r.battingAverage).toBeCloseTo(avg, 4);
      expect(r.onBasePercentage).toBeCloseTo(obp, 4);
      expect(r.sluggingPercentage).toBeCloseTo(slg, 4);
      expect(r.ops).toBeCloseTo(ops, 4);
      expect(r.isolatedPower).toBeCloseTo(iso, 4);
    });

    it('protects against division by zero when denominators are 0', () => {
      // Arrange: everything zero/undefined
      const empty = makeBatterStat({
        hits: 0,
        at_bats: 0,
        walks: 0,
        plate_appearances: 0,
        total_bases: 0,
        strikeouts: 0,
        games: 0,
      });

      // Act
      const totals = computeTotals([empty]);
      const r = computeRatesFromTotals(totals);

      // Assert: all zero, not NaN
      expect(r.battingAverage).toBe(0);
      expect(r.onBasePercentage).toBe(0);
      expect(r.sluggingPercentage).toBe(0);
      expect(r.ops).toBe(0);
      expect(r.isolatedPower).toBe(0);
      expect(r.kPercentage).toBe(0);
      expect(r.bbPercentage).toBe(0);
    });
  });

  describe('Derived and Per-Game', () => {
    it('computes k% and bb% with PA denominator; k_per/bb_per per game and their weighted variants', () => {
      // Arrange
      const g1 = makeBatterStat({
        plate_appearances: 10,
        strikeouts: 3,
        walks: 1,
        games: 1,
        k_per: 3,
        bb_per: 1,
      });
      const g2 = makeBatterStat({
        plate_appearances: 5,
        strikeouts: 1,
        walks: 2,
        games: 2,
        k_per: 0.5,
        bb_per: 1,
      });

      // Act
      const totals = computeTotals([g1, g2]);
      const r = computeRatesFromTotals(totals);

      // Assert
      // k% = (3+1)/(10+5)=4/15=0.2666.., bb% = (1+2)/15 = 0.2
      expect(r.kPercentage).toBeCloseTo(4 / 15, 4);
      expect(r.bbPercentage).toBeCloseTo(0.2, 4);

      // Per-game simple averages (from totals):
      // games = 1 + 2 = 3; K/G = (3+1)/3 = 1.3333.., BB/G = (1+2)/3 = 1
      // Weighted variants using provided k_per/bb_per with games weight:
      // k_per weighted: (3*1 + 0.5*2) / (1+2) = (3 + 1)/3 = 1.3333..
      // bb_per weighted: (1*1 + 1*2) / 3 = 1
      expect(r.averagedKPer).toBeCloseTo(1.3333, 3);
      expect(r.averagedBbPer).toBeCloseTo(1.0, 3);
    });
  });

  describe('Edge & Fallback Scenarios', () => {
    it('handles missing fields without NaN and falls back games = rows.length when games are zero', () => {
      // Arrange: games are 0 on each row
      const r1 = makeBatterStat({
        games: 0,
        at_bats: 0,
        hits: 0,
        walks: 0,
        plate_appearances: 0,
      });
      const r2 = makeBatterStat({
        games: 0,
        at_bats: 0,
        hits: 0,
        walks: 0,
        plate_appearances: 0,
      });

      // Act
      const totals = computeTotals([r1, r2]);
      const r = computeRatesFromTotals(totals);

      // Assert
      expect(totals.games).toBe(2); // fallback to rows.length
      expect(r.battingAverage).toBe(0);
      expect(r.onBasePercentage).toBe(0);
      expect(r.sluggingPercentage).toBe(0);
      expect(r.ops).toBe(0);
    });

    it('treats missing total_bases as 0 (no implicit derivation) and computes SLG accordingly', () => {
      // Arrange: one row missing total_bases, one with value
      const a = makeBatterStat({ at_bats: 4, hits: 2, total_bases: undefined });
      const b = makeBatterStat({ at_bats: 6, hits: 3, total_bases: 7 });

      // Act
      const totals = computeTotals([a, b]);
      const r = computeRatesFromTotals(totals);

      // Assert
      // SLG uses provided total_bases sum: (0 + 7) / (4 + 6) = 0.7
      expect(r.sluggingPercentage).toBeCloseTo(0.7, 4);
    });
  });

  describe('Summary Validation', () => {
    it('returns a correct multi-player summary row', () => {
      // Arrange
      const p1 = makeBatterStat({
        hits: 10,
        at_bats: 30,
        total_bases: 40,
        walks: 5,
        strikeouts: 6,
        plate_appearances: 38,
        hit_by_pitch: 1,
        sacrifice: 2,
      });
      const p2 = makeBatterStat({
        hits: 5,
        at_bats: 20,
        total_bases: 22,
        walks: 4,
        strikeouts: 4,
        plate_appearances: 26,
        hit_by_pitch: 0,
        sacrifice: 1,
      });
      const players: BatterStatsTable[] = [p1, p2];

      // Act
      const summary = createBatterStatsSummary(players);

      // Assert (manually computed expectations)
      expect(summary.hits).toBe(15);
      expect(summary.at_bats).toBe(50);
      expect(summary.total_bases).toBe(62);
      expect(summary.walks).toBe(9);
      expect(summary.strikeouts).toBe(10);

      const battingAvg = 15 / 50;
      const onBasePct = (15 + 9 + 1) / (50 + 9 + 1 + 3);
      const sluggingPct = 62 / 50;

      expect(summary.batting_average).toBeCloseTo(battingAvg, 4);
      expect(summary.on_base_percentage).toBeCloseTo(onBasePct, 4);
      expect(summary.slugging_percentage).toBeCloseTo(sluggingPct, 4);
    });
  });
});
