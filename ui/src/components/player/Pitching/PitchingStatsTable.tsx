import { PitcherStatsTable } from '@/types/schemas';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import {
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  SelectChangeEvent,
  CircularProgress,
} from '@mui/material';
import { useState, useEffect } from 'react';
import Divider from '@mui/material/Divider';
import Tooltip from '@mui/material/Tooltip';
import { supabase } from '@/utils/supabase/client';
import { useNavigate, useParams } from 'react-router';

export default function PitchingStatsTable({
  teamName,
  playerName,
  year,
}: {
  teamName: string | undefined;
  playerName: string | undefined;
  year: string | number | undefined;
}) {
  const navigate = useNavigate();
  const params = useParams();

  const [player, setPlayer] = useState<PitcherStatsTable[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const teamParam = params.teamName || 'NULL';
  const [selectedDataType, setSelectedDataType] = useState<string>(teamParam);

  // Default to current year if not specified
  const safeYear = year || 2025;

  // Format the player name to match database format (replace underscores with commas)
  const formattedPlayerName = playerName?.replace('_', ', ');

  // Debug the props being used
  useEffect(() => {
    console.log('PitchingStatsTable props:', {
      teamName,
      playerName,
      formattedPlayerName,
      year: safeYear,
    });
  }, [teamName, playerName, formattedPlayerName, safeYear]);

  useEffect(() => {
    async function fetchPitcherStats() {
      // Always set loading to false even if we return early
      if (!formattedPlayerName || !teamName) {
        console.log('Missing required props:', { formattedPlayerName, teamName });
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        console.log('Fetching pitcher stats with:', {
          Pitcher: formattedPlayerName,
          PitcherTeam: teamName,
          Year: safeYear,
        });

        const { data, error } = await supabase
          .from('PitcherStats')
          .select('*')
          .eq('Pitcher', formattedPlayerName)
          .eq('PitcherTeam', teamName)
          .eq('Year', safeYear)
          .overrideTypes<PitcherStatsTable[], { merge: false }>();

        if (error) throw error;

        console.log('Pitcher stats fetched:', data);
        setPlayer(data || []);
      } catch (err) {
        console.error('Error fetching pitcher stats:', err);
        setError('Failed to load pitcher stats');
      } finally {
        setLoading(false);
      }
    }

    fetchPitcherStats();
  }, [formattedPlayerName, teamName, safeYear]);

  // Add loading state monitoring
  useEffect(() => {
    console.log('Loading state:', loading, 'Player data length:', player.length);
  }, [loading, player]);

  useEffect(() => {
    const newTeam = params.teamName || 'NULL';
    setSelectedDataType(newTeam);
  }, [params.teamName]);

  const safePlayerName = encodeURIComponent(
    playerName || (player.length > 0 ? player[0].Pitcher : 'unknown-pitcher'),
  );

  const hasPracticePage = player.length > 0;

  const handleNavigation = (newTeamName: string) => {
    if (!newTeamName || !['AUB_TIG', 'AUB_PRC'].includes(newTeamName)) {
      alert('Invalid team selected.');
      return;
    }
    navigate(`/team/${newTeamName}/player/${safePlayerName}/stats/${safeYear}`);
  };

  const handleSelectChange = (event: SelectChangeEvent<string>) => {
    const newValue = event.target.value;
    setSelectedDataType(newValue);
    handleNavigation(newValue);
  };

  return (
    <Paper elevation={3} sx={{ paddingX: 2, paddingY: 2, width: '100%', overflowX: 'auto' }}>
      {/* Render header divider with title */}
      <Divider textAlign="center" sx={{ mb: 2 }}>
        Standard NCAA Pitching Stats
      </Divider>
      {hasPracticePage && ['AUB_TIG', 'AUB_PRC'].includes(selectedDataType) && (
        // Conditionally render dropdown only for teams with practice data.
        <FormControl fullWidth sx={{ marginBottom: '1rem' }}>
          <InputLabel id="data-type-select-label">Data Type</InputLabel>
          <Select
            labelId="data-type-select-label"
            value={selectedDataType}
            onChange={handleSelectChange}
            label="Data Type"
          >
            <MenuItem value="AUB_TIG">Game Data</MenuItem>
            <MenuItem value="AUB_PRC">Practice Data</MenuItem>
          </Select>
        </FormControl>
      )}
      <TableContainer>
        <Table sx={{ minWidth: 800 }} size="small">
          <TableHead>
            <TableRow>
              {/* Table header cells for key pitching statistics */}
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center', width: 60 }}>
                <Tooltip title="Batters Faced" arrow placement="top">
                  <span>BF</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center', width: 50 }}>
                <Tooltip title="Games" arrow placement="top">
                  <span>G</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center', width: 50 }}>
                <Tooltip title="Games Started" arrow placement="top">
                  <span>GS</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center', width: 70 }}>
                <Tooltip title="Innings Pitched" arrow placement="top">
                  <span>IP</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center', width: 60 }}>
                <Tooltip title="Base on Balls" arrow placement="top">
                  <span>BB</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center', width: 60 }}>
                <Tooltip title="Strikeouts" arrow placement="top">
                  <span>SO</span>
                </Tooltip>
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={6} sx={{ textAlign: 'center', padding: 2 }}>
                  <CircularProgress size={24} />
                </TableCell>
              </TableRow>
            ) : error ? (
              <TableRow>
                <TableCell colSpan={6} sx={{ textAlign: 'center', color: 'error.main' }}>
                  {error}
                </TableCell>
              </TableRow>
            ) : player.length > 0 ? (
              <TableRow>
                {/* Render calculated statistics */}
                <TableCell sx={{ textAlign: 'center' }}>{player[0].total_batters_faced}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{player[0].games}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{player[0].games_started}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>
                  {player[0].total_innings_pitched}
                </TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{player[0].total_walks_pitcher}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>
                  {player[0].total_strikeouts_pitcher}
                </TableCell>
              </TableRow>
            ) : (
              // Render fallback row when no data is available
              <TableRow>
                <TableCell colSpan={6} sx={{ textAlign: 'center' }}>
                  No Data Available
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
}
