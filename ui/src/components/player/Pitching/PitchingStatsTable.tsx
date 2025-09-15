import { pitcher_stats_forTable } from '@/utils/types'; // Type definition for pitcher stats
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import { useRouter, useParams } from 'next/navigation';
import { MenuItem, Select, FormControl, InputLabel, SelectChangeEvent } from '@mui/material';
import { useState, useEffect } from 'react';
import Divider from '@mui/material/Divider';
import Tooltip from '@mui/material/Tooltip';

export default function PitchingStatsTable({
  player,
  teamName,
  playerName,
  startDate,
  endDate,
}: {
  player: pitcher_stats_forTable[];
  teamName: string | undefined; // Optional team identifier
  playerName: string | undefined; // Optional pitcher name
  startDate: string | undefined; // Optional start date for stats
  endDate: string | undefined; // Optional end date for stats
}) {
  const router = useRouter();
  const params = useParams();

  // Derive team name from URL parameters, default to "AUB_TIG" if missing
  const teamParam = Array.isArray(params.teamName)
    ? params.teamName[0]
    : params.teamName || 'AUB_TIG';

  // Determine if practice data is available based on player array length
  const hasPracticePage = player.length > 0;

  // Initialize selected data type state with the team parameter
  const [selectedDataType, setSelectedDataType] = useState<string>(teamParam);

  // Update selectedDataType when URL parameters change
  useEffect(() => {
    const newTeam = Array.isArray(params.teamName)
      ? params.teamName[0]
      : params.teamName || 'AUB_TIG';
    setSelectedDataType(newTeam);
  }, [params.teamName]);

  // Prepare safe parameters for URL navigation using defaults if values are missing
  const safePlayerName = encodeURIComponent(
    playerName || (player.length > 0 ? player[0].Pitcher : 'unknown-pitcher'),
  );
  const safeStartDate = startDate || '2024-02-16';

  // Calculate tomorrow's date as a fallback for endDate
  const today = new Date();
  const tomorrow = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 1);
  const safeEndDate = endDate || tomorrow.toISOString().split('T')[0];

  /**
   * Navigates to the selected team's page for the current player and date range.
   * @param newTeamName - The new team selected.
   */
  const handleNavigation = (newTeamName: string) => {
    if (!newTeamName || !['AUB_TIG', 'AUB_PRC'].includes(newTeamName)) {
      alert('Invalid team selected.');
      return;
    }
    router.push(
      `/team/${newTeamName}/player/${safePlayerName}/stats/${safeStartDate}/${safeEndDate}`,
    );
  };

  /**
   * Handles changes in the dropdown selection.
   * @param event - The select change event.
   */
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
            {player.length > 0 ? (
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
