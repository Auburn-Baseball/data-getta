import { PitchCountsTable, PitcherStatsTable } from '@/types/schemas';

const inningsToOuts = (innings: number | string | null | undefined): number => {
  if (innings === null || innings === undefined) {
    return 0;
  }

  const numeric =
    typeof innings === 'string'
      ? Number.parseFloat(innings)
      : typeof innings === 'number'
        ? innings
        : Number(innings);

  if (!Number.isFinite(numeric)) {
    return 0;
  }

  const wholeInnings = Math.trunc(numeric);
  const fractional = Number((numeric - wholeInnings).toFixed(2));

  if (fractional === 0) {
    return wholeInnings * 3;
  }

  // Baseball scoring typically uses .1 and .2 to represent 1 and 2 outs respectively.
  const tenth = Math.round(fractional * 10);
  if (tenth === 1) {
    return wholeInnings * 3 + 1;
  }
  if (tenth === 2) {
    return wholeInnings * 3 + 2;
  }

  // Fallback: treat fractional component as true fractional innings (e.g., 0.33 repeating)
  return wholeInnings * 3 + Math.round((numeric - wholeInnings) * 3);
};

const outsToInnings = (outs: number): number => {
  if (!Number.isFinite(outs) || outs <= 0) {
    return 0;
  }
  const whole = Math.floor(outs / 3);
  const remainder = outs % 3;
  const decimal = remainder === 0 ? 0 : remainder === 1 ? 0.1 : 0.2;
  return Number((whole + decimal).toFixed(1));
};

const aggregatePitcherStats = (playerStats: PitcherStatsTable[]): PitcherStatsTable | null => {
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

export function pitcherStatsTransform(data: PitcherStatsTable[]): PitcherStatsTable[] {
  if (!data || data.length === 0) {
    return [];
  }

  const playerMap = new Map<string, PitcherStatsTable[]>();

  for (const stat of data) {
    const key = `${stat.Pitcher}|${stat.PitcherTeam}`;
    if (!playerMap.has(key)) {
      playerMap.set(key, []);
    }
    playerMap.get(key)!.push(stat);
  }

  const results: PitcherStatsTable[] = [];

  for (const playerStats of playerMap.values()) {
    const aggregated = aggregatePitcherStats(playerStats);
    if (aggregated) {
      results.push(aggregated);
    }
  }

  return results.sort((a, b) => {
    const outsDiff =
      inningsToOuts(b.total_innings_pitched) - inningsToOuts(a.total_innings_pitched);
    if (outsDiff !== 0) {
      return outsDiff;
    }
    return a.Pitcher.localeCompare(b.Pitcher);
  });
}

const aggregatePitchCounts = (counts: PitchCountsTable[]): PitchCountsTable | null => {
  if (!counts.length) {
    return null;
  }

  const template = counts[0];

  let totalPitches = 0;
  let curveball = 0;
  let fourSeam = 0;
  let sinker = 0;
  let slider = 0;
  let twoSeam = 0;
  let changeup = 0;
  let cutter = 0;
  let splitter = 0;
  let other = 0;
  let games = 0;

  for (const entry of counts) {
    totalPitches += entry.total_pitches ?? 0;
    curveball += entry.curveball_count ?? 0;
    fourSeam += entry.fourseam_count ?? 0;
    sinker += entry.sinker_count ?? 0;
    slider += entry.slider_count ?? 0;
    twoSeam += entry.twoseam_count ?? 0;
    changeup += entry.changeup_count ?? 0;
    cutter += entry.cutter_count ?? 0;
    splitter += entry.splitter_count ?? 0;
    other += entry.other_count ?? 0;
    games += entry.games ?? 0;
  }

  if (games === 0) {
    games = counts.length;
  }

  return {
    Pitcher: template.Pitcher,
    PitcherTeam: template.PitcherTeam,
    Date: template.Date,
    Year: template.Year,
    total_pitches: totalPitches,
    curveball_count: curveball,
    fourseam_count: fourSeam,
    sinker_count: sinker,
    slider_count: slider,
    twoseam_count: twoSeam,
    changeup_count: changeup,
    cutter_count: cutter,
    splitter_count: splitter,
    other_count: other,
    games,
    is_practice: template.is_practice,
  };
};

export function pitchCountsTransform(data: PitchCountsTable[]): PitchCountsTable[] {
  if (!data || data.length === 0) {
    return [];
  }

  const pitcherMap = new Map<string, PitchCountsTable[]>();

  for (const entry of data) {
    const key = `${entry.Pitcher}|${entry.PitcherTeam}`;
    if (!pitcherMap.has(key)) {
      pitcherMap.set(key, []);
    }
    pitcherMap.get(key)!.push(entry);
  }

  const results: PitchCountsTable[] = [];

  for (const counts of pitcherMap.values()) {
    const aggregated = aggregatePitchCounts(counts);
    if (aggregated) {
      results.push(aggregated);
    }
  }

  return results.sort((a, b) => {
    const pitchDiff = (b.total_pitches ?? 0) - (a.total_pitches ?? 0);
    if (pitchDiff !== 0) {
      return pitchDiff;
    }
    return a.Pitcher.localeCompare(b.Pitcher);
  });
}
