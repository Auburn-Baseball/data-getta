import { BatterStatsTable } from '@/types/db';

const aggregatePlayerStats = (playerStats: BatterStatsTable[]): BatterStatsTable | null => {
  if (!playerStats.length) return null;

  const template = playerStats[0];

  let games = 0;
  let atBats = 0;
  let hits = 0;
  let doubles = 0;
  let triples = 0;
  let singles = 0;
  let homeruns = 0;
  let totalBases = 0;
  let walks = 0;
  let strikeouts = 0;
  let strikes = 0;
  let extraBaseHits = 0;
  let plateAppearances = 0;
  let sacrifice = 0;
  let hitByPitch = 0;
  let battedBalls = 0;
  let totalExitVelo = 0;

  let chaseWeightedSum = 0;
  let chaseWeight = 0;
  let whiffWeightedSum = 0;
  let whiffWeight = 0;
  let kPerWeightedSum = 0;
  let kPerWeight = 0;
  let bbPerWeightedSum = 0;
  let bbPerWeight = 0;
  let avgExitVeloWeightedSum = 0;
  let avgExitVeloWeight = 0;

  for (const stat of playerStats) {
    const statGames = stat.games ?? 0;
    const statPlateAppearances = stat.plate_appearances ?? 0;
    const statStrikes = stat.strikes ?? statPlateAppearances;
    const statBattedBalls = stat.batted_balls ?? 0;
    const statTotalExitVelo =
      stat.total_exit_velo ??
      (stat.avg_exit_velo && statBattedBalls > 0 ? stat.avg_exit_velo * statBattedBalls : 0);

    games += statGames;
    atBats += stat.at_bats ?? 0;
    hits += stat.hits ?? 0;
    doubles += stat.doubles ?? 0;
    triples += stat.triples ?? 0;
    singles += stat.singles ?? 0;
    homeruns += stat.homeruns ?? 0;
    totalBases += stat.total_bases ?? 0;
    walks += stat.walks ?? 0;
    strikeouts += stat.strikeouts ?? 0;
    strikes += stat.strikes ?? 0;
    extraBaseHits += stat.extra_base_hits ?? 0;
    plateAppearances += statPlateAppearances;
    sacrifice += stat.sacrifice ?? 0;
    hitByPitch += stat.hit_by_pitch ?? 0;
    battedBalls += statBattedBalls;
    totalExitVelo += statTotalExitVelo;

    const chasePct = stat.chase_percentage ?? 0;
    chaseWeightedSum += chasePct * statPlateAppearances;
    chaseWeight += statPlateAppearances;

    const whiffPct = stat.in_zone_whiff_percentage ?? 0;
    whiffWeightedSum += whiffPct * statStrikes;
    whiffWeight += statStrikes;

    const kPerValue = stat.k_per ?? 0;
    const bbPerValue = stat.bb_per ?? 0;
    const gamesWeight = statGames || 1;
    kPerWeightedSum += kPerValue * gamesWeight;
    kPerWeight += gamesWeight;
    bbPerWeightedSum += bbPerValue * gamesWeight;
    bbPerWeight += gamesWeight;

    const exitWeight = statBattedBalls || stat.at_bats || statPlateAppearances || statGames;
    if (exitWeight > 0) {
      avgExitVeloWeightedSum += (stat.avg_exit_velo ?? 0) * exitWeight;
      avgExitVeloWeight += exitWeight;
    }
  }

  if (games === 0) {
    games = playerStats.length;
  }

  const battingAverage = atBats > 0 ? hits / atBats : 0;
  const obpDenominator = atBats + walks + hitByPitch + sacrifice;
  const onBasePercentage = obpDenominator > 0 ? (hits + walks + hitByPitch) / obpDenominator : 0;
  const sluggingPercentage = atBats > 0 ? totalBases / atBats : 0;
  const ops = onBasePercentage + sluggingPercentage;
  const isolatedPower = sluggingPercentage - battingAverage;
  const kPercentage = plateAppearances > 0 ? strikeouts / plateAppearances : 0;
  const bbPercentage = plateAppearances > 0 ? walks / plateAppearances : 0;
  const chasePercentage = chaseWeight > 0 ? chaseWeightedSum / chaseWeight : 0;
  const whiffPercentage = whiffWeight > 0 ? whiffWeightedSum / whiffWeight : 0;
  const kPer = games > 0 ? strikeouts / games : 0;
  const bbPer = games > 0 ? walks / games : 0;
  const averagedKPer = kPerWeight > 0 ? kPerWeightedSum / kPerWeight : kPer;
  const averagedBbPer = bbPerWeight > 0 ? bbPerWeightedSum / bbPerWeight : bbPer;
  const averageExitVelo =
    battedBalls > 0
      ? totalExitVelo / battedBalls
      : avgExitVeloWeight > 0
        ? avgExitVeloWeightedSum / avgExitVeloWeight
        : 0;

  const aggregated: BatterStatsTable = {
    Batter: template.Batter,
    BatterTeam: template.BatterTeam,
    Date: '',
    games,
    at_bats: atBats,
    hits,
    doubles,
    triples,
    homeruns,
    total_bases: totalBases,
    walks,
    strikeouts,
    batting_average: battingAverage,
    on_base_percentage: onBasePercentage,
    slugging_percentage: sluggingPercentage,
    onbase_plus_slugging: ops,
    isolated_power: isolatedPower,
    strikes,
    extra_base_hits: extraBaseHits,
    plate_appearances: plateAppearances,
    sacrifice,
    hit_by_pitch: hitByPitch,
    k_percentage: kPercentage,
    base_on_ball_percentage: bbPercentage,
    chase_percentage: chasePercentage,
    in_zone_whiff_percentage: whiffPercentage,
    k_per: averagedKPer,
    bb_per: averagedBbPer,
    avg_exit_velo: averageExitVelo,
  };

  if (singles > 0) {
    aggregated.singles = singles;
  }
  if (battedBalls > 0) {
    aggregated.batted_balls = battedBalls;
  }
  if (totalExitVelo > 0) {
    aggregated.total_exit_velo = totalExitVelo;
  }

  return aggregated;
};

