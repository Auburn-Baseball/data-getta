import { useEffect, useState } from 'react';
import Grid from '@mui/material/Grid';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import ConferenceTable from '@/components/ConferenceTable';
import { fetchTeamsByDateRange } from '@/services/teamService';
import type { TeamsTable } from '@/types/db';
import type { ConferenceGroup, ConferenceGroupTeam } from '@/types';
import type { DateRange } from '@/types/dateRange';
import { formatYearRange } from '@/utils/dateRange';

type ConferencePageProps = {
  dateRange: DateRange;
};

export default function ConferencePage({ dateRange }: ConferencePageProps) {
  const [conferences, setConferences] = useState<ConferenceGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        const { data, error } = await fetchTeamsByDateRange(dateRange);

        if (error) {
          throw error;
        }

        const groupedData =
          data?.reduce((acc: Record<string, ConferenceGroupTeam[]>, team: TeamsTable) => {
            const conferenceKey = team.Conference ?? 'Unknown';
            if (!acc[conferenceKey]) {
              acc[conferenceKey] = [];
            }
            acc[conferenceKey].push({
              TeamName: team.TeamName ?? '',
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
  }, [dateRange]);

  const yearLabel = formatYearRange(dateRange);

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
        Conferences ({yearLabel})
      </Typography>
      {conferences.length === 0 ? (
        <Typography variant="body1" color="text.secondary">
          No teams found for the selected date range.
        </Typography>
      ) : (
        <Grid container spacing={2}>
          {conferences.map((confGroup, index) => (
            <Grid key={index} size={{ xs: 12, md: 6, xl: 4 }} sx={{ width: '100%' }}>
              <ConferenceTable conferenceGroup={confGroup} />
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
}
