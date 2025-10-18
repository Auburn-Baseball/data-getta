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
import { cachedQuery, createCacheKey } from '@/utils/supabase/cache';
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

  const [playerStats, setPlayerStats] = useState<BatterStatsTable[]>([]);
  const [advancedStats, setAdvancedStats] = useState<BatterStatsTable[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const teamParam = params.teamName || 'NULL';
  const [selectedDataType, setSelectedDataType] = useState<string>(teamParam);

  const safeYear = year || 2025;
  const formattedPlayerName = playerName?.replace('_', ', ');

  useEffect(() => {
    console.log('BattingStatsTable props:', {
      teamName,
      playerName,
      formattedPlayerName,
      year: safeYear,
    });
  }, [teamName, playerName, formattedPlayerName, safeYear]);

  useEffect(() => {
    async function fetchStats() {
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

        const { data, error } = await cachedQuery({
          key: createCacheKey('BatterStats', {
            select: '*',
            eq: {
              Batter: formattedPlayerName,
              BatterTeam: teamName,
              Year: safeYear,
            },
          }),
          query: () =>
            supabase
              .from('BatterStats')
              .select('*')
              .eq('Batter', formattedPlayerName)
              .eq('BatterTeam', teamName)
              .eq('Year', safeYear)
              .overrideTypes<BatterStatsTable[], { merge: false }>(),
        });

        // if (playerError) throw playerError;
        // setPlayerStats(playerData || []);

        // Advanced stats (copying top table format exactly)
        const { data: advData, error: advError } = await supabase
          .from('AdvancedBattingStats')
          .select('*')
          .eq('Batter', formattedPlayerName)
          .eq('BatterTeam', teamName)
          .eq('Year', safeYear)
          .overrideTypes<BatterStatsTable[], { merge: false }>();

        if (advError) throw advError;
        setAdvancedStats(advData || []);
      } catch (err) {
        console.error('Error fetching stats:', err);
        setError('Failed to load batter stats');
      } finally {
        setLoading(false);
      }
    }

    fetchStats();
  }, [formattedPlayerName, teamName, safeYear]);

  useEffect(() => {
    const newTeam = params.teamName || 'NULL';
    setSelectedDataType(newTeam);
  }, [params.teamName]);

  const safePlayerName = encodeURIComponent(
    playerName || (playerStats.length > 0 ? playerStats[0].Batter : 'unknown-player'),
  );

  const hasPracticePage = playerStats.length > 0;

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
      {/* Standard NCAA Batting Stats Table */}
      <Divider textAlign="center" sx={{ mb: 2 }}>
        Standard NCAA Batting Stats
      </Divider>

      {hasPracticePage && ['AUB_TIG', 'AUB_PRC'].includes(selectedDataType) && (
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
            ) : playerStats.length > 0 ? (
              <TableRow>
                <TableCell sx={{ textAlign: 'center' }}>{playerStats[0].games}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{playerStats[0].plate_appearances}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{playerStats[0].at_bats}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{playerStats[0].hits}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{playerStats[0].homeruns}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{playerStats[0].walks}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{playerStats[0].strikeouts}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{playerStats[0].hit_by_pitch}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>
                  {playerStats[0].batting_average?.toFixed(3).replace(/^0/, '') ?? '.000'}
                </TableCell>
                <TableCell sx={{ textAlign: 'center' }}>
                  {playerStats[0].on_base_percentage?.toFixed(3).replace(/^0/, '') ?? '.000'}
                </TableCell>
                <TableCell sx={{ textAlign: 'center' }}>
                  {playerStats[0].slugging_percentage?.toFixed(3).replace(/^0/, '') ?? '.000'}
                </TableCell>
                <TableCell sx={{ textAlign: 'center' }}>
                  {playerStats[0].onbase_plus_slugging?.toFixed(3).replace(/^0/, '') ?? '.000'}
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
