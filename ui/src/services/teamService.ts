import { supabase } from '@/lib/supabaseClient';
import { cachedQuery, createCacheKey } from '@/services/cacheService';
import type {
  BatterStatsTable,
  PitchCountsTable,
  PitcherStatsTable,
  PlayersTable,
  TeamsTable,
} from '@/types/db';
import type { DateRange } from '@/types/dateRange';
import { getYearRange } from '@/utils/dateRange';

const toRangeDescriptor = (range: DateRange) => ({
  range: { startDate: range.startDate, endDate: range.endDate },
});

export async function fetchTeamsByDateRange(range: DateRange) {
  const { startYear, endYear } = getYearRange(range);

  return cachedQuery({
    key: createCacheKey('Teams', {
      select: '*',
      ...toRangeDescriptor(range),
      order: [
        { column: 'Conference', ascending: true },
        { column: 'TeamName', ascending: true },
      ],
    }),
    query: () =>
      supabase
        .from('Teams')
        .select('*')
        .gte('Year', startYear)
        .lte('Year', endYear)
        .order('Conference', { ascending: true })
        .order('TeamName', { ascending: true })
        .overrideTypes<TeamsTable[], { merge: false }>(),
  });
}

export async function fetchTeamByAbbreviation(range: DateRange, trackmanAbbreviation: string) {
  const { startYear, endYear } = getYearRange(range);

  return cachedQuery({
    key: createCacheKey('Teams', {
      select: ['TeamName', 'TrackmanAbbreviation', 'Conference'],
      eq: {
        TrackmanAbbreviation: trackmanAbbreviation,
      },
      ...toRangeDescriptor(range),
    }),
    query: () =>
      supabase
        .from('Teams')
        .select('TeamName, TrackmanAbbreviation, Conference, Year')
        .eq('TrackmanAbbreviation', trackmanAbbreviation)
        .gte('Year', startYear)
        .lte('Year', endYear)
        .order('Year', { ascending: false })
        .limit(1)
        .maybeSingle()
        .overrideTypes<TeamsTable, { merge: false }>(),
  });
}

export async function fetchTeamRoster(range: DateRange, trackmanAbbreviation: string) {
  const { startYear, endYear } = getYearRange(range);

  return cachedQuery({
    key: createCacheKey('Players', {
      select: '*',
      eq: {
        TeamTrackmanAbbreviation: trackmanAbbreviation,
      },
      ...toRangeDescriptor(range),
      order: [{ column: 'Name', ascending: true }],
    }),
    query: () =>
      supabase
        .from('Players')
        .select('*')
        .eq('TeamTrackmanAbbreviation', trackmanAbbreviation)
        .gte('Year', startYear)
        .lte('Year', endYear)
        .order('Name', { ascending: true })
        .overrideTypes<PlayersTable[], { merge: false }>(),
  });
}

export async function fetchTeamBattingStats(team: string, range: DateRange) {
  return cachedQuery({
    key: createCacheKey('BatterStats', {
      select: '*',
      eq: { BatterTeam: team },
      ...toRangeDescriptor(range),
    }),
    query: () =>
      supabase
        .from('BatterStats')
        .select('*')
        .eq('BatterTeam', team)
        .gte('Date', range.startDate)
        .lte('Date', range.endDate)
        .overrideTypes<BatterStatsTable[], { merge: false }>(),
  });
}

export async function fetchTeamPitcherStats(team: string, range: DateRange) {
  return cachedQuery({
    key: createCacheKey('PitcherStats', {
      select: '*',
      eq: { PitcherTeam: team },
      ...toRangeDescriptor(range),
    }),
    query: () =>
      supabase
        .from('PitcherStats')
        .select('*')
        .eq('PitcherTeam', team)
        .gte('Date', range.startDate)
        .lte('Date', range.endDate)
        .overrideTypes<PitcherStatsTable[], { merge: false }>(),
  });
}

export async function fetchTeamPitchCounts(team: string, range: DateRange) {
  return cachedQuery({
    key: createCacheKey('PitchCounts', {
      select: '*',
      eq: { PitcherTeam: team },
      ...toRangeDescriptor(range),
    }),
    query: () =>
      supabase
        .from('PitchCounts')
        .select('*')
        .eq('PitcherTeam', team)
        .gte('Date', range.startDate)
        .lte('Date', range.endDate)
        .overrideTypes<PitchCountsTable[], { merge: false }>(),
  });
}
