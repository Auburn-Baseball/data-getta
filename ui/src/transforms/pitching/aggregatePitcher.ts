import type { PitcherStatsTable } from '@/types/db';
import { inningsToOuts, outsToInnings } from '@/transforms/pitching/utils';

export const aggregatePitcherStats = (
  playerStats: PitcherStatsTable[],
): PitcherStatsTable | null => {
  if (!playerStats.length) {
    return null;
  }

  const template = playerStats[0];

  let totalOuts = 0;
  let totalStrikeouts = 0;
  let totalWalks = 0;
  let totalOutOfZone = 0;
  let totalInZone = 0;
  let totalMissesInZone = 0;
  let totalSwingsInZone = 0;
  let totalChases = 0;
  let totalPitches = 0;
  let gamesStarted = 0;
  let totalGames = 0;
  let totalBattersFaced = 0;
  let totalHits = 0;
  let totalRunsAllowed = 0;
  let totalHomeRuns = 0;
  let totalEarnedRuns = 0;

  for (const stat of playerStats) {
    totalOuts += inningsToOuts(stat.total_innings_pitched);
    totalStrikeouts += stat.total_strikeouts_pitcher ?? 0;
    totalWalks += stat.total_walks_pitcher ?? 0;
    totalOutOfZone += stat.total_out_of_zone_pitches ?? 0;
    totalInZone += stat.total_in_zone_pitches ?? 0;
    totalMissesInZone += stat.misses_in_zone ?? 0;
    totalSwingsInZone += stat.swings_in_zone ?? 0;
    totalChases += stat.total_num_chases ?? 0;
    totalPitches += stat.pitches ?? 0;
    gamesStarted += stat.games_started ?? 0;
    totalGames += stat.games ?? 0;
    totalBattersFaced += stat.total_batters_faced ?? 0;
    totalHits += stat.hits ?? 0;
    totalRunsAllowed += stat.runs_allowed ?? 0;
    totalHomeRuns += stat.homeruns ?? 0;
    totalEarnedRuns += stat.earned_runs ?? 0;
  }

  if (totalGames === 0) {
    totalGames = playerStats.length;
  }

  const inningsPitched = outsToInnings(totalOuts);
  const inningsAsInnings = totalOuts / 3;

  const kPercentage = totalBattersFaced > 0 ? totalStrikeouts / totalBattersFaced : 0;
  const bbPercentage = totalBattersFaced > 0 ? totalWalks / totalBattersFaced : 0;
  const chasePercentage =
    totalOutOfZone > 0
      ? totalChases / totalOutOfZone
      : playerStats.reduce((sum, stat) => sum + (stat.chase_percentage ?? 0), 0) /
        playerStats.length;
  const inZoneWhiffPercentage =
    totalSwingsInZone > 0
      ? totalMissesInZone / totalSwingsInZone
      : playerStats.reduce((sum, stat) => sum + (stat.in_zone_whiff_percentage ?? 0), 0) /
        playerStats.length;

  const kPerNine = inningsAsInnings > 0 ? (totalStrikeouts * 9) / inningsAsInnings : 0;
  const bbPerNine = inningsAsInnings > 0 ? (totalWalks * 9) / inningsAsInnings : 0;
  const whip = inningsAsInnings > 0 ? (totalWalks + totalHits) / inningsAsInnings : 0;

  const aggregated: PitcherStatsTable = {
    Pitcher: template.Pitcher,
    PitcherTeam: template.PitcherTeam,
    Date: '',
    Year: template.Year,
    hits: totalHits,
    runs_allowed: totalRunsAllowed,
    homeruns: totalHomeRuns,
    earned_runs: totalEarnedRuns,
    total_strikeouts_pitcher: totalStrikeouts,
    total_walks_pitcher: totalWalks,
    total_out_of_zone_pitches: totalOutOfZone,
    total_in_zone_pitches: totalInZone,
    misses_in_zone: totalMissesInZone,
    swings_in_zone: totalSwingsInZone,
    total_num_chases: totalChases,
    pitches: totalPitches,
    games_started: gamesStarted,
    total_innings_pitched: inningsPitched,
    total_batters_faced: totalBattersFaced,
    k_percentage: kPercentage,
    base_on_ball_percentage: bbPercentage,
    in_zone_whiff_percentage: inZoneWhiffPercentage,
    chase_percentage: chasePercentage,
    games: totalGames,
    k_per_9: kPerNine,
    bb_per_9: bbPerNine,
    whip,
    is_practice: template.is_practice,
  };

  return aggregated;
};
