// TODO: Had an issue with batterStatsTransform returning an empty array even when there was valid data in the filtered rows.
// fallback has been implemented for now

import { useEffect, useState } from 'react';
import { useParams, useLocation } from 'react-router';

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
  const location = useLocation();
  const practice = new URLSearchParams(location.search).get('practice') === 'true';

  const [batters, setBatters] = useState<BatterStatsTable[]>([]);
  const [summary, setSummary] = useState<BatterStatsTable | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchBatters() {
      if (!trackmanAbbreviation) return;

      try {
        setLoading(true);
        const decodedTrackmanAbbreviation = decodeURIComponent(trackmanAbbreviation);

        const { data, error } = await fetchTeamBattingStats(decodedTrackmanAbbreviation, {
          startDate,
          endDate,
        });
        if (error) throw error;

        const raw = Array.isArray(data) ? data : [];

        // Respect the practice toggle like PitchingTab
        const filtered = practice
          ? raw.filter((r: any) => r?.is_practice === true)
          : raw.filter((r: any) => r?.is_practice === false || r?.is_practice == null);

        // Transform; if it returns empty but we have filtered rows,
        // fall back to the filtered rows so the table isn't blank.
        const transformed = batterStatsTransform(filtered as BatterStatsTable[]);
        const safe = transformed.length === 0 && filtered.length > 0
          ? (filtered as BatterStatsTable[])
          : transformed;

        setBatters(safe);
        setSummary(createBatterStatsSummary(safe));
      } catch (error) {
        console.error('Error fetching batters:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchBatters();
  }, [endDate, startDate, trackmanAbbreviation, practice]);

  if (loading) return <TableSkeleton />;
  return <BatterTable players={batters} summaryRow={summary || createBatterStatsSummary([])} />;
}
