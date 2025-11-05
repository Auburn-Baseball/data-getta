import type { BatterStatsTable } from '@/types/db';

type Totals = {
  games: number;
  atBats: number;
  hits: number;
  doubles: number;
  triples: number;
  singles: number;
  homeruns: number;
  totalBases: number;
  walks: number;
  strikeouts: number;
  strikes: number;
  extraBaseHits: number;
  plateAppearances: number;
  sacrifice: number;
  hitByPitch: number;
  battedBalls: number;
  totalExitVelo: number;
  chaseWeightedSum: number;
  chaseWeight: number;
  whiffWeightedSum: number;
  whiffWeight: number;
  kPerWeightedSum: number;
  kPerWeight: number;
  bbPerWeightedSum: number;
  bbPerWeight: number;
  avgExitVeloWeightedSum: number;
  avgExitVeloWeight: number;
};

export function computeTotals(playerStats: BatterStatsTable[]): Totals {
  const t: Totals = {
    games: 0,
    atBats: 0,
    hits: 0,
    doubles: 0,
    triples: 0,
    singles: 0,
    homeruns: 0,
    totalBases: 0,
    walks: 0,
    strikeouts: 0,
    strikes: 0,
    extraBaseHits: 0,
    plateAppearances: 0,
    sacrifice: 0,
    hitByPitch: 0,
    battedBalls: 0,
    totalExitVelo: 0,
    chaseWeightedSum: 0,
    chaseWeight: 0,
    whiffWeightedSum: 0,
    whiffWeight: 0,
    kPerWeightedSum: 0,
    kPerWeight: 0,
    bbPerWeightedSum: 0,
    bbPerWeight: 0,
    avgExitVeloWeightedSum: 0,
    avgExitVeloWeight: 0,
  };

  for (const stat of playerStats) {
    const statGames = stat.games ?? 0;
    const statPlateAppearances = stat.plate_appearances ?? 0;
    const statStrikes = stat.strikes ?? statPlateAppearances;
    const statBattedBalls = stat.batted_balls ?? 0;
    const statTotalExitVelo =
      stat.total_exit_velo ??
      (stat.avg_exit_velo && statBattedBalls > 0 ? stat.avg_exit_velo * statBattedBalls : 0);

    t.games += statGames;
    t.atBats += stat.at_bats ?? 0;
    t.hits += stat.hits ?? 0;
    t.doubles += stat.doubles ?? 0;
    t.triples += stat.triples ?? 0;
    t.singles += stat.singles ?? 0;
    t.homeruns += stat.homeruns ?? 0;
    t.totalBases += stat.total_bases ?? 0;
    t.walks += stat.walks ?? 0;
    t.strikeouts += stat.strikeouts ?? 0;
    t.strikes += statStrikes ?? 0;
    t.extraBaseHits += stat.extra_base_hits ?? 0;
    t.plateAppearances += statPlateAppearances;
    t.sacrifice += stat.sacrifice ?? 0;
    t.hitByPitch += stat.hit_by_pitch ?? 0;
    t.battedBalls += statBattedBalls;
    t.totalExitVelo += statTotalExitVelo;

    const chasePct = stat.chase_percentage ?? 0;
    t.chaseWeightedSum += chasePct * statPlateAppearances;
    t.chaseWeight += statPlateAppearances;

    const whiffPct = stat.in_zone_whiff_percentage ?? 0;
    t.whiffWeightedSum += whiffPct * statStrikes;
    t.whiffWeight += statStrikes;

    const kPerValue = stat.k_per ?? 0;
    const bbPerValue = stat.bb_per ?? 0;
    const gamesWeight = statGames || 1;
    t.kPerWeightedSum += kPerValue * gamesWeight;
    t.kPerWeight += gamesWeight;
    t.bbPerWeightedSum += bbPerValue * gamesWeight;
    t.bbPerWeight += gamesWeight;

    const exitWeight = statBattedBalls || stat.at_bats || statPlateAppearances || statGames;
    if (exitWeight > 0) {
      t.avgExitVeloWeightedSum += (stat.avg_exit_velo ?? 0) * exitWeight;
      t.avgExitVeloWeight += exitWeight;
    }
  }

  if (t.games === 0) {
    t.games = playerStats.length;
  }

  return t;
}

