import { useEffect, useState } from 'react';
import { Outlet, useLocation, useNavigate, useParams } from 'react-router';
import Box from '@mui/material/Box';

import ModelTabs from '@/components/player/ModelTabs';
import PlayerInfo from '@/components/player/PlayerInfo';
import { fetchPlayer } from '@/services/playerService';
import type { PlayersTable } from '@/types/db';
import type { DateRange } from '@/types/dateRange';
import { formatYearRange } from '@/utils/dateRange';

type PlayerPageProps = {
  dateRange: DateRange;
};

export default function PlayerPage({ dateRange }: PlayerPageProps) {
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
      const seasonSlug = formatYearRange(dateRange);

      if (location.pathname === playerPath || location.pathname === `${playerPath}/stats`) {
        navigate(
          {
            pathname: `${playerPath}/stats/${seasonSlug}`,
            search: `?start=${dateRange.startDate}&end=${dateRange.endDate}`,
          },
          { replace: true },
        );
      }
    }
  }, [dateRange, location.pathname, navigate, playerName, trackmanAbbreviation]);

  useEffect(() => {
    async function loadPlayer() {
      if (!trackmanAbbreviation || !playerName) return;

      try {
        const decodedTrackmanAbbreviation = decodeURIComponent(trackmanAbbreviation);
        const decodedPlayerName = decodeURIComponent(playerName).split('_').join(', ');
        setLoading(true);

        const { data, error } = await fetchPlayer(
          dateRange,
          decodedTrackmanAbbreviation,
          decodedPlayerName,
        );

        if (error) throw error;
        setPlayer(data);
      } catch (error) {
        console.error('Error fetching player:', error);
      } finally {
        setLoading(false);
      }
    }

    loadPlayer();
  }, [dateRange, playerName, trackmanAbbreviation]);

  if (loading) {
    return <div>Loading...</div>;
  }
  if (!playerName || !player) {
    return <div>Player not found</div>;
  }

  const decodedTeamName = decodeURIComponent(trackmanAbbreviation || '');
  const decodedPlayerName = decodeURIComponent(playerName);
  const seasonLabel = formatYearRange(dateRange);

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
        <ModelTabs team={decodedTeamName} player={decodedPlayerName} seasonSlug={seasonLabel} />
      </Box>

      <Box sx={{ paddingX: { xs: 4, sm: 8 }, paddingY: 4 }}>
        <PlayerInfo
          name={player.Name}
          team={player.TeamTrackmanAbbreviation}
          seasonLabel={seasonLabel}
        />
        <Outlet />
      </Box>
    </Box>
  );
}
