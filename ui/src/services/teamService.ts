import { supabase } from '@/lib/supabaseClient';
import { cachedQuery, createCacheKey } from '@/services/cacheService';
import type {
  BatterStatsTable,
  PitchCountsTable,
  PitcherStatsTable,
  PlayersTable,
  TeamsTable,
} from '@/types/db';

export async function fetchTeamsByYear(year: number) {
  return cachedQuery({
    key: createCacheKey('Teams', {
      select: '*',
      eq: { Year: year },
      order: [
        { column: 'Conference', ascending: true },
        { column: 'TeamName', ascending: true },
      ],
    }),
    query: () =>
      supabase
        .from('Teams')
        .select('*')
        .eq('Year', year)
        .order('Conference', { ascending: true })
        .order('TeamName', { ascending: true })
        .overrideTypes<TeamsTable[], { merge: false }>(),
  });
}

export async function fetchTeamByAbbreviation(year: number, trackmanAbbreviation: string) {
  return cachedQuery({
    key: createCacheKey('Teams', {
      select: ['TeamName', 'TrackmanAbbreviation', 'Conference'],
      eq: {
        TrackmanAbbreviation: trackmanAbbreviation,
        Year: year,
      },
      single: true,
    }),
    query: () =>
      supabase
        .from('Teams')
        .select('TeamName, TrackmanAbbreviation, Conference')
        .eq('TrackmanAbbreviation', trackmanAbbreviation)
        .eq('Year', year)
        .single()
        .overrideTypes<TeamsTable, { merge: false }>(),
  });
}

export async function fetchTeamRoster(year: number, trackmanAbbreviation: string) {
  return cachedQuery({
    key: createCacheKey('Players', {
      select: '*',
      eq: {
        Year: year,
        TeamTrackmanAbbreviation: trackmanAbbreviation,
      },
      order: [{ column: 'Name', ascending: true }],
    }),
    query: () =>
      supabase
        .from('Players')
        .select('*')
        .eq('Year', year)
        .eq('TeamTrackmanAbbreviation', trackmanAbbreviation)
        .order('Name', { ascending: true })
        .overrideTypes<PlayersTable[], { merge: false }>(),
  });
}

export async function fetchTeamBattingStats(team: string, startDate?: string, endDate?: string) {
  return cachedQuery({
    key: createCacheKey('BatterStats', {
      select: '*',
      eq: { BatterTeam: team },
      range: { startDate, endDate },
    }),
    query: () => {
      let query = supabase.from('BatterStats').select('*').eq('BatterTeam', team);
      if (startDate) {
        query = query.gte('Date', startDate);
      }
      if (endDate) {
        query = query.lte('Date', endDate);
      }
      return query.overrideTypes<BatterStatsTable[], { merge: false }>();
    },
  });
}

export async function fetchTeamPitcherStats(team: string, startDate?: string, endDate?: string) {
  return cachedQuery({
    key: createCacheKey('PitcherStats', {
      select: '*',
      eq: { PitcherTeam: team },
      range: { startDate, endDate },
    }),
    query: () => {
      let query = supabase.from('PitcherStats').select('*').eq('PitcherTeam', team);
      if (startDate) {
        query = query.gte('Date', startDate);
      }
      if (endDate) {
        query = query.lte('Date', endDate);
      }
      return query.overrideTypes<PitcherStatsTable[], { merge: false }>();
    },
  });
}

export async function fetchTeamPitchCounts(team: string, startDate?: string, endDate?: string) {
  return cachedQuery({
    key: createCacheKey('PitchCounts', {
      select: '*',
      eq: { PitcherTeam: team },
      range: { startDate, endDate },
    }),
    query: () => {
      let query = supabase.from('PitchCounts').select('*').eq('PitcherTeam', team);
      if (startDate) {
        query = query.gte('Date', startDate);
      }
      if (endDate) {
        query = query.lte('Date', endDate);
      }
      return query.overrideTypes<PitchCountsTable[], { merge: false }>();
    },
  });
}
