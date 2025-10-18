import { PitcherPitchBinsTable } from '@/types/schemas';

/**
 * Groups pitch data by zone and aggregates counts across date ranges
 */
export function transformPitcherPitchBins(bins: PitcherPitchBinsTable[]): PitcherPitchBinsTable[] {
  if (!bins || bins.length === 0) return [];

  // Group by ZoneId - each unique zone gets one entry
  const zoneMap = new Map<number, PitcherPitchBinsTable[]>();

  // Group bins by ZoneId
  for (const bin of bins) {
    const zoneId = bin.ZoneId;
    if (!zoneMap.has(zoneId)) {
      zoneMap.set(zoneId, []);
    }
    zoneMap.get(zoneId)!.push(bin);
  }

  // Create aggregated data for each zone
  const results: PitcherPitchBinsTable[] = [];

  zoneMap.forEach((zoneBins) => {
    if (zoneBins.length === 0) return;

    // Use the first bin as a template
    const baseBin = zoneBins[0];

    // Create aggregated bin
    const aggregated: PitcherPitchBinsTable = {
      // Metadata stays the same
      PitcherTeam: baseBin.PitcherTeam,
      Pitcher: baseBin.Pitcher,
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
    };

    // Sum all counts
    for (const bin of zoneBins) {
      aggregated.TotalPitchCount += bin.TotalPitchCount;

      // Total pitch counts
      aggregated.Count_FourSeam += bin.Count_FourSeam;
      aggregated.Count_Sinker += bin.Count_Sinker;
      aggregated.Count_Slider += bin.Count_Slider;
      aggregated.Count_Curveball += bin.Count_Curveball;
      aggregated.Count_Changeup += bin.Count_Changeup;
      aggregated.Count_Cutter += bin.Count_Cutter;
      aggregated.Count_Splitter += bin.Count_Splitter;
      aggregated.Count_Other += bin.Count_Other;

      // Left-handed batter counts
      aggregated.Count_L_FourSeam += bin.Count_L_FourSeam;
      aggregated.Count_L_Sinker += bin.Count_L_Sinker;
      aggregated.Count_L_Slider += bin.Count_L_Slider;
      aggregated.Count_L_Curveball += bin.Count_L_Curveball;
      aggregated.Count_L_Changeup += bin.Count_L_Changeup;
      aggregated.Count_L_Cutter += bin.Count_L_Cutter;
      aggregated.Count_L_Splitter += bin.Count_L_Splitter;
      aggregated.Count_L_Other += bin.Count_L_Other;

      // Right-handed batter counts
      aggregated.Count_R_FourSeam += bin.Count_R_FourSeam;
      aggregated.Count_R_Sinker += bin.Count_R_Sinker;
      aggregated.Count_R_Slider += bin.Count_R_Slider;
      aggregated.Count_R_Curveball += bin.Count_R_Curveball;
      aggregated.Count_R_Changeup += bin.Count_R_Changeup;
      aggregated.Count_R_Cutter += bin.Count_R_Cutter;
      aggregated.Count_R_Splitter += bin.Count_R_Splitter;
      aggregated.Count_R_Other += bin.Count_R_Other;
    }

    results.push(aggregated);
  });

  // Sort by ZoneId for consistency
  return results.sort((a, b) => a.ZoneId - b.ZoneId);
}
