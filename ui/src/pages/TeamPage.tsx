import { useState, useEffect } from 'react';
import { useParams, Outlet, useSearchParams } from 'react-router';
import Box from '@mui/material/Box';
import TeamInfo from '@/components/team/TeamInfo';
import TableTabs from '@/components/team/TableTabs';
import { supabase } from '@/utils/supabase/client';
import { cachedQuery, createCacheKey } from '@/utils/supabase/cache';
import { TeamsTable } from '@/types/schemas';

type TeamPageProps = {
  year: number;
};

export default function TeamPage({ year }: TeamPageProps) {
  const [searchParams] = useSearchParams();
  const playerParam = searchParams.get('player');
  const { trackmanAbbreviation } = useParams<{ trackmanAbbreviation: string }>();
  const [team, setTeam] = useState<TeamsTable | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchTeam() {
      if (!trackmanAbbreviation) return;

      try {
        const decodedTrackmanAbbreviation = decodeURIComponent(trackmanAbbreviation);
        console.log('Fetching team:', decodedTrackmanAbbreviation);

        const { data, error } = await cachedQuery({
          key: createCacheKey('Teams', {
            select: ['TeamName', 'TrackmanAbbreviation', 'Conference'],
            eq: {
              TrackmanAbbreviation: decodedTrackmanAbbreviation,
              Year: year,
            },
            single: true,
          }),
          query: () =>
            supabase
              .from('Teams')
              .select('TeamName, TrackmanAbbreviation, Conference')
              .eq('TrackmanAbbreviation', decodedTrackmanAbbreviation)
              .eq('Year', year)
              .single()
              .overrideTypes<TeamsTable, { merge: false }>(),
        });

        if (error) throw error;
        setTeam(data);
      } catch (error) {
        console.error('Error fetching team:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchTeam();
  }, [trackmanAbbreviation, year]);

  if (loading) return <div>Loading...</div>;
  if (!team) return <div>Team not found</div>;

  return (
    <Box>
      <Box
        sx={{
          backgroundColor: '#f5f5f5',
          paddingLeft: { xs: 4, sm: 8 },
          paddingY: 2,
          marginTop: '4px',
        }}
      >
        <TableTabs trackmanAbbreviation={team.TrackmanAbbreviation!} />
      </Box>

      <Box sx={{ paddingX: { xs: 4, sm: 8 }, paddingY: 4 }}>
        <TeamInfo name={team.TeamName} conference={team.Conference} year={year} />
        <Outlet />
      </Box>
    </Box>
  );
}
