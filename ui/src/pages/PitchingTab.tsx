import { useEffect, useState } from 'react';
import { useParams, useLocation } from 'react-router';
import Box from '@mui/material/Box';

import PitcherTable from '@/components/team/PitcherTable';
import PitchSumsTable from '@/components/team/PitchSumsTable';
import TableSkeleton from '@/components/team/TableSkeleton';
import { fetchTeamPitchCounts, fetchTeamPitcherStats } from '@/services/teamService';
import type { PitchCountsTable, PitcherStatsTable } from '@/types/db';
import { pitcherStatsTransform, pitchCountsTransform } from '@/transforms/pitcherStatsTransforms';

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
    async function fetchPitchers() {
      if (!trackmanAbbreviation) return;

      try {
        setLoading(true);
        const decodedTrackmanAbbreviation = decodeURIComponent(trackmanAbbreviation);

        const range = { startDate, endDate };

        const [pitchersResponse, pitchesResponse] = await Promise.all([
          fetchTeamPitcherStats(decodedTrackmanAbbreviation, range),
          fetchTeamPitchCounts(decodedTrackmanAbbreviation, range),
        ]);

        if (pitchersResponse.error) throw pitchersResponse.error;
        if (pitchesResponse.error) throw pitchesResponse.error;

        // Apply practice filter client-side to preserve service shape
        const rawPitchers = (pitchersResponse.data ?? []) as unknown as Array<Record<string, any>>;
        const rawPitches = (pitchesResponse.data ?? []) as unknown as Array<Record<string, any>>;

        const filteredPitchers = practice
          ? rawPitchers.filter((r) => r?.is_practice === true)
          : rawPitchers.filter((r) => r?.is_practice === false || r?.is_practice == null);

        const filteredPitches = practice
          ? rawPitches.filter((r) => r?.is_practice === true)
          : rawPitches.filter((r) => r?.is_practice === false || r?.is_practice == null);

        const transformedPitchers = pitcherStatsTransform(filteredPitchers as unknown as PitcherStatsTable[]);
        const transformedPitches = pitchCountsTransform(filteredPitches as unknown as PitchCountsTable[]);

        setPitchers(transformedPitchers);
        setPitches(transformedPitches);
      } catch (error) {
        console.error('Error fetching pitchers:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchPitchers();
  }, [endDate, startDate, trackmanAbbreviation, practice]);

  if (loading) return <TableSkeleton />;

  return (
    <Box>
      <PitcherTable players={pitchers} />
      <PitchSumsTable players={pitches} />
    </Box>
  );
}
