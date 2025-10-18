import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';

import TeamPercent from '@/components/team/TeamPercent';
import {
  fetchAdvancedBattingStatsByYear,
  fetchAdvancedPitchingStatsByYear,
} from '@/services/teamPerformanceService';
import {
  transformTeamPerformance,
  TeamPerformanceRow,
} from '@/transforms/teamPerformanceTransform';

type TeamPerformancePageProps = {
  year: number;
};

export default function TeamPerformancePage({ year }: TeamPerformancePageProps) {
  const [params] = useSearchParams();

  // Extract year from date for filtering and display purposes
  const safeYear = useMemo(() => year || new Date().getFullYear(), [year]);

  const mode = useMemo<'overall' | 'wl'>(() => {
    const m = (params.get('mode') || 'overall').toLowerCase();
    return m === 'wl' ? 'wl' : 'overall';
  }, [params]);

  const [rows, setRows] = useState<TeamPerformanceRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchStats() {
      setLoading(true);
      setError(null);

      try {
        // Fetch batting stats for the specific year
        const { data: battingData, error: battingError } =
          await fetchAdvancedBattingStatsByYear(safeYear);

        if (battingError) {
          throw new Error(`Error fetching batting stats: ${battingError.message}`);
        }

        // Fetch pitching stats for the specific year
        const { data: pitchingData, error: pitchingError } =
          await fetchAdvancedPitchingStatsByYear(safeYear);

        if (pitchingError) {
          throw new Error(`Error fetching pitching stats: ${pitchingError.message}`);
        }

        // Transform data into the format expected by TeamPercent
        const performanceRows = transformTeamPerformance(battingData || [], pitchingData || []);

        setRows(performanceRows);
      } catch (error: unknown) {
        console.error('Error in team performance:', error);
        const message = error instanceof Error ? error.message : null;
        setError(message || 'An error occurred while fetching team performance data');
      } finally {
        setLoading(false);
      }
    }

    fetchStats();
  }, [safeYear]);

  // If mode is W/L (no data yet), pass empty rows to show the empty state
  const rowsToShow = mode === 'wl' ? [] : rows;

  return (
    <Box sx={{ bgcolor: 'white', color: 'black', minHeight: '100vh', px: 4, py: 4 }}>
      <Typography variant="h4" sx={{ mb: 1, color: 'black' }}>
        Team Performance Metrics
      </Typography>
      <Typography variant="subtitle1" sx={{ mb: 3, color: 'text.secondary' }}>
        {safeYear} Season
      </Typography>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: '4rem' }}>
          <CircularProgress />
        </Box>
      )}

      {error && (
        <Typography variant="body1" sx={{ color: 'error.main', py: 2 }}>
          Error: {error}
        </Typography>
      )}

      {!loading &&
        !error &&
        (rows.length > 0 ? (
          <TeamPercent year={safeYear.toString()} rows={rowsToShow} mode={mode} />
        ) : (
          <Typography variant="body1" sx={{ py: 2 }}>
            No team performance data available for {safeYear}
          </Typography>
        ))}
    </Box>
  );
}
