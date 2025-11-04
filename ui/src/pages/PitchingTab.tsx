import { useEffect, useState } from 'react';
import { useParams, useLocation } from 'react-router';
import Box from '@mui/material/Box';

import PitcherTable from '@/components/team/PitcherTable';
import PitchSumsTable from '@/components/team/PitchSumsTable';
import TableSkeleton from '@/components/team/TableSkeleton';

import { fetchTeamPitchCounts, fetchTeamPitcherStats } from '@/services/teamService';
import { pitcherStatsTransform, pitchCountsTransform } from '@/transforms/pitcherStatsTransforms';

import type { PitchCountsTable, PitcherStatsTable } from '@/types/db';

type PitchingTabProps = {
  startDate: string;
  endDate: string;
};

export default function PitchingTab({ startDate, endDate }: PitchingTabProps) {
  const { trackmanAbbreviation } = useParams<{ trackmanAbbreviation: string }>();
  const location = useLocation();
  const practice = new URLSearchParams(location.search).get('practice') === 'true';

  const [pitchers, setPitchers] = useState<PitcherStatsTable[]>([]);
  const [pitches, setPitches] = useState<PitchCountsTable[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchPitching() {
      if (!trackmanAbbreviation) return;

      setLoading(true);
      try {
        const team = decodeURIComponent(trackmanAbbreviation);
        const range = { startDate, endDate };

        const [pitchersResp, pitchesResp] = await Promise.all([
          fetchTeamPitcherStats(team, range),
          fetchTeamPitchCounts(team, range),
        ]);

        if (pitchersResp.error) throw pitchersResp.error;
        if (pitchesResp.error) throw pitchesResp.error;

        // Apply practice filter client-side to preserve service shape
        const rawPitchers: PitcherStatsTable[] = pitchersResp.data ?? [];
        const rawPitches: PitchCountsTable[] = pitchesResp.data ?? [];

        const filter = <T extends { is_practice?: boolean | null }>(rows: T[]) =>
          practice
            ? rows.filter((r) => r?.is_practice === true)
            : rows.filter((r) => r?.is_practice === false || r?.is_practice == null);

        const filteredPitchers = filter(rawPitchers) as unknown as PitcherStatsTable[];
        const filteredPitches = filter(rawPitches) as unknown as PitchCountsTable[];

        // Transforms aggregate by player already
        const transformedPitchers = pitcherStatsTransform(filteredPitchers);
        const transformedPitches = pitchCountsTransform(filteredPitches);

        setPitchers(transformedPitchers);
        setPitches(transformedPitches);
      } catch (e) {
        console.error('Error fetching team pitching data:', e);
        setPitchers([]);
        setPitches([]);
      } finally {
        setLoading(false);
      }
    }

    fetchPitching();
  }, [trackmanAbbreviation, startDate, endDate, practice]);

  if (loading) return <TableSkeleton />;

  return (
    <Box>
      {/* per-pitcher summary stats */}
      <PitcherTable players={pitchers} />
      {/* per-pitcher pitch type/count distribution */}
      <PitchSumsTable players={pitches} />
    </Box>
  );
}
