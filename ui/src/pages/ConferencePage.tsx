import { useEffect, useState } from 'react';
import Grid from '@mui/material/Grid';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import ConferenceTable from '@/components/ConferenceTable';
import { supabase } from '@/utils/supabase/client';
import { TeamsTable } from '@/types/schemas';
import { ConferenceGroup, ConferenceGroupTeam } from '@/types/types';

export default function ConferencePage() {
  const [conferences, setConferences] = useState<ConferenceGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        const { data, error } = await supabase
          .from('Teams')
          .select('*')
          .eq('Year', 2025) // change this to match the year passed into the page
          .order('Conference', { ascending: true })
          .order('TeamName', { ascending: true })
          .overrideTypes<TeamsTable[], { merge: false }>();

        if (error) {
          throw error;
        }

        const groupedData =
          data?.reduce((acc: Record<string, ConferenceGroupTeam[]>, team: TeamsTable) => {
            const conference = team.Conference;
            if (!acc[conference]) {
              acc[conference] = [];
            }
            acc[conference].push({
              TeamName: team.TeamName,
              TrackmanAbbreviation: team.TrackmanAbbreviation,
            });
            return acc;
          }, {}) || {};

        const conferenceArray: ConferenceGroup[] = Object.entries(groupedData)
          .map(([conferenceName, teams]) => ({
            ConferenceName: conferenceName,
            teams,
          }))
          .sort((a, b) => b.teams.length - a.teams.length);

        setConferences(conferenceArray);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
        console.error('Error fetching conference data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <Box sx={{ px: 8, py: 4 }}>
        <Typography variant="h6">Loading conferences...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ px: 8, py: 4 }}>
        <Typography variant="h6" color="error">
          Error: {error}
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ px: 8, py: 4 }}>
      <Typography variant="h4" fontWeight={700} sx={{ pb: 4 }}>
        Conferences
      </Typography>

      <Grid container spacing={2}>
        {conferences.map((confGroup, index) => (
          <Grid key={index} size={{ xs: 12, md: 6, xl: 4 }} sx={{ width: '100%' }}>
            <ConferenceTable conferenceGroup={confGroup} />
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
