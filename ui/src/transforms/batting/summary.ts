import type { BatterStatsTable } from '@/types/db';

export function createBatterStatsSummary(players: BatterStatsTable[]): BatterStatsTable {
  if (!players || players.length === 0) {
    return {
      Batter: 'Total',
      BatterTeam: '',
      Date: '',
      is_practice: false,
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

  const totalAtBats = players.reduce((s, p) => s + (p.at_bats || 0), 0);
  const totalHits = players.reduce((s, p) => s + (p.hits || 0), 0);
  const totalWalks = players.reduce((s, p) => s + (p.walks || 0), 0);
  const totalHBP = players.reduce((s, p) => s + (p.hit_by_pitch || 0), 0);
  const totalSacrifice = players.reduce((s, p) => s + (p.sacrifice || 0), 0);
  const totalBases = players.reduce((s, p) => s + (p.total_bases || 0), 0);
  const totalPA = players.reduce((s, p) => s + (p.plate_appearances || 0), 0);
  const totalSO = players.reduce((s, p) => s + (p.strikeouts || 0), 0);

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
    is_practice: false,
    games: players.length > 0 ? Math.max(...players.map((p) => p.games || 0)) : 0,
    plate_appearances: totalPA,
    at_bats: totalAtBats,
    hits: totalHits,
    doubles: players.reduce((s, p) => s + (p.doubles || 0), 0),
    triples: players.reduce((s, p) => s + (p.triples || 0), 0),
    homeruns: players.reduce((s, p) => s + (p.homeruns || 0), 0),
    total_bases: totalBases,
    walks: totalWalks,
    strikeouts: totalSO,
    batting_average: battingAvg,
    on_base_percentage: onBasePct,
    slugging_percentage: sluggingPct,
    onbase_plus_slugging: obpSlg,
    isolated_power: isolatedPower,
    strikes: players.reduce((s, p) => s + (p.strikes || 0), 0),
    extra_base_hits: players.reduce((s, p) => s + (p.extra_base_hits || 0), 0),
    sacrifice: totalSacrifice,
    hit_by_pitch: totalHBP,
    k_percentage: kPercentage,
    base_on_ball_percentage: bbPercentage,
    chase_percentage: players.reduce((s, p) => s + (p.chase_percentage || 0), 0) / players.length,
    in_zone_whiff_percentage:
      players.reduce((s, p) => s + (p.in_zone_whiff_percentage || 0), 0) / players.length,
    k_per: players.reduce((s, p) => s + (p.k_per || 0), 0) / players.length,
    bb_per: players.reduce((s, p) => s + (p.bb_per || 0), 0) / players.length,
    avg_exit_velo: players.reduce((s, p) => s + (p.avg_exit_velo || 0), 0) / players.length,
  };
}
