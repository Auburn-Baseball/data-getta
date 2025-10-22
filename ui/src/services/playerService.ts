import { supabase } from '@/lib/supabaseClient';
import { cachedQuery, createCacheKey } from '@/services/cacheService';
import type {
  AdvancedBattingStatsTable,
  AdvancedPitchingStatsTable,
  BatterPitchBinsTable,
  BatterStatsTable,
  PitchCountsTable,
  PitcherPitchBinsTable,
  PitcherStatsTable,
  PlayersTable,
} from '@/types/db';
import type { DateRange } from '@/types/dateRange';
import { getYearRange } from '@/utils/dateRange';

const toRangeDescriptor = (range: DateRange) => ({
  range: { startDate: range.startDate, endDate: range.endDate },
});

export async function fetchPlayer(range: DateRange, team: string, playerName: string) {
  const { startYear, endYear } = getYearRange(range);

  return cachedQuery({
    key: createCacheKey('Players', {
      select: '*',
      eq: {
        TeamTrackmanAbbreviation: team,
        Name: playerName,
      },
      ...toRangeDescriptor(range),
      maybeSingle: true,
    }),
    query: () =>
      supabase
        .from('Players')
        .select('*')
        .eq('TeamTrackmanAbbreviation', team)
        .eq('Name', playerName)
        .gte('Year', startYear)
        .lte('Year', endYear)
        .maybeSingle<PlayersTable>(),
  });
}

export async function fetchPlayerBatterStats(playerName: string, team: string, range: DateRange) {
  return cachedQuery({
    key: createCacheKey('BatterStats', {
      select: '*',
      eq: { Batter: playerName, BatterTeam: team },
      ...toRangeDescriptor(range),
    }),
    query: () =>
      supabase
        .from('BatterStats')
        .select('*')
        .eq('Batter', playerName)
        .eq('BatterTeam', team)
        .gte('Date', range.startDate)
        .lte('Date', range.endDate)
        .overrideTypes<BatterStatsTable[], { merge: false }>(),
  });
}

export async function fetchPlayerPitcherStats(playerName: string, team: string, range: DateRange) {
  return cachedQuery({
    key: createCacheKey('PitcherStats', {
      select: '*',
      eq: { Pitcher: playerName, PitcherTeam: team },
      ...toRangeDescriptor(range),
    }),
    query: () =>
      supabase
        .from('PitcherStats')
        .select('*')
        .eq('Pitcher', playerName)
        .eq('PitcherTeam', team)
        .gte('Date', range.startDate)
        .lte('Date', range.endDate)
        .overrideTypes<PitcherStatsTable[], { merge: false }>(),
  });
}

export async function fetchPlayerPitchCounts(playerName: string, team: string, range: DateRange) {
  return cachedQuery({
    key: createCacheKey('PitchCounts', {
      select: '*',
      eq: { Pitcher: playerName, PitcherTeam: team },
      ...toRangeDescriptor(range),
    }),
    query: () =>
      supabase
        .from('PitchCounts')
        .select('*')
        .eq('Pitcher', playerName)
        .eq('PitcherTeam', team)
        .gte('Date', range.startDate)
        .lte('Date', range.endDate)
        .overrideTypes<PitchCountsTable[], { merge: false }>(),
  });
}

const pitcherBinsSelect = `
  PitcherTeam, Date, Pitcher, ZoneId, InZone, ZoneRow, ZoneCol, ZoneCell, OuterLabel, ZoneVersion,
  TotalPitchCount,
  Count_FourSeam, Count_Sinker, Count_Slider, Count_Curveball, Count_Changeup, Count_Cutter, Count_Splitter, Count_Other,
  Count_L_FourSeam, Count_L_Sinker, Count_L_Slider, Count_L_Curveball, Count_L_Changeup, Count_L_Cutter, Count_L_Splitter, Count_L_Other,
  Count_R_FourSeam, Count_R_Sinker, Count_R_Slider, Count_R_Curveball, Count_R_Changeup, Count_R_Cutter, Count_R_Splitter, Count_R_Other
`.trim();

const batterBinsSelect = `
  BatterTeam, Date, Batter, ZoneId, InZone, ZoneRow, ZoneCol, ZoneCell, OuterLabel, ZoneVersion,
  TotalPitchCount, TotalSwingCount, TotalHitCount,
  Count_FourSeam, Count_Sinker, Count_Slider, Count_Curveball, Count_Changeup, Count_Cutter, Count_Splitter, Count_Other,
  SwingCount_FourSeam, SwingCount_Sinker, SwingCount_Slider, SwingCount_Curveball, SwingCount_Changeup, SwingCount_Cutter, SwingCount_Splitter, SwingCount_Other,
  HitCount_FourSeam, HitCount_Sinker, HitCount_Slider, HitCount_Curveball, HitCount_Changeup, HitCount_Cutter, HitCount_Splitter, HitCount_Other
`.trim();

export async function fetchPitcherHeatMapBins(playerName: string, team: string, range: DateRange) {
  return cachedQuery({
    key: createCacheKey('PitcherPitchBins', {
      select: pitcherBinsSelect,
      eq: { Pitcher: playerName, PitcherTeam: team },
      ...toRangeDescriptor(range),
    }),
    query: () =>
      supabase
        .from('PitcherPitchBins')
        .select(pitcherBinsSelect)
        .eq('Pitcher', playerName)
        .eq('PitcherTeam', team)
        .gte('Date', range.startDate)
        .lte('Date', range.endDate)
        .overrideTypes<PitcherPitchBinsTable[], { merge: false }>(),
  });
}

export async function fetchBatterHeatMapBins(playerName: string, team: string, range: DateRange) {
  return cachedQuery({
    key: createCacheKey('BatterPitchBins', {
      select: batterBinsSelect,
      eq: { Batter: playerName, BatterTeam: team },
      ...toRangeDescriptor(range),
    }),
    query: () =>
      supabase
        .from('BatterPitchBins')
        .select(batterBinsSelect)
        .eq('Batter', playerName)
        .eq('BatterTeam', team)
        .gte('Date', range.startDate)
        .lte('Date', range.endDate)
        .overrideTypes<BatterPitchBinsTable[], { merge: false }>(),
  });
}

export async function fetchAdvancedBattingStats(playerName: string, team: string, range: DateRange) {
  const { startYear, endYear } = getYearRange(range);

  return cachedQuery({
    key: createCacheKey('AdvancedBattingStats', {
      select: '*',
      eq: { Batter: playerName, BatterTeam: team },
      ...toRangeDescriptor(range),
    }),
    query: () =>
      supabase
        .from('AdvancedBattingStats')
        .select('*')
        .eq('Batter', playerName)
        .eq('BatterTeam', team)
        .gte('Year', startYear)
        .lte('Year', endYear)
        .overrideTypes<AdvancedBattingStatsTable[], { merge: false }>(),
  });
}

export async function fetchAdvancedPitchingStats(playerName: string, team: string, range: DateRange) {
  const { startYear, endYear } = getYearRange(range);

  return cachedQuery({
    key: createCacheKey('AdvancedPitchingStats', {
      select: '*',
      eq: { Pitcher: playerName, PitcherTeam: team },
      ...toRangeDescriptor(range),
    }),
    query: () =>
      supabase
        .from('AdvancedPitchingStats')
        .select('*')
        .eq('Pitcher', playerName)
        .eq('PitcherTeam', team)
        .gte('Year', startYear)
        .lte('Year', endYear)
        .overrideTypes<AdvancedPitchingStatsTable[], { merge: false }>(),
  });
}
