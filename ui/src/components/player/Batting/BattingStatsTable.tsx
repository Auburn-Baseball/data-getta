import { batter_stats_forTable } from '@/utils/types';
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

export default function BattingStatsTable({
  player,
  teamName,
  playerName,
  startDate,
  endDate,
}: {
  player: batter_stats_forTable[];
  teamName: string | undefined; // Team identifier (optional).
  playerName: string | undefined; // Batter name (optional).
  startDate: string | undefined; // Stats start date.
  endDate: string | undefined; // Stats end date.
}) {
  const router = useRouter();
  const params = useParams();
  // Retrieve team name from URL params or default to "AUB_TIG"
  const teamParam = Array.isArray(params.teamName)
    ? params.teamName[0]
    : params.teamName || 'AUB_TIG';

  // Check if player data exists to conditionally render the practice data dropdown.
  const hasPracticePage = player.length > 0;

  // Initialize selectedDataType state with teamParam value.
  const [selectedDataType, setSelectedDataType] = useState<string>(teamParam);

  // Sync the selected data type with URL parameter changes.
  useEffect(() => {
    const newTeam = Array.isArray(params.teamName)
      ? params.teamName[0]
      : params.teamName || 'AUB_TIG';
    setSelectedDataType(newTeam);
  }, [params.teamName]);

  // Create safe URL parameters using defaults if necessary.
  const safePlayerName = encodeURIComponent(
    playerName || (player.length > 0 ? player[0].Batter : 'unknown-player'),
  );
  const safeStartDate = startDate || '2024-02-16';

  // Calculate tomorrow's date for the default end date using local time zone.
  const today = new Date();
  const tomorrow = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 1);
  const safeEndDate = endDate || tomorrow.toISOString().split('T')[0];

  /**
   * Handle navigation when a new team is selected.
   * Validates the team name before navigating.
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
   * Processes the dropdown change event.
   * Updates local state and triggers navigation.
   */
  const handleSelectChange = (event: SelectChangeEvent<string>) => {
    const newValue = event.target.value;
    setSelectedDataType(newValue);
    handleNavigation(newValue);
  };

  return (
    <Paper elevation={3} sx={{ paddingX: 2, paddingY: 2, width: '100%', overflowX: 'auto' }}>
      {/* Section divider with title */}
      <Divider textAlign="center" sx={{ mb: 2 }}>
        Standard NCAA Batting Stats
      </Divider>
      {hasPracticePage && ['AUB_TIG', 'AUB_PRC'].includes(selectedDataType) && (
        // Render dropdown only for teams with practice data.
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
            {player.length > 0 ? (
              <TableRow>
                {/* Render batter statistics; note: formatting AVG, OBP, SLG, OPS for readability */}
                <TableCell sx={{ textAlign: 'center' }}>{player[0].games}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{player[0].plate_appearances}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{player[0].at_bats}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{player[0].hits}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{player[0].homeruns}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{player[0].walks}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{player[0].strikeouts}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{player[0].hit_by_pitch}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>
                  {player[0].batting_average === 1
                    ? player[0].batting_average.toFixed(3)
                    : player[0].batting_average.toFixed(3).replace(/^0/, '')}
                </TableCell>
                <TableCell sx={{ textAlign: 'center' }}>
                  {player[0].on_base_percentage.toFixed(3).replace(/^0/, '')}
                </TableCell>
                <TableCell sx={{ textAlign: 'center' }}>
                  {player[0].slugging_percentage.toFixed(3).replace(/^0/, '')}
                </TableCell>
                <TableCell sx={{ textAlign: 'center' }}>
                  {player[0].onbase_plus_slugging.toFixed(3).replace(/^0/, '')}
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
