import { useEffect, useState } from 'react';
import { useParams, useLocation } from 'react-router';

import BatterTable from '@/components/team/BatterTable';
import TableSkeleton from '@/components/team/TableSkeleton';
import {
  batterStatsTransform,
  createBatterStatsSummary,
} from '@/transforms/batterStatsTransform';
import { fetchTeamBattingStats } from '@/services/teamService';
import type { BatterStatsTable } from '@/types/db';

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
    async function run() {
      if (!trackmanAbbreviation) return;
      setLoading(true);
      try {
        const { data, error } = await fetchTeamBattingStats(trackmanAbbreviation, {
          startDate,
          endDate,
        });
        if (error) throw error;

        const raw = (data ?? []) as BatterStatsTable[];

        // Do a simple client-side practice filter to mimic the rest of the app.
        const filtered = practice
          ? raw.filter((r) => r?.is_practice === true)
          : raw.filter((r) => r?.is_practice === false || r?.is_practice == null);

        // *** Important: pass the mode so we aggregate to one row per player ***
        let transformed = batterStatsTransform(filtered, {
          mode: practice ? 'practiceOnly' : 'gameOnly',
        });

        // Defensive fallback: if transform ever returns [], keep it empty (no raw rows)
        if (transformed.length === 0) {
          transformed = [];
        }

        setBatters(transformed);
        setSummary(createBatterStatsSummary(transformed));
      } catch (e) {
        console.error('Error fetching team batting stats:', e);
        setBatters([]);
        setSummary(createBatterStatsSummary([]));
      } finally {
        setLoading(false);
      }
    }

    run();
  }, [trackmanAbbreviation, startDate, endDate, practice]);

  if (loading) return <TableSkeleton />;
  return <BatterTable players={batters} summaryRow={summary || createBatterStatsSummary([])} />;
}
