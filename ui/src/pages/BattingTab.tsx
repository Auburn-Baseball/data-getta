import { useState, useEffect } from 'react';
import { useParams } from 'react-router';
import { supabase } from '@/utils/supabase/client';
import { cachedQuery, createCacheKey } from '@/utils/supabase/cache';
import BatterTable from '@/components/team/BatterTable';
import { BatterStatsTable } from '@/types/schemas';
import TableSkeleton from '@/components/team/TableSkeleton';
import { batterStatsTransform, createBatterStatsSummary } from '@/transforms/batterStatsTransform';

type BattingTabProps = {
  startDate: string;
  endDate: string;
};

export default function BattingTab({ startDate, endDate }: BattingTabProps) {
  const { trackmanAbbreviation } = useParams<{ trackmanAbbreviation: string }>();
  const [batters, setBatters] = useState<BatterStatsTable[]>([]);
  const [summary, setSummary] = useState<BatterStatsTable | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchBatters() {
      if (!trackmanAbbreviation) return;

      try {
        const decodedTrackmanAbbreviation = decodeURIComponent(trackmanAbbreviation);

        const { data, error } = await cachedQuery({
          key: createCacheKey('BatterStats', {
            select: '*',
            eq: { BatterTeam: decodedTrackmanAbbreviation },
            range: {
              startDate,
              endDate,
            },
          }),
          query: () =>
            supabase
              .from('BatterStats')
              .select('*')
              .eq('BatterTeam', decodedTrackmanAbbreviation)
              .gte('Date', startDate)
              .lte('Date', endDate)
              .overrideTypes<BatterStatsTable[], { merge: false }>(),
        });

        if (error) throw error;
        console.log('Fetched batters:', data);

        const transformedData = batterStatsTransform(data);
        setBatters(transformedData);

        const summaryRow = createBatterStatsSummary(transformedData);
        setSummary(summaryRow);
      } catch (error) {
        console.error('Error fetching batters:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchBatters();
  }, [trackmanAbbreviation, startDate, endDate]);

  if (loading) return <TableSkeleton />;
  return <BatterTable players={batters} summaryRow={summary || createBatterStatsSummary([])} />;
}
