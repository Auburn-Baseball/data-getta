import { PitcherStatsTable } from '@/types/schemas';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import { MenuItem, Select, FormControl, InputLabel, SelectChangeEvent } from '@mui/material';
import { useState, useEffect } from 'react';
import Divider from '@mui/material/Divider';
import Tooltip from '@mui/material/Tooltip';
import { useNavigate, useParams } from 'react-router';

export default function PitchingStatsTable({
  stats,
  teamName,
}: {
  stats: PitcherStatsTable | null;
  teamName: string;
}) {
  const navigate = useNavigate();
  const params = useParams();

  const teamParam = params.teamName || 'NULL';
  const [selectedDataType, setSelectedDataType] = useState<string>(teamParam);
  const playerName = params.playerName || '';
  const year = params.year || '';

  useEffect(() => {
    const newTeam = params.teamName || 'NULL';
    setSelectedDataType(newTeam);
  }, [params.teamName]);

  const handleNavigation = (newTeamName: string) => {
    if (!newTeamName || !['AUB_TIG', 'AUB_PRC'].includes(newTeamName)) {
      alert('Invalid team selected.');
      return;
    }
    navigate(`/team/${newTeamName}/player/${playerName}/stats/${year}`);
  };

  const handleSelectChange = (event: SelectChangeEvent<string>) => {
    const newValue = event.target.value;
    setSelectedDataType(newValue);
    handleNavigation(newValue);
  };

  return (
    <Paper elevation={3} sx={{ paddingX: 2, paddingY: 2, width: '100%', overflowX: 'auto' }}>
      <Divider textAlign="center" sx={{ mb: 2 }}>
        Standard NCAA Pitching Stats
      </Divider>

      {stats && ['AUB_TIG', 'AUB_PRC'].includes(selectedDataType) && (
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
            {stats ? (
              <TableRow>
                <TableCell sx={{ textAlign: 'center' }}>{stats.total_batters_faced}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{stats.games}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{stats.games_started}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{stats.total_innings_pitched}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{stats.total_walks_pitcher}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{stats.total_strikeouts_pitcher}</TableCell>
              </TableRow>
            ) : (
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
