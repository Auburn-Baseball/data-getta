import { BatterStatsTable } from '@/types/db';
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
import { useParams, useNavigate } from 'react-router';

type BattingStatsTableProps = {
  stats: BatterStatsTable | null;
  teamName?: string;
};

export default function BattingStatsTable({ stats }: BattingStatsTableProps) {
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

  // Format stats for display
  const formatStat = (value: number | null | undefined, decimals: number = 3): string => {
    if (value === null || value === undefined) return '.000';
    if (value === 1 && decimals === 3) return value.toFixed(3);
    return value.toFixed(decimals).replace(/^0/, '');
  };

  return (
    <Paper elevation={3} sx={{ paddingX: 2, paddingY: 2, width: '100%', overflowX: 'auto' }}>
      <Divider textAlign="center" sx={{ mb: 2 }}>
        Standard NCAA Batting Stats
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
              {['GP', 'PA', 'AB', 'H', 'HR', 'BB', 'SO', 'HBP', 'AVG', 'OBP', 'SLG', 'OPS'].map(
                (header) => (
                  <TableCell
                    key={header}
                    sx={{ fontWeight: 'bold', textAlign: 'center', width: 50 }}
                  >
                    <Tooltip title={header} arrow>
                      <span>{header}</span>
                    </Tooltip>
                  </TableCell>
                ),
              )}
            </TableRow>
          </TableHead>
          <TableBody>
            {stats ? (
              <TableRow>
                <TableCell sx={{ textAlign: 'center' }}>{stats.games}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{stats.plate_appearances}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{stats.at_bats}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{stats.hits}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{stats.homeruns}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{stats.walks}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{stats.strikeouts}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{stats.hit_by_pitch}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>
                  {formatStat(stats.batting_average)}
                </TableCell>
                <TableCell sx={{ textAlign: 'center' }}>
                  {formatStat(stats.on_base_percentage)}
                </TableCell>
                <TableCell sx={{ textAlign: 'center' }}>
                  {formatStat(stats.slugging_percentage)}
                </TableCell>
                <TableCell sx={{ textAlign: 'center' }}>
                  {formatStat(stats.onbase_plus_slugging)}
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
