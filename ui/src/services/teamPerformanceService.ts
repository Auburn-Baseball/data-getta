import { supabase } from '@/lib/supabaseClient';
import { cachedQuery, createCacheKey } from '@/services/cacheService';
import type { AdvancedBattingStatsTable, AdvancedPitchingStatsTable } from '@/types/db';
import type { DateRange } from '@/types/dateRange';
import { getYearRange } from '@/utils/dateRange';

const toRangeDescriptor = (range: DateRange) => ({
  range: { startDate: range.startDate, endDate: range.endDate },
});

export async function fetchAdvancedBattingStats(range: DateRange) {
  const { startYear, endYear } = getYearRange(range);

  return cachedQuery({
    key: createCacheKey('AdvancedBattingStats', {
      select: '*',
      ...toRangeDescriptor(range),
    }),
    query: () =>
      supabase
        .from('AdvancedBattingStats')
        .select('*')
        .gte('Year', startYear)
        .lte('Year', endYear)
        .overrideTypes<AdvancedBattingStatsTable[], { merge: false }>(),
  });
}

export async function fetchAdvancedPitchingStats(range: DateRange) {
  const { startYear, endYear } = getYearRange(range);

  return cachedQuery({
    key: createCacheKey('AdvancedPitchingStats', {
      select: '*',
      ...toRangeDescriptor(range),
    }),
    query: () =>
      supabase
        .from('AdvancedPitchingStats')
        .select('*')
        .gte('Year', startYear)
        .lte('Year', endYear)
        .overrideTypes<AdvancedPitchingStatsTable[], { merge: false }>(),
  });
}
