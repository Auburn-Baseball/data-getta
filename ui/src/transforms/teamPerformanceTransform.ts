import { AdvancedBattingStatsTable, AdvancedPitchingStatsTable } from '@/types/db';

export interface TeamPerformanceRow {
  team: string;
  label: string;
  raw_value: number;
  percentile: number;
}

export function transformTeamPerformance(
  battingStats: AdvancedBattingStatsTable[],
  pitchingStats: AdvancedPitchingStatsTable[],
): TeamPerformanceRow[] {
  if (!battingStats.length && !pitchingStats.length) {
    return [];
  }

  // Step 1: Group batting stats by team
  const battingByTeam = new Map<string, AdvancedBattingStatsTable[]>();
  for (const stat of battingStats) {
    const team = stat.BatterTeam;
    if (!battingByTeam.has(team)) {
      battingByTeam.set(team, []);
    }
    battingByTeam.get(team)!.push(stat);
  }

  // Step 2: Group pitching stats by team
  const pitchingByTeam = new Map<string, AdvancedPitchingStatsTable[]>();
  for (const stat of pitchingStats) {
    const team = stat.PitcherTeam;
    if (!pitchingByTeam.has(team)) {
      pitchingByTeam.set(team, []);
    }
    pitchingByTeam.get(team)!.push(stat);
  }

  // Step 3: Calculate team batting averages
  const teamBattingAverages = new Map<string, Record<string, number>>();
  battingByTeam.forEach((players, team) => {
    // Initialize accumulator
    const sums: Record<string, { total: number; count: number }> = {
      avg_exit_velo: { total: 0, count: 0 },
      k_per: { total: 0, count: 0 },
      bb_per: { total: 0, count: 0 },
      la_sweet_spot_per: { total: 0, count: 0 },
      hard_hit_per: { total: 0, count: 0 },
      whiff_per: { total: 0, count: 0 },
      chase_per: { total: 0, count: 0 },
      xba_per: { total: 0, count: 0 },
      xslg_per: { total: 0, count: 0 },
      barrel_per: { total: 0, count: 0 },
    };

    // Sum all values across players
    for (const player of players) {
      for (const key of Object.keys(sums)) {
        const value = player[key as keyof AdvancedBattingStatsTable];
        if (value !== null && value !== undefined && typeof value === 'number') {
          sums[key].total += value;
          sums[key].count++;
        }
      }
    }

    // Calculate averages
    const averages: Record<string, number> = {};
    for (const [key, { total, count }] of Object.entries(sums)) {
      if (count > 0) {
        averages[key] = total / count;
      }
    }

    teamBattingAverages.set(team, averages);
  });

  // Step 4: Calculate team pitching averages
  const teamPitchingAverages = new Map<string, Record<string, number>>();
  pitchingByTeam.forEach((pitchers, team) => {
    // Initialize accumulator
    const sums: Record<string, { total: number; count: number }> = {
      avg_exit_velo: { total: 0, count: 0 },
      k_per: { total: 0, count: 0 },
      bb_per: { total: 0, count: 0 },
      la_sweet_spot_per: { total: 0, count: 0 },
      hard_hit_per: { total: 0, count: 0 },
      whiff_per: { total: 0, count: 0 },
      chase_per: { total: 0, count: 0 },
      avg_fastball_velo: { total: 0, count: 0 },
      gb_per: { total: 0, count: 0 },
      xba_per: { total: 0, count: 0 },
      xslg_per: { total: 0, count: 0 },
      xwoba_per: { total: 0, count: 0 },
    };

    // Sum all values across pitchers
    for (const pitcher of pitchers) {
      for (const key of Object.keys(sums)) {
        const value = pitcher[key as keyof AdvancedPitchingStatsTable];
        if (value !== null && value !== undefined && typeof value === 'number') {
          sums[key].total += value;
          sums[key].count++;
        }
      }
    }

    // Calculate averages
    const averages: Record<string, number> = {};
    for (const [key, { total, count }] of Object.entries(sums)) {
      if (count > 0) {
        averages[key] = total / count;
      }
    }

    teamPitchingAverages.set(team, averages);
  });

  // Step 5: Convert to performance rows with percentile calculations
  const performanceRows: TeamPerformanceRow[] = [];

  // Define metrics to show and their display labels
  const battingMetrics = [
    { key: 'avg_exit_velo', label: 'Exit Velocity', higherIsBetter: true },
    { key: 'k_per', label: 'K%', higherIsBetter: false },
    { key: 'bb_per', label: 'BB%', higherIsBetter: true },
    { key: 'la_sweet_spot_per', label: 'Sweet Spot%', higherIsBetter: true },
    { key: 'hard_hit_per', label: 'Hard Hit%', higherIsBetter: true },
    { key: 'whiff_per', label: 'Whiff%', higherIsBetter: false },
    { key: 'chase_per', label: 'Chase%', higherIsBetter: false },
    { key: 'xba_per', label: 'xBA', higherIsBetter: true },
    { key: 'xslg_per', label: 'xSLG', higherIsBetter: true },
    { key: 'barrel_per', label: 'Barrel%', higherIsBetter: true },
  ];

  const pitchingMetrics = [
    { key: 'avg_fastball_velo', label: 'FB Velo', higherIsBetter: true },
    { key: 'k_per', label: 'K%', higherIsBetter: true },
    { key: 'bb_per', label: 'BB%', higherIsBetter: false },
    { key: 'gb_per', label: 'GB%', higherIsBetter: true },
    { key: 'whiff_per', label: 'Whiff%', higherIsBetter: true },
    { key: 'chase_per', label: 'Chase%', higherIsBetter: true },
    { key: 'xba_per', label: 'xBA', higherIsBetter: false },
    { key: 'xslg_per', label: 'xSLG', higherIsBetter: false },
    { key: 'xwoba_per', label: 'xwOBA', higherIsBetter: false },
  ];

  // Process batting metrics
  for (const { key, label, higherIsBetter } of battingMetrics) {
    // Get all teams' values for this metric
    const values: { team: string; value: number }[] = [];
    teamBattingAverages.forEach((stats, team) => {
      const value = stats[key];
      if (value !== undefined) {
        values.push({ team, value });
      }
    });

    // Skip if no values
    if (values.length === 0) continue;

    // Sort values
    values.sort((a, b) => {
      return higherIsBetter
        ? a.value - b.value // Lower to higher for higher is better
        : b.value - a.value; // Higher to lower for lower is better
    });

    // Calculate percentiles
    const totalTeams = values.length;
    for (let i = 0; i < values.length; i++) {
      const { team, value } = values[i];
      const percentile = Math.round((i / (totalTeams - 1)) * 100);

      performanceRows.push({
        team,
        label,
        raw_value: Number(value.toFixed(3)),
        percentile,
      });
    }
  }

  // Process pitching metrics
  for (const { key, label, higherIsBetter } of pitchingMetrics) {
    // Get all teams' values for this metric
    const values: { team: string; value: number }[] = [];
    teamPitchingAverages.forEach((stats, team) => {
      const value = stats[key];
      if (value !== undefined) {
        values.push({ team, value });
      }
    });

    // Skip if no values
    if (values.length === 0) continue;

    // Sort values
    values.sort((a, b) => {
      return higherIsBetter
        ? a.value - b.value // Lower to higher for higher is better
        : b.value - a.value; // Higher to lower for lower is better
    });

    // Calculate percentiles
    const totalTeams = values.length;
    for (let i = 0; i < values.length; i++) {
      const { team, value } = values[i];
      const percentile = Math.round((i / (totalTeams - 1)) * 100);

      performanceRows.push({
        team,
        label: `Pitching ${label}`, // Prefix with "Pitching" to differentiate
        raw_value: Number(value.toFixed(3)),
        percentile,
      });
    }
  }

  return performanceRows;
}
