import type { PitchCountsTable } from '@/types/db';

export const aggregatePitchCounts = (counts: PitchCountsTable[]): PitchCountsTable | null => {
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
