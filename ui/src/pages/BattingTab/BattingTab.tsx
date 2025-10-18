import { useEffect, useState } from 'react';
import { useParams } from 'react-router';

import BatterTable from '@/components/team/BatterTable';
import TableSkeleton from '@/components/team/TableSkeleton';
import { fetchTeamBattingStats } from '@/services/teamService';
import type { BatterStatsTable } from '@/types/db';
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
        setLoading(true);
        const decodedTrackmanAbbreviation = decodeURIComponent(trackmanAbbreviation);

        const { data, error } = await fetchTeamBattingStats(
          decodedTrackmanAbbreviation,
          startDate || undefined,
          endDate || undefined,
        );

        if (error) throw error;

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
