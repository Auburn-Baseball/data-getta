import { supabase } from '@/lib/supabaseClient';
import { cachedQuery, createCacheKey } from '@/services/cacheService';
import type { SeasonDatesTable } from '@/types/db';

export type SeasonDateRange = {
  year: string;
  startDate: string;
  endDate: string;
};

type SeasonDateRangeResponse = {
  ranges: SeasonDateRange[];
  errorMessage?: string;
};

export async function fetchSeasonDateRanges(): Promise<SeasonDateRangeResponse> {
  const descriptor = {
    select: ['year', 'season_start', 'season_end'],
    order: [{ column: 'year', ascending: false }],
  } as const;

  try {
    const { data, error } = await cachedQuery({
      key: createCacheKey('SeasonDates', descriptor),
      query: () => {
        console.debug('[seasonService] fetching SeasonDates from Supabase', { descriptor });

        return supabase
          .from('SeasonDates')
          .select('year, season_start, season_end')
          .order('year', { ascending: false })
          .returns<SeasonDatesTable[]>();
      },
    });

    if (error) {
      const message = error.message ?? 'Unknown error loading season dates';
      console.error('Failed to load season date ranges:', error);
      return { ranges: [], errorMessage: message };
    }

    const rows = Array.isArray(data) ? data : [];

    const ranges = rows
      .filter((row) => row.season_start && row.season_end)
      .map((row) => ({
        year: String(row.year),
        startDate: row.season_start as string,
        endDate: row.season_end as string,
      }));

    console.debug('[seasonService] SeasonDates query result', { rowCount: rows.length, ranges });

    if (ranges.length === 0) {
      return { ranges: [], errorMessage: 'No season dates available.' };
    }

    return { ranges };
  } catch (err) {
    console.error('[seasonService] Exception fetching season dates:', err);
    return { ranges: [], errorMessage: 'Failed to load season dates.' };
  }
}
