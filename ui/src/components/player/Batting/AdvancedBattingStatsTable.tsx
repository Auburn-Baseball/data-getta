import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import Divider from '@mui/material/Divider';
import Tooltip from '@mui/material/Tooltip';
import CircularProgress from '@mui/material/CircularProgress';
import { useState, useEffect } from 'react';
import { supabase } from '@/utils/supabase/client';

export interface AdvancedBattingStats {
  avg_exit_velo: number | null;
  k_per: number | null;
  bb_per: number | null;
  Batter: string;
  BatterTeam: string;
  Year: number;
}

export default function AdvancedBattingStatsTable({
  teamName,
  playerName,
  year,
}: {
  teamName: string | undefined;
  playerName: string | undefined;
  year: string | number | undefined;
}) {
  const [stats, setStats] = useState<AdvancedBattingStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const safeYear = typeof year === 'string' ? parseInt(year) : year || 2025;
  const formattedPlayerName = playerName?.replace('_', ', ');

  useEffect(() => {
    async function fetchAdvancedStats() {
      if (!formattedPlayerName || !teamName) {
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        setError(null);
        const { data, error } = await supabase
          .from('AdvancedBattingStats')
          .select('*')
          .eq('Batter', formattedPlayerName)
          .eq('BatterTeam', teamName)
          .eq('Year', safeYear);
        if (error) throw error;
        setStats(data || []);
      } catch (err) {
        setError('Failed to load advanced batting stats');
      } finally {
        setLoading(false);
      }
    }
    fetchAdvancedStats();
  }, [formattedPlayerName, teamName, safeYear]);

  return (
    <Paper elevation={3} sx={{ paddingX: 2, paddingY: 2, width: '100%', overflowX: 'auto' }}>
      <Divider textAlign="center" sx={{ mb: 2 }}>
        Advanced Batting Stats
      </Divider>
      <TableContainer>
        <Table sx={{ minWidth: 400 }} size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center' }}>
                <Tooltip title="Average Exit Velocity" arrow placement="top">
                  <span>EV</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center' }}>
                <Tooltip title="Strikeout Percentage" arrow placement="top">
                  <span>K %</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center' }}>
                <Tooltip title="Walk Percentage" arrow placement="top">
                  <span>BB %</span>
                </Tooltip>
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={3} sx={{ textAlign: 'center', padding: 2 }}>
                  <CircularProgress size={24} />
                </TableCell>
              </TableRow>
            ) : error ? (
              <TableRow>
                <TableCell colSpan={3} sx={{ textAlign: 'center', color: 'error.main' }}>
                  {error}
                </TableCell>
              </TableRow>
            ) : stats.length > 0 ? (
              <TableRow>
                <TableCell sx={{ textAlign: 'center' }}>{stats[0].avg_exit_velo ?? '-'}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{stats[0].k_per !== null ? `${(stats[0].k_per * 100).toFixed(1)}%` : '-'}</TableCell>
                <TableCell sx={{ textAlign: 'center' }}>{stats[0].bb_per !== null ? `${(stats[0].bb_per * 100).toFixed(1)}%` : '-'}</TableCell>
              </TableRow>
            ) : (
              <TableRow>
                <TableCell colSpan={3} sx={{ textAlign: 'center' }}>
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
