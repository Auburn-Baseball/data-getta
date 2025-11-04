import { describe, expect, it } from 'vitest';

import { transformBatterPitchBins } from '@/transforms/batterPitchBinTransform';
import type { BatterPitchBinsTable } from '@/types/db';

const makeBin = (overrides: Partial<BatterPitchBinsTable>): BatterPitchBinsTable => ({
  BatterTeam: 'AUB_TIG',
  Date: '2024-02-16',
  Batter: 'Doe, John',
  ZoneId: 5,
  InZone: true,
  ZoneRow: 2,
  ZoneCol: 2,
  ZoneCell: 5,
  OuterLabel: 'NA',
  ZoneVersion: 'v1',
  TotalPitchCount: 0,
  TotalSwingCount: 0,
  TotalHitCount: 0,
  Count_FourSeam: 0,
  Count_Sinker: 0,
  Count_Slider: 0,
  Count_Curveball: 0,
  Count_Changeup: 0,
  Count_Cutter: 0,
  Count_Splitter: 0,
  Count_Other: 0,
  SwingCount_FourSeam: 0,
  SwingCount_Sinker: 0,
  SwingCount_Slider: 0,
  SwingCount_Curveball: 0,
  SwingCount_Changeup: 0,
  SwingCount_Cutter: 0,
  SwingCount_Splitter: 0,
  SwingCount_Other: 0,
  HitCount_FourSeam: 0,
  HitCount_Sinker: 0,
  HitCount_Slider: 0,
  HitCount_Curveball: 0,
  HitCount_Changeup: 0,
  HitCount_Cutter: 0,
  HitCount_Splitter: 0,
  HitCount_Other: 0,
  ...overrides,
});

describe('transformBatterPitchBins', () => {
  it('aggregates bins by zone and sums pitch, swing, and hit counts', () => {
    const bin1 = makeBin({
      TotalPitchCount: 5,
      TotalSwingCount: 3,
      TotalHitCount: 2,
      Count_FourSeam: 5,
      SwingCount_FourSeam: 3,
      HitCount_FourSeam: 2,
    });
    const bin2 = makeBin({
      Date: '2024-02-17',
      TotalPitchCount: 4,
      TotalSwingCount: 2,
      TotalHitCount: 1,
      Count_FourSeam: 2,
      Count_Slider: 2,
      SwingCount_FourSeam: 1,
      SwingCount_Slider: 1,
      HitCount_Slider: 1,
    });
    const outerBin = makeBin({
      ZoneId: 10,
      InZone: false,
      ZoneRow: 0,
      ZoneCol: 0,
      ZoneCell: 0,
      OuterLabel: 'OTL',
      TotalPitchCount: 3,
      Count_Sinker: 3,
    });

    const result = transformBatterPitchBins([bin1, bin2, outerBin]);
    expect(result).toHaveLength(2);

    const inner = result.find((r) => r.ZoneId === 5)!;
    expect(inner.TotalPitchCount).toBe(9);
    expect(inner.TotalSwingCount).toBe(5);
    expect(inner.TotalHitCount).toBe(3);
    expect(inner.Count_FourSeam).toBe(7);
    expect(inner.Count_Slider).toBe(2);
    expect(inner.SwingCount_FourSeam).toBe(4);
    expect(inner.SwingCount_Slider).toBe(1);
    expect(inner.HitCount_FourSeam).toBe(2);
    expect(inner.HitCount_Slider).toBe(1);
    expect(inner.Date).toBe('2024-02-16 to 2024-02-17');

    const outer = result.find((r) => r.ZoneId === 10)!;
    expect(outer.TotalPitchCount).toBe(3);
    expect(outer.Count_Sinker).toBe(3);
    expect(outer.InZone).toBe(false);
  });
});
