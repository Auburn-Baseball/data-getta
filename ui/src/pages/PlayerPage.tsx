import { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate, Outlet } from 'react-router';
import { supabase } from '@/utils/supabase/client';
import { cachedQuery, createCacheKey } from '@/utils/supabase/cache';
import { PlayersTable } from '@/types/schemas';
import Box from '@mui/material/Box';
import ModelTabs from '@/components/player/ModelTabs';
import PlayerInfo from '@/components/player/PlayerInfo';

type PlayerPageProps = {
  year: number;
};

export default function PlayerPage({ year }: PlayerPageProps) {
  const { trackmanAbbreviation, playerName } = useParams<{
    trackmanAbbreviation: string;
    playerName: string;
  }>();
  const location = useLocation();
  const navigate = useNavigate();

  const [player, setPlayer] = useState<PlayersTable | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (trackmanAbbreviation && playerName) {
      const playerPath = `/team/${trackmanAbbreviation}/player/${playerName}`;

      if (location.pathname === playerPath || location.pathname === `${playerPath}/stats`) {
        navigate(`${playerPath}/stats/${year}`, { replace: true });
      }
    }
  }, [location.pathname, trackmanAbbreviation, playerName, navigate]);

  useEffect(() => {
    async function fetchPlayer() {
      if (!trackmanAbbreviation || !playerName) return;

      try {
        const decodedTrackmanAbbreviation = decodeURIComponent(trackmanAbbreviation);
        const decodedPlayerName = decodeURIComponent(playerName).split('_').join(', ');
        console.log(decodedPlayerName);
        setLoading(true);

        const { data, error } = await cachedQuery({
          key: createCacheKey('Players', {
            select: '*',
            eq: {
              TeamTrackmanAbbreviation: decodedTrackmanAbbreviation,
              Name: decodedPlayerName,
              Year: year,
            },
            maybeSingle: true,
          }),
          query: () =>
            supabase
              .from('Players')
              .select('*')
              .eq('TeamTrackmanAbbreviation', decodedTrackmanAbbreviation)
              .eq('Name', decodedPlayerName)
              .eq('Year', year)
              .maybeSingle(),
        });

        if (error) throw error;
        console.log('Fetched player data:', data);
        setPlayer(data);
      } catch (error) {
        console.error('Error fetching player:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchPlayer();
  }, [trackmanAbbreviation, playerName, year]);

  if (loading) {
    return <div>Loading...</div>;
  }
  if (!playerName || !player) {
    console.log('Player not found:', { trackmanAbbreviation, playerName, player });
    return <div>Player not found</div>;
  }

  const decodedTeamName = decodeURIComponent(trackmanAbbreviation || '');
  const decodedPlayerName = decodeURIComponent(playerName);

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
        <ModelTabs team={decodedTeamName} player={decodedPlayerName} />
      </Box>

      <Box sx={{ paddingX: { xs: 4, sm: 8 }, paddingY: 4 }}>
        <PlayerInfo name={player.Name} team={player.TeamTrackmanAbbreviation} year={year} />
        <Outlet />
      </Box>
    </Box>
  );
}