export function computeRatesFromTotals(t: Totals) {
  const battingAverage = t.atBats > 0 ? t.hits / t.atBats : 0;
  const obpDenominator = t.atBats + t.walks + t.hitByPitch + t.sacrifice;
  const onBasePercentage =
    obpDenominator > 0 ? (t.hits + t.walks + t.hitByPitch) / obpDenominator : 0;
  const sluggingPercentage = t.atBats > 0 ? t.totalBases / t.atBats : 0;
  const ops = onBasePercentage + sluggingPercentage;
  const isolatedPower = sluggingPercentage - battingAverage;
  const kPercentage = t.plateAppearances > 0 ? t.strikeouts / t.plateAppearances : 0;
  const bbPercentage = t.plateAppearances > 0 ? t.walks / t.plateAppearances : 0;
  const chasePercentage = t.chaseWeight > 0 ? t.chaseWeightedSum / t.chaseWeight : 0;
  const whiffPercentage = t.whiffWeight > 0 ? t.whiffWeightedSum / t.whiffWeight : 0;
  const kPer = t.games > 0 ? t.strikeouts / t.games : 0;
  const bbPer = t.games > 0 ? t.walks / t.games : 0;
  const averagedKPer = t.kPerWeight > 0 ? t.kPerWeightedSum / t.kPerWeight : kPer;
  const averagedBbPer = t.bbPerWeight > 0 ? t.bbPerWeightedSum / t.bbPerWeight : bbPer;
  const averageExitVelo =
    t.battedBalls > 0
      ? t.totalExitVelo / t.battedBalls
      : t.avgExitVeloWeight > 0
        ? t.avgExitVeloWeightedSum / t.avgExitVeloWeight
        : 0;

  return {
    battingAverage,
    onBasePercentage,
    sluggingPercentage,
    ops,
    isolatedPower,
    kPercentage,
    bbPercentage,
    chasePercentage,
    whiffPercentage,
    averagedKPer,
    averagedBbPer,
    averageExitVelo,
  };
}

function buildAggregatedRow(
  template: BatterStatsTable,
  t: Totals,
  r: ReturnType<typeof computeRatesFromTotals>,
): BatterStatsTable {
  return {
    Batter: template.Batter,
    BatterTeam: template.BatterTeam,
    Date: '',
    is_practice: template.is_practice ?? false,
    games: t.games,
    at_bats: t.atBats,
    hits: t.hits,
    doubles: t.doubles,
    triples: t.triples,
    homeruns: t.homeruns,
    total_bases: t.totalBases,
    walks: t.walks,
    strikeouts: t.strikeouts,
    batting_average: r.battingAverage,
    on_base_percentage: r.onBasePercentage,
    slugging_percentage: r.sluggingPercentage,
    onbase_plus_slugging: r.ops,
    isolated_power: r.isolatedPower,
    strikes: t.strikes,
    extra_base_hits: t.extraBaseHits,
    plate_appearances: t.plateAppearances,
    sacrifice: t.sacrifice,
    hit_by_pitch: t.hitByPitch,
    k_percentage: r.kPercentage,
    base_on_ball_percentage: r.bbPercentage,
    chase_percentage: r.chasePercentage,
    in_zone_whiff_percentage: r.whiffPercentage,
    k_per: r.averagedKPer,
    bb_per: r.averagedBbPer,
    avg_exit_velo: r.averageExitVelo,
    // Optional fields kept intact when present in inputs
    singles: t.singles || undefined,
    batted_balls: t.battedBalls || undefined,
    total_exit_velo: t.totalExitVelo || undefined,
  };
}

export function aggregateBatterStats(playerStats: BatterStatsTable[]): BatterStatsTable | null {
  if (!playerStats.length) return null;
  const template = playerStats[0];
  const totals = computeTotals(playerStats);
  const rates = computeRatesFromTotals(totals);
  return buildAggregatedRow(template, totals, rates);
}
