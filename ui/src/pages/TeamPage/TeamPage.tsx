import { useEffect, useState } from 'react';
import { Outlet, useParams } from 'react-router';
import Box from '@mui/material/Box';

import TeamInfo from '@/components/team/TeamInfo';
import TableTabs from '@/components/team/TableTabs';
import { fetchTeamByAbbreviation } from '@/services/teamService';
import type { TeamsTable } from '@/types/db';

type TeamPageProps = {
  year: number;
};

export default function TeamPage({ year }: TeamPageProps) {
  const { trackmanAbbreviation } = useParams<{ trackmanAbbreviation: string }>();
  const [team, setTeam] = useState<TeamsTable | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchTeam() {
      if (!trackmanAbbreviation) return;

      try {
        setLoading(true);
        const decodedTrackmanAbbreviation = decodeURIComponent(trackmanAbbreviation);
        console.log('Fetching team:', decodedTrackmanAbbreviation);

        const { data, error } = await fetchTeamByAbbreviation(year, decodedTrackmanAbbreviation);

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
