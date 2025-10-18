import { BatterPitchBinsTable } from '@/types/db';

/**
 * Groups batter pitch data by zone and aggregates counts across date ranges
 */
export function transformBatterPitchBins(bins: BatterPitchBinsTable[]): BatterPitchBinsTable[] {
  if (!bins || bins.length === 0) return [];

  // Group by ZoneId - each unique zone gets one entry
  const zoneMap = new Map<number, BatterPitchBinsTable[]>();

  // Group bins by ZoneId
  for (const bin of bins) {
    const zoneId = bin.ZoneId;
    if (!zoneMap.has(zoneId)) {
      zoneMap.set(zoneId, []);
    }
    zoneMap.get(zoneId)!.push(bin);
  }

  // Create aggregated data for each zone
  const results: BatterPitchBinsTable[] = [];

  zoneMap.forEach((zoneBins) => {
    if (zoneBins.length === 0) return;

    // Use the first bin as a template
    const baseBin = zoneBins[0];

    // Create aggregated bin
    const aggregated: BatterPitchBinsTable = {
      // Metadata stays the same
      BatterTeam: baseBin.BatterTeam,
      Batter: baseBin.Batter,
      // Use date range as the date (not shown in UI)
      Date: `${zoneBins[0].Date} to ${zoneBins[zoneBins.length - 1].Date}`,
      ZoneId: baseBin.ZoneId,
      InZone: baseBin.InZone,
      ZoneRow: baseBin.ZoneRow,
      ZoneCol: baseBin.ZoneCol,
      ZoneCell: baseBin.ZoneCell,
      OuterLabel: baseBin.OuterLabel,
      ZoneVersion: baseBin.ZoneVersion,

      // Initialize counters at zero
      TotalPitchCount: 0,
      TotalSwingCount: 0,
      TotalHitCount: 0,

      // Pitch counts
      Count_FourSeam: 0,
      Count_Sinker: 0,
      Count_Slider: 0,
      Count_Curveball: 0,
      Count_Changeup: 0,
      Count_Cutter: 0,
      Count_Splitter: 0,
      Count_Other: 0,

      // Swing counts
      SwingCount_FourSeam: 0,
      SwingCount_Sinker: 0,
      SwingCount_Slider: 0,
      SwingCount_Curveball: 0,
      SwingCount_Changeup: 0,
      SwingCount_Cutter: 0,
      SwingCount_Splitter: 0,
      SwingCount_Other: 0,

      // Hit counts
      HitCount_FourSeam: 0,
      HitCount_Sinker: 0,
      HitCount_Slider: 0,
      HitCount_Curveball: 0,
      HitCount_Changeup: 0,
      HitCount_Cutter: 0,
      HitCount_Splitter: 0,
      HitCount_Other: 0,
    };

    // Sum all counts
    for (const bin of zoneBins) {
      // Total counts
      aggregated.TotalPitchCount += bin.TotalPitchCount;
      aggregated.TotalSwingCount += bin.TotalSwingCount;
      aggregated.TotalHitCount += bin.TotalHitCount;

      // Pitch counts
      aggregated.Count_FourSeam += bin.Count_FourSeam;
      aggregated.Count_Sinker += bin.Count_Sinker;
      aggregated.Count_Slider += bin.Count_Slider;
      aggregated.Count_Curveball += bin.Count_Curveball;
      aggregated.Count_Changeup += bin.Count_Changeup;
      aggregated.Count_Cutter += bin.Count_Cutter;
      aggregated.Count_Splitter += bin.Count_Splitter;
      aggregated.Count_Other += bin.Count_Other;

      // Swing counts
      aggregated.SwingCount_FourSeam += bin.SwingCount_FourSeam;
      aggregated.SwingCount_Sinker += bin.SwingCount_Sinker;
      aggregated.SwingCount_Slider += bin.SwingCount_Slider;
      aggregated.SwingCount_Curveball += bin.SwingCount_Curveball;
      aggregated.SwingCount_Changeup += bin.SwingCount_Changeup;
      aggregated.SwingCount_Cutter += bin.SwingCount_Cutter;
      aggregated.SwingCount_Splitter += bin.SwingCount_Splitter;
      aggregated.SwingCount_Other += bin.SwingCount_Other;

      // Hit counts
      aggregated.HitCount_FourSeam += bin.HitCount_FourSeam;
      aggregated.HitCount_Sinker += bin.HitCount_Sinker;
      aggregated.HitCount_Slider += bin.HitCount_Slider;
      aggregated.HitCount_Curveball += bin.HitCount_Curveball;
      aggregated.HitCount_Changeup += bin.HitCount_Changeup;
      aggregated.HitCount_Cutter += bin.HitCount_Cutter;
      aggregated.HitCount_Splitter += bin.HitCount_Splitter;
      aggregated.HitCount_Other += bin.HitCount_Other;
    }

    results.push(aggregated);
  });

  // Sort by ZoneId for consistency
  return results.sort((a, b) => a.ZoneId - b.ZoneId);
}
