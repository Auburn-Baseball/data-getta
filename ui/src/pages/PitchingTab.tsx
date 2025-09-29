import { useState, useEffect } from 'react';
import { useParams } from 'react-router';
import { supabase } from '@/utils/supabase/client';
import PitcherTable from '@/components/team/PitcherTable';
import PitchSumsTable from '@/components/team/PitchSumsTable';
import { PitcherStatsTable, PitchCountsTable } from '@/types/schemas';
import TableSkeleton from '@/components/team/TableSkeleton';
import Box from '@mui/material/Box';

export default function PitchingTab() {
  const { trackmanAbbreviation } = useParams<{ trackmanAbbreviation: string }>();
  const [pitchers, setPitchers] = useState<PitcherStatsTable[]>([]);
  const [pitches, setPitches] = useState<PitchCountsTable[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchPitchers() {
      if (!trackmanAbbreviation) return;

      try {
        const decodedTrackmanAbbreviation = decodeURIComponent(trackmanAbbreviation);
        console.log(decodedTrackmanAbbreviation);

        const [pitchersResponse, pitchesResponse] = await Promise.all([
          supabase
            .from('PitcherStats')
            .select('*')
            .eq('PitcherTeam', decodedTrackmanAbbreviation)
            .eq('Year', 2025)
            .order('total_innings_pitched', { ascending: false })
            .overrideTypes<PitcherStatsTable[], { merge: false }>(),
          supabase
            .from('PitchCounts')
            .select('*')
            .eq('PitcherTeam', decodedTrackmanAbbreviation)
            .eq('Year', 2025)
            .order('total_pitches', { ascending: false })
            .overrideTypes<PitchCountsTable[], { merge: false }>(),
        ]);

        if (pitchersResponse.error) throw pitchersResponse.error;
        if (pitchesResponse.error) throw pitchesResponse.error;

        setPitchers(pitchersResponse.data || []);
        setPitches(pitchesResponse.data || []);
      } catch (error) {
        console.error('Error fetching pitchers:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchPitchers();
  }, [trackmanAbbreviation]);

  if (loading) return <TableSkeleton />;

  return (
    <Box>
      <PitcherTable players={pitchers} />
      <PitchSumsTable players={pitches} />
    </Box>
  );
}
