import { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router';
import { supabase } from '@/utils/supabase/client';
import { PlayersTable } from '@/types/schemas';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

export default function PlayerPage() {
  const { trackmanAbbreviation } = useParams<{ trackmanAbbreviation: string }>();
  const [searchParams] = useSearchParams();
  const playerName = searchParams.get('player');

  const [player, setPlayer] = useState<PlayersTable | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchPlayer() {
      if (!trackmanAbbreviation || !playerName) return;

      try {
        const decodedTrackmanAbbreviation = decodeURIComponent(trackmanAbbreviation);
        const decodedPlayerName = decodeURIComponent(playerName);

        const { data, error } = await supabase
          .from('Players')
          .select('*')
          .eq('TeamTrackmanAbbreviation', decodedTrackmanAbbreviation)
          .eq('Name', decodedPlayerName)
          .eq('Year', 2025)
          .maybeSingle()
          .overrideTypes<PlayersTable, { merge: false }>();

        if (error && error.code !== 'PGRST116') throw error;
        // setPlayer(data || null);
      } catch (error) {
        console.error('Error fetching player:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchPlayer();
  }, [trackmanAbbreviation, playerName]);

  if (loading || !playerName) {
    return <Box>Loading...</Box>;
  }

  const decodedTeamName = decodeURIComponent(trackmanAbbreviation || '');
  const decodedPlayerName = decodeURIComponent(playerName);

  // Format player name for display
  const formatPlayerName = (name: string) => {
    const nameParts = name.includes(',') ? name.split(', ') : name.split(' ');

    return nameParts.length > 1 ? `${nameParts[1]} ${nameParts[0]}` : name;
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
        {/* TODO: Add ModelTabs component */}
        <Typography variant="h6">Player Tabs (TODO: ModelTabs component)</Typography>
      </Box>

      <Box sx={{ paddingX: { xs: 4, sm: 8 }, paddingY: 4 }}>
        {/* TODO: Add PlayerInfo component */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h4" fontWeight={700}>
            {formatPlayerName(decodedPlayerName)}
          </Typography>
          <Typography variant="h6" color="text.secondary">
            {decodedTeamName}
          </Typography>
        </Box>

        {/* Children content will go here */}
        <Typography variant="body1">Player content will be added here...</Typography>
      </Box>
    </Box>
  );
}
