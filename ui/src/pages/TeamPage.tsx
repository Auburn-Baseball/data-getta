import { useEffect, useState } from 'react';
import { Outlet, useParams, useSearchParams } from 'react-router';
import { useRef } from 'react';
import Box from '@mui/material/Box';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import TeamInfo from '@/components/team/TeamInfo';
import TableTabs from '@/components/team/TableTabs';
import { fetchTeamByAbbreviation } from '@/services/teamService';
import type { TeamsTable } from '@/types/db';
import type { DateRange } from '@/types/dateRange';
import { formatYearRange } from '@/utils/dateRange';

type TeamPageProps = {
  dateRange: DateRange;
};

export default function TeamPage({ dateRange }: TeamPageProps) {
  const { trackmanAbbreviation } = useParams<{ trackmanAbbreviation: string }>();
  const [searchParams, setSearchParams] = useSearchParams();

  const [team, setTeam] = useState<TeamsTable | null>(null);
  const [loading, setLoading] = useState(true);

  const practice = searchParams.get('practice') === 'true';

  const clearedOnce = useRef(false);
  useEffect(() => {
    if (clearedOnce.current) return;
    clearedOnce.current = true;
  
    // Default to OFF on entry: remove ?practice from URL if present
    const next = new URLSearchParams(searchParams);
    if (next.has('practice')) {
      next.delete('practice');
      setSearchParams(next, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  

  useEffect(() => {
    async function fetchTeam() {
      if (!trackmanAbbreviation) return;

      try {
        setLoading(true);
        const decodedTrackmanAbbreviation = decodeURIComponent(trackmanAbbreviation);
        console.log('Fetching team:', decodedTrackmanAbbreviation);

        const { data, error } = await fetchTeamByAbbreviation(
          dateRange,
          decodedTrackmanAbbreviation,
        );

        if (error) throw error;
        setTeam(data);
      } catch (error) {
        console.error('Error fetching team:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchTeam();
  }, [dateRange, trackmanAbbreviation]);

  const yearLabel = formatYearRange(dateRange);

  if (loading) return <div>Loading...</div>;
  if (!team) return <div>Team not found</div>;

  const isAuburn = team.TrackmanAbbreviation === 'AUB_TIG';

  const onPracticeToggle = (_: unknown, checked: boolean) => {
    const next = new URLSearchParams(searchParams);
    if (checked) next.set('practice', 'true');
    else next.delete('practice');
    setSearchParams(next, { replace: true });
  };

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
        {/* Header row: tabs on the left, optional practice toggle on the right */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 2,
            paddingRight: { xs: 4, sm: 8 },
          }}
        >
          <TableTabs trackmanAbbreviation={team.TrackmanAbbreviation!} />
          <Box sx={{ marginLeft: 'auto' }}>
            {isAuburn && (
              <FormControlLabel
                control={<Switch checked={practice} onChange={onPracticeToggle} />}
                label="Practice"
              />
            )}
          </Box>
        </Box>
      </Box>

      <Box sx={{ paddingX: { xs: 4, sm: 8 }, paddingY: 4 }}>
        <TeamInfo name={team.TeamName} conference={team.Conference} seasonLabel={yearLabel} />
        <Outlet />
      </Box>
    </Box>
  );
}
