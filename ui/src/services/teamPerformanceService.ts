import { supabase } from '@/lib/supabaseClient';
import { cachedQuery, createCacheKey } from '@/services/cacheService';
import type { AdvancedBattingStatsTable, AdvancedPitchingStatsTable } from '@/types/db';

export async function fetchAdvancedBattingStatsByYear(year: number) {
  return cachedQuery({
    key: createCacheKey('AdvancedBattingStats', {
      select: '*',
      eq: { Year: year },
    }),
    query: () =>
      supabase
        .from('AdvancedBattingStats')
        .select('*')
        .eq('Year', year)
        .overrideTypes<AdvancedBattingStatsTable[], { merge: false }>(),
  });
}

export async function fetchAdvancedPitchingStatsByYear(year: number) {
  return cachedQuery({
    key: createCacheKey('AdvancedPitchingStats', {
      select: '*',
      eq: { Year: year },
    }),
    query: () =>
      supabase
        .from('AdvancedPitchingStats')
        .select('*')
        .eq('Year', year)
        .overrideTypes<AdvancedPitchingStatsTable[], { merge: false }>(),
  });
}
