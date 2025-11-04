import { describe, expect, it } from 'vitest';

import { transformPitcherPitchBins } from '@/transforms/pitcherPitchBinTransform';
import type { PitcherPitchBinsTable } from '@/types/db';

const makeBin = (overrides: Partial<PitcherPitchBinsTable>): PitcherPitchBinsTable => ({
  PitcherTeam: 'AUB_TIG',
  Date: '2024-02-16',
  Pitcher: 'Ace, John',
  ZoneId: 5,
  InZone: true,
  ZoneRow: 2,
  ZoneCol: 2,
  ZoneCell: 5,
  OuterLabel: 'NA',
  ZoneVersion: 'v1',
  TotalPitchCount: 0,
  Count_FourSeam: 0,
  Count_Sinker: 0,
  Count_Slider: 0,
  Count_Curveball: 0,
  Count_Changeup: 0,
  Count_Cutter: 0,
  Count_Splitter: 0,
  Count_Other: 0,
  Count_L_FourSeam: 0,
  Count_L_Sinker: 0,
  Count_L_Slider: 0,
  Count_L_Curveball: 0,
  Count_L_Changeup: 0,
  Count_L_Cutter: 0,
  Count_L_Splitter: 0,
  Count_L_Other: 0,
  Count_R_FourSeam: 0,
  Count_R_Sinker: 0,
  Count_R_Slider: 0,
  Count_R_Curveball: 0,
  Count_R_Changeup: 0,
  Count_R_Cutter: 0,
  Count_R_Splitter: 0,
  Count_R_Other: 0,
  ...overrides,
});

describe('transformPitcherPitchBins', () => {
  it('aggregates pitcher pitch bins by zone and batter handedness', () => {
    const bin1 = makeBin({
      TotalPitchCount: 6,
      Count_FourSeam: 4,
      Count_L_FourSeam: 3,
      Count_R_FourSeam: 1,
      Count_Slider: 2,
      Count_R_Slider: 2,
    });

    const bin2 = makeBin({
      Date: '2024-02-17',
      TotalPitchCount: 5,
      Count_FourSeam: 1,
      Count_L_FourSeam: 0,
      Count_R_FourSeam: 1,
      Count_Sinker: 4,
      Count_L_Sinker: 2,
      Count_R_Sinker: 2,
    });

    const otherZone = makeBin({
      ZoneId: 11,
      InZone: false,
      ZoneRow: 0,
      ZoneCol: 0,
      ZoneCell: 0,
      OuterLabel: 'OTR',
      TotalPitchCount: 3,
      Count_Cutter: 3,
      Count_R_Cutter: 3,
    });

    const result = transformPitcherPitchBins([bin1, bin2, otherZone]);
    expect(result).toHaveLength(2);

    const inner = result.find((r) => r.ZoneId === 5)!;
    expect(inner.TotalPitchCount).toBe(11);
    expect(inner.Count_FourSeam).toBe(5);
    expect(inner.Count_Sinker).toBe(4);
    expect(inner.Count_L_FourSeam).toBe(3);
    expect(inner.Count_R_FourSeam).toBe(2);
    expect(inner.Count_R_Slider).toBe(2);
    expect(inner.Date).toBe('2024-02-16 to 2024-02-17');

    const outer = result.find((r) => r.ZoneId === 11)!;
    expect(outer.TotalPitchCount).toBe(3);
    expect(outer.Count_Cutter).toBe(3);
    expect(outer.Count_R_Cutter).toBe(3);
    expect(outer.InZone).toBe(false);
  });
});
