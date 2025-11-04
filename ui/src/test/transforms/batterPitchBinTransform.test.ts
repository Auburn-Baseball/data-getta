import { describe, expect, it } from 'vitest';

import { transformBatterPitchBins } from '@/transforms/batterPitchBinTransform';
import { makeBatterPitchBin as makeBin } from '@/test/mocks/batterPitchBins';

describe('transformBatterPitchBins', () => {
  it('aggregates correctly across dates for the same zone', () => {
    // Zone 5 on two different dates
    const z5a = makeBin({
      ZoneId: 5,
      Date: '2024-02-14',
      TotalPitchCount: 5,
      TotalSwingCount: 3,
      TotalHitCount: 2,
      Count_FourSeam: 5,
      SwingCount_FourSeam: 3,
      HitCount_FourSeam: 2,
    });
    const z5b = makeBin({
      ZoneId: 5,
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

    const result = transformBatterPitchBins([z5a, z5b]);
    expect(result).toHaveLength(1);

    const zone5 = result[0];
    expect(zone5.ZoneId).toBe(5);
    expect(zone5.TotalPitchCount).toBe(9);
    expect(zone5.TotalSwingCount).toBe(5);
    expect(zone5.TotalHitCount).toBe(3);
    expect(zone5.Count_FourSeam).toBe(7);
    expect(zone5.Count_Slider).toBe(2);
    expect(zone5.SwingCount_FourSeam).toBe(4);
    expect(zone5.SwingCount_Slider).toBe(1);
    expect(zone5.HitCount_FourSeam).toBe(2);
    expect(zone5.HitCount_Slider).toBe(1);
    // Date range reflects first and last for that zone
    expect(zone5.Date).toBe('2024-02-14 to 2024-02-17');
  });

  it('adds bins that share the same ZoneId even when other zones are present', () => {
    const z5a = makeBin({ ZoneId: 5, Date: '2024-02-14', TotalPitchCount: 2 });
    const z5b = makeBin({ ZoneId: 5, Date: '2024-02-17', TotalPitchCount: 4 });
    const z10 = makeBin({
      ZoneId: 10,
      InZone: false,
      ZoneRow: 0,
      ZoneCol: 0,
      ZoneCell: 0,
      OuterLabel: 'OTL',
      Date: '2024-02-18',
      TotalPitchCount: 3,
      Count_Sinker: 3,
    });

    const result = transformBatterPitchBins([z5a, z10, z5b]);
    expect(result.length).toBe(2);

    const zone5 = result.find((r) => r.ZoneId === 5)!;
    const zone10 = result.find((r) => r.ZoneId === 10)!;

    expect(zone5.TotalPitchCount).toBe(6); // 2 + 4
    expect(zone5.Date).toBe('2024-02-14 to 2024-02-17');

    expect(zone10.TotalPitchCount).toBe(3);
    expect(zone10.Count_Sinker).toBe(3);
    expect(zone10.InZone).toBe(false);
    expect(zone10.Date).toBe('2024-02-18 to 2024-02-18');
  });

  it('only updates the correct ZoneId when multiple different zones exist', () => {
    // Four total zones: 5 (2 bins), 10 (1 bin), 7 (2 bins), 3 (1 bin)
    const z5a = makeBin({ ZoneId: 5, Date: '2024-02-14', TotalPitchCount: 1, Count_FourSeam: 1 });
    const z5b = makeBin({ ZoneId: 5, Date: '2024-02-17', TotalPitchCount: 2, Count_FourSeam: 2 });

    const z10 = makeBin({
      ZoneId: 10,
      InZone: false,
      ZoneRow: 0,
      ZoneCol: 0,
      ZoneCell: 0,
      OuterLabel: 'OTR',
      Date: '2024-02-18',
      TotalPitchCount: 5,
      Count_Cutter: 5,
    });

    const z7a = makeBin({ ZoneId: 7, Date: '2024-02-15', TotalPitchCount: 3, Count_Changeup: 3 });
    const z7b = makeBin({ ZoneId: 7, Date: '2024-02-16', TotalPitchCount: 2, Count_Changeup: 2 });

    const z3 = makeBin({ ZoneId: 3, Date: '2024-02-13', TotalPitchCount: 4, Count_Slider: 4 });

    const result = transformBatterPitchBins([z5a, z5b, z10, z7a, z7b, z3]);
    expect(result.length).toBe(4);

    const zone5 = result.find((r) => r.ZoneId === 5)!;
    const zone10 = result.find((r) => r.ZoneId === 10)!;
    const zone7 = result.find((r) => r.ZoneId === 7)!;
    const zone3 = result.find((r) => r.ZoneId === 3)!;

    // Zone 5 sums only its own bins
    expect(zone5.TotalPitchCount).toBe(3);
    expect(zone5.Count_FourSeam).toBe(3);
    expect(zone5.Date).toBe('2024-02-14 to 2024-02-17');

    // Zone 10 remains independent
    expect(zone10.TotalPitchCount).toBe(5);
    expect(zone10.Count_Cutter).toBe(5);
    expect(zone10.InZone).toBe(false);

    // Zone 7 aggregates just its two bins
    expect(zone7.TotalPitchCount).toBe(5);
    expect(zone7.Count_Changeup).toBe(5);
    expect(zone7.Date).toBe('2024-02-15 to 2024-02-16');

    // Zone 3 single bin
    expect(zone3.TotalPitchCount).toBe(4);
    expect(zone3.Count_Slider).toBe(4);
    expect(zone3.Date).toBe('2024-02-13 to 2024-02-13');
  });
});
