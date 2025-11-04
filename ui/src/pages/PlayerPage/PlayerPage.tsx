import { useEffect, useState } from 'react';
import { useRef } from 'react';
import { Outlet, useLocation, useNavigate, useParams, useSearchParams } from 'react-router';
import Box from '@mui/material/Box';
import ModelTabs from '@/components/player/ModelTabs';
import PlayerInfo from '@/components/player/PlayerInfo';
import { fetchPlayer } from '@/services/playerService';
import type { PlayersTable } from '@/types/db';
import type { DateRange } from '@/types/dateRange';
import { formatYearRange } from '@/utils/dateRange';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';

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

  const [searchParams, setSearchParams] = useSearchParams();
  const practice = searchParams.get('practice') === 'true';

  const decodedTeamName = decodeURIComponent(trackmanAbbreviation || '');
  const decodedPlayerName = decodeURIComponent(playerName || '');
  const seasonLabel = formatYearRange(dateRange);

  const isAuburn = decodedTeamName === 'AUB_TIG';

  const clearedOnce = useRef(false);
  useEffect(() => {
    if (clearedOnce.current) return;
    clearedOnce.current = true;

    // Default to OFF on entry: remove ?practice from URL if present
    const next = new URLSearchParams(searchParams);
    if (!isAuburn && next.has('practice')) {
      next.delete('practice');
      setSearchParams(next, { replace: true });
    } else if (next.has('practice')) {
      next.delete('practice');
      setSearchParams(next, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuburn]);

  const handlePracticeToggle = (_e: React.ChangeEvent<HTMLInputElement>, checked: boolean) => {
    const next = new URLSearchParams(searchParams);
    if (checked) next.set('practice', 'true');
    else next.delete('practice'); // keep URL clean, and treat "off" as non-practice
    setSearchParams(next);
  };

  // Keep the canonical stats route with current date range and existing search params (incl. practice)
  useEffect(() => {
    if (trackmanAbbreviation && playerName) {
      const playerPath = `/team/${trackmanAbbreviation}/player/${playerName}`;
      const seasonSlug = formatYearRange(dateRange);

      if (location.pathname === playerPath || location.pathname === `${playerPath}/stats`) {
        const next = new URLSearchParams(searchParams);
        next.set('start', dateRange.startDate);
        next.set('end', dateRange.endDate);
        next.delete('practice'); // prevent bleed + default OFF

        navigate(
          { pathname: `${playerPath}/stats/${seasonSlug}`, search: `?${next.toString()}` },
          { replace: true },
        );
      }
    }
  }, [dateRange, location.pathname, navigate, playerName, trackmanAbbreviation, searchParams]);

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

  return (
    <Box>
      <Box
        sx={{
          backgroundColor: '#f5f5f5',
          paddingLeft: { xs: 4, sm: 8 },
          paddingRight: { xs: 4, sm: 8 },
          paddingY: 2,
          marginTop: '4px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <ModelTabs team={decodedTeamName} player={decodedPlayerName} seasonSlug={seasonLabel} />

        {isAuburn && (
          <FormControlLabel
            control={
              <Switch
                checked={practice}
                onChange={handlePracticeToggle}
                inputProps={{ 'aria-label': 'Practice data' }}
              />
            }
            label="Practice"
            sx={{ marginLeft: 'auto' }}
          />
        )}
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
