import { BatterStatsTable } from '@/types/schemas';
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

export default function BattingStatsTable({
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

  const [player, setPlayer] = useState<BatterStatsTable[]>([]);
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
    console.log('BattingStatsTable props:', {
      teamName,
      playerName,
      formattedPlayerName,
      year: safeYear,
    });
  }, [teamName, playerName, formattedPlayerName, safeYear]);

  useEffect(() => {
    async function fetchBatterStats() {
      // Always set loading to false even if we return early
      if (!formattedPlayerName || !teamName) {
        console.log('Missing required props:', { formattedPlayerName, teamName });
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        console.log('Fetching batter stats with:', {
          Batter: formattedPlayerName,
          BatterTeam: teamName,
          Year: safeYear,
        });

        const { data, error } = await supabase
          .from('BatterStats')
          .select('*')
          .eq('Batter', formattedPlayerName)
          .eq('BatterTeam', teamName)
          .eq('Year', safeYear)
          .overrideTypes<BatterStatsTable[], { merge: false }>();

        if (error) throw error;

        console.log('Batter stats fetched:', data);
        setPlayer(data || []);
      } catch (err) {
        console.error('Error fetching batter stats:', err);
        setError('Failed to load batter stats');
      } finally {
        setLoading(false);
      }
    }

    fetchBatterStats();
  }, [formattedPlayerName, teamName, safeYear]);

  useEffect(() => {
    const newTeam = params.teamName || 'NULL';
    setSelectedDataType(newTeam);
  }, [params.teamName]);

  const safePlayerName = encodeURIComponent(
    playerName || (player.length > 0 ? player[0].Batter : 'unknown-player'),
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

  // Add loading state monitoring
  useEffect(() => {
    console.log('Loading state:', loading, 'Player data length:', player.length);
  }, [loading, player]);

  return (
    <Paper elevation={3} sx={{ paddingX: 2, paddingY: 2, width: '100%', overflowX: 'auto' }}>
      {/* Section divider with title */}
      <Divider textAlign="center" sx={{ mb: 2 }}>
        Standard NCAA Batting Stats
      </Divider>
      {hasPracticePage && ['AUB_TIG', 'AUB_PRC'].includes(selectedDataType) && (
        // Render dropdown only for teams with practice data
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
              {/* Table headers with tooltips for clarity */}
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center', width: 50 }}>
                <Tooltip title="Games" arrow placement="top">
                  <span>G</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center', width: 50 }}>
                <Tooltip title="Plate Appearances" arrow placement="top">
                  <span>PA</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center', width: 50 }}>
                <Tooltip title="At Bats" arrow placement="top">
                  <span>AB</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center', width: 50 }}>
                <Tooltip title="Hits" arrow placement="top">
                  <span>H</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center', width: 50 }}>
                <Tooltip title="Home Runs" arrow placement="top">
                  <span>HR</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center', width: 50 }}>
                <Tooltip title="Base on Balls" arrow placement="top">
                  <span>BB</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center', width: 50 }}>
                <Tooltip title="Strikeouts" arrow placement="top">
                  <span>SO</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center', width: 50 }}>
                <Tooltip title="Hit By Pitch" arrow placement="top">
                  <span>HBP</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center', width: 50 }}>
                <Tooltip title="Batting Average" arrow placement="top">
                  <span>AVG</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center', width: 50 }}>
                <Tooltip title="On‑Base Percentage" arrow placement="top">
                  <span>OBP</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center', width: 50 }}>
                <Tooltip title="Slugging Percentage" arrow placement="top">
                  <span>SLG</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center', width: 50 }}>
                <Tooltip title="On‑Base Plus Slugging" arrow placement="top">
                  <span>OPS</span>
                </Tooltip>
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={12} sx={{ textAlign: 'center', padding: 2 }}>
                  <CircularProgress size={24} />
                </TableCell>
              </TableRow>
            ) : error ? (
              <TableRow>
                <TableCell colSpan={12} sx={{ textAlign: 'center', color: 'error.main' }}>
                  {error}
                </TableCell>
              </TableRow>
            ) : player.length > 0 ? (
              <TableRow>
                {/* Render batter statistics with proper formatting */}
                <TableCell sx={{ textAlign: 'center' }}>{player[0].games}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{player[0].plate_appearances}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{player[0].at_bats}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{player[0].hits}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{player[0].homeruns}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{player[0].walks}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{player[0].strikeouts}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{player[0].hit_by_pitch}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>
                  {player[0].batting_average === null
                    ? '.000'
                    : player[0].batting_average === 1
                      ? player[0].batting_average.toFixed(3)
                      : player[0].batting_average.toFixed(3).replace(/^0/, '')}
                </TableCell>
                <TableCell sx={{ textAlign: 'center' }}>
                  {player[0].on_base_percentage === null
                    ? '.000'
                    : player[0].on_base_percentage.toFixed(3).replace(/^0/, '')}
                </TableCell>
                <TableCell sx={{ textAlign: 'center' }}>
                  {player[0].slugging_percentage === null
                    ? '.000'
                    : player[0].slugging_percentage.toFixed(3).replace(/^0/, '')}
                </TableCell>
                <TableCell sx={{ textAlign: 'center' }}>
                  {player[0].onbase_plus_slugging === null
                    ? '.000'
                    : player[0].onbase_plus_slugging.toFixed(3).replace(/^0/, '')}
                </TableCell>
              </TableRow>
            ) : (
              <TableRow>
                <TableCell colSpan={12} sx={{ textAlign: 'center' }}>
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
