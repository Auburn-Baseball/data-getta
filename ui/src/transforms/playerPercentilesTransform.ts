import { AdvancedBattingStatsTable } from '@/types/db';

/**
 * Transforms advanced batting stats data for a specific player
 * and calculates percentile ranks within the team
 */
export function transformPercentileStats(
  allPlayerStats: AdvancedBattingStatsTable[],
  playerName: string,
): AdvancedBattingStatsTable | null {
  if (!allPlayerStats || allPlayerStats.length === 0) {
    return null;
  }

  // Find the target player's stats
  const playerStats = allPlayerStats.find((player) => player.Batter === playerName);
  if (!playerStats) {
    return null;
  }

  // Group data by player
  const playerMap = new Map<string, AdvancedBattingStatsTable[]>();
  for (const stat of allPlayerStats) {
    const key = stat.Batter;
    if (!playerMap.has(key)) {
      playerMap.set(key, []);
    }
    playerMap.get(key)!.push(stat);
  }

  // Aggregate stats for each player
  const aggregatedPlayers: AdvancedBattingStatsTable[] = [];

  playerMap.forEach((playerData) => {
    if (playerData.length === 0) return;

    // Use first record as base
    const base = playerData[0];

    // Start aggregation with base values - create a proper copy to avoid modifying original
    const aggregated: AdvancedBattingStatsTable = {
      ...base,
      // Remove any fields that shouldn't be in the final object
    };

    // Initialize numeric values to be averaged
    let avgExitVeloCount = 0;
    let totalExitVelo = 0;
    let kPerSum = 0;
    let bbPerSum = 0;
    let laSweetSpotPerSum = 0;
    let hardHitPerSum = 0;
    let whiffPerSum = 0;
    let chasePerSum = 0;

    // Sum counts for spray chart
    let infieldLeftSum = 0;
    let infieldLcSum = 0;
    let infieldCenterSum = 0;
    let infieldRcSum = 0;
    let infieldRightSum = 0;

    // Process all player records
    for (const record of playerData) {
      // Accumulate exit velocity
      if (typeof record.avg_exit_velo === 'number') {
        totalExitVelo += record.avg_exit_velo;
        avgExitVeloCount++;
      }

      // Accumulate percentages
      if (typeof record.k_per === 'number') kPerSum += record.k_per;
      if (typeof record.bb_per === 'number') bbPerSum += record.bb_per;
      if (typeof record.la_sweet_spot_per === 'number')
        laSweetSpotPerSum += record.la_sweet_spot_per;
      if (typeof record.hard_hit_per === 'number') hardHitPerSum += record.hard_hit_per;
      if (typeof record.whiff_per === 'number') whiffPerSum += record.whiff_per;
      if (typeof record.chase_per === 'number') chasePerSum += record.chase_per;

      // Accumulate spray chart data
      if (typeof record.infield_left_slice === 'number')
        infieldLeftSum += record.infield_left_slice;
      if (typeof record.infield_lc_slice === 'number') infieldLcSum += record.infield_lc_slice;
      if (typeof record.infield_center_slice === 'number')
        infieldCenterSum += record.infield_center_slice;
      if (typeof record.infield_rc_slice === 'number') infieldRcSum += record.infield_rc_slice;
      if (typeof record.infield_right_slice === 'number')
        infieldRightSum += record.infield_right_slice;
    }

    // Calculate averages
    aggregated.avg_exit_velo = avgExitVeloCount > 0 ? totalExitVelo / avgExitVeloCount : null;
    aggregated.k_per = playerData.length > 0 ? kPerSum / playerData.length : null;
    aggregated.bb_per = playerData.length > 0 ? bbPerSum / playerData.length : null;
    aggregated.la_sweet_spot_per =
      playerData.length > 0 ? laSweetSpotPerSum / playerData.length : null;
    aggregated.hard_hit_per = playerData.length > 0 ? hardHitPerSum / playerData.length : null;
    aggregated.whiff_per = playerData.length > 0 ? whiffPerSum / playerData.length : null;
    aggregated.chase_per = playerData.length > 0 ? chasePerSum / playerData.length : null;

    // Set spray chart totals
    aggregated.infield_left_slice = infieldLeftSum || undefined;
    aggregated.infield_lc_slice = infieldLcSum || undefined;
    aggregated.infield_center_slice = infieldCenterSum || undefined;
    aggregated.infield_rc_slice = infieldRcSum || undefined;
    aggregated.infield_right_slice = infieldRightSum || undefined;

    aggregatedPlayers.push(aggregated);
  });

  // Find our target player in aggregated data
  const targetPlayer = aggregatedPlayers.find((p) => p.Batter === playerName);
  if (!targetPlayer) return null;

  // Calculate percentile ranks for the target player
  targetPlayer.avg_exit_velo_rank = calculatePercentileRank(
    aggregatedPlayers,
    'avg_exit_velo',
    targetPlayer.avg_exit_velo,
    true,
  );

  targetPlayer.k_per_rank = calculatePercentileRank(
    aggregatedPlayers,
    'k_per',
    targetPlayer.k_per,
    false, // Lower is better for K%
  );

  targetPlayer.bb_per_rank = calculatePercentileRank(
    aggregatedPlayers,
    'bb_per',
    targetPlayer.bb_per,
    true,
  );

  targetPlayer.la_sweet_spot_per_rank = calculatePercentileRank(
    aggregatedPlayers,
    'la_sweet_spot_per',
    targetPlayer.la_sweet_spot_per,
    true,
  );

  targetPlayer.hard_hit_per_rank = calculatePercentileRank(
    aggregatedPlayers,
    'hard_hit_per',
    targetPlayer.hard_hit_per,
    true,
  );

  targetPlayer.whiff_per_rank = calculatePercentileRank(
    aggregatedPlayers,
    'whiff_per',
    targetPlayer.whiff_per,
    false, // Lower is better for whiff%
  );

  targetPlayer.chase_per_rank = calculatePercentileRank(
    aggregatedPlayers,
    'chase_per',
    targetPlayer.chase_per,
    false, // Lower is better for chase%
  );

  return targetPlayer;
}

/**
 * Calculates the percentile rank of a value within a dataset
 * @param data Array of player stats
 * @param field The field to compare
 * @param value The player's value
 * @param higherIsBetter Whether higher values are better (true) or worse (false)
 * @returns Percentile rank from 0-100
 */
function calculatePercentileRank(
  data: AdvancedBattingStatsTable[],
  field: keyof AdvancedBattingStatsTable,
  value: number | null | undefined,
  higherIsBetter: boolean,
): number {
  if (value === null || value === undefined) return 50;

  // Filter out entries with no data for this field
  const validEntries = data.filter((p) => {
    const fieldValue = p[field];
    return fieldValue !== null && fieldValue !== undefined;
  });

  if (validEntries.length <= 1) return 50;

  // Count how many values are worse than this one
  const worseThan = validEntries.filter((p) => {
    const otherValue = p[field];
    if (higherIsBetter) {
      return otherValue !== null && otherValue !== undefined && otherValue < value;
    } else {
      return otherValue !== null && otherValue !== undefined && otherValue > value;
    }
  }).length;

  // Calculate percentile (0-100)
  return (worseThan / (validEntries.length - 1)) * 100;
}