export function batterStatsTransform(
  data: BatterStatsTable[],
  opts: { mode?: 'all' | 'practiceOnly' | 'gameOnly' } = { mode: 'all' }
): BatterStatsTable[] {
  if (!data || data.length === 0) return [];

  const { mode = 'all' } = opts;
  const playerMap = new Map<string, BatterStatsTable[]>();

  for (const stat of data) {
    if (mode === 'gameOnly' && stat.is_practice) continue;
    if (mode === 'practiceOnly' && !stat.is_practice) continue;

    const key = `${stat.Batter}|${stat.BatterTeam}`;
    if (!playerMap.has(key)) playerMap.set(key, []);
    playerMap.get(key)!.push(stat);
  }

  const results: BatterStatsTable[] = [];
  for (const playerStats of playerMap.values()) {
    const aggregated = aggregatePlayerStats(playerStats);
    if (aggregated) results.push(aggregated);
  }

  // Sort by batting average (desc), then name for stability
  return results.sort((a, b) => {
    const aAvg = a.batting_average ?? 0;
    const bAvg = b.batting_average ?? 0;
    if (bAvg !== aAvg) return bAvg - aAvg;
    return (a.Batter || '').localeCompare(b.Batter || '');
  });
}

// Add a new function to create summary row
export function createBatterStatsSummary(players: BatterStatsTable[]): BatterStatsTable {
  if (!players || players.length === 0) {
    return {
      Batter: 'Total',
      BatterTeam: '',
      Date: '',
      games: 0,
      at_bats: 0,
      hits: 0,
      doubles: 0,
      triples: 0,
      homeruns: 0,
      total_bases: 0,
      walks: 0,
      strikeouts: 0,
      batting_average: 0,
      on_base_percentage: 0,
      slugging_percentage: 0,
      onbase_plus_slugging: 0,
      isolated_power: 0,
      strikes: 0,
      extra_base_hits: 0,
      plate_appearances: 0,
      sacrifice: 0,
      hit_by_pitch: 0,
      k_percentage: 0,
      base_on_ball_percentage: 0,
      chase_percentage: 0,
      in_zone_whiff_percentage: 0,
      k_per: 0,
      bb_per: 0,
      avg_exit_velo: 0,
    };
  }

  // Compute summary stats
  const totalAtBats = players.reduce((sum, p) => sum + (p.at_bats || 0), 0);
  const totalHits = players.reduce((sum, p) => sum + (p.hits || 0), 0);
  const totalWalks = players.reduce((sum, p) => sum + (p.walks || 0), 0);
  const totalHBP = players.reduce((sum, p) => sum + (p.hit_by_pitch || 0), 0);
  const totalSacrifice = players.reduce((sum, p) => sum + (p.sacrifice || 0), 0);
  const totalBases = players.reduce((sum, p) => sum + (p.total_bases || 0), 0);
  const totalPA = players.reduce((sum, p) => sum + (p.plate_appearances || 0), 0);
  const totalSO = players.reduce((sum, p) => sum + (p.strikeouts || 0), 0);

  // Calculate derived stats
  const battingAvg = totalAtBats > 0 ? totalHits / totalAtBats : 0;

  const onBasePct =
    totalAtBats + totalWalks + totalHBP + totalSacrifice > 0
      ? (totalHits + totalWalks + totalHBP) / (totalAtBats + totalWalks + totalHBP + totalSacrifice)
      : 0;

  const sluggingPct = totalAtBats > 0 ? totalBases / totalAtBats : 0;

  const obpSlg = onBasePct + sluggingPct;

  const isolatedPower = sluggingPct - battingAvg;

  const kPercentage = totalPA > 0 ? totalSO / totalPA : 0;

  const bbPercentage = totalPA > 0 ? totalWalks / totalPA : 0;

  return {
    Batter: 'Total',
    BatterTeam: '',
    Date: '',
    games: players.length > 0 ? Math.max(...players.map((p) => p.games || 0)) : 0,
    plate_appearances: totalPA,
    at_bats: totalAtBats,
    hits: totalHits,
    doubles: players.reduce((sum, p) => sum + (p.doubles || 0), 0),
    triples: players.reduce((sum, p) => sum + (p.triples || 0), 0),
    homeruns: players.reduce((sum, p) => sum + (p.homeruns || 0), 0),
    total_bases: totalBases,
    walks: totalWalks,
    strikeouts: totalSO,
    batting_average: battingAvg,
    on_base_percentage: onBasePct,
    slugging_percentage: sluggingPct,
    onbase_plus_slugging: obpSlg,
    isolated_power: isolatedPower,
    strikes: players.reduce((sum, p) => sum + (p.strikes || 0), 0),
    extra_base_hits: players.reduce((sum, p) => sum + (p.extra_base_hits || 0), 0),
    sacrifice: totalSacrifice,
    hit_by_pitch: totalHBP,
    k_percentage: kPercentage,
    base_on_ball_percentage: bbPercentage,
    chase_percentage:
      players.reduce((sum, p) => sum + (p.chase_percentage || 0), 0) / players.length,
    in_zone_whiff_percentage:
      players.reduce((sum, p) => sum + (p.in_zone_whiff_percentage || 0), 0) / players.length,
    k_per: players.reduce((sum, p) => sum + (p.k_per || 0), 0) / players.length,
    bb_per: players.reduce((sum, p) => sum + (p.bb_per || 0), 0) / players.length,
    avg_exit_velo: players.reduce((sum, p) => sum + (p.avg_exit_velo || 0), 0) / players.length,
  };
}
