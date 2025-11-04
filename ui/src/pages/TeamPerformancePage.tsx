import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';

import TeamPercent from '@/components/team/TeamPercent';
import {
  fetchAdvancedBattingStats,
  fetchAdvancedPitchingStats,
} from '@/services/teamPerformanceService';
import { fetchSeasonDateRanges } from '@/services/seasonService';
import {
  transformTeamPerformance,
  TeamPerformanceRow,
} from '@/transforms/teamPerformanceTransform';
import type { DateRange, SeasonDateRange } from '@/types/dateRange';
import { getYearRange } from '@/utils/dateRange';

type TeamPerformancePageProps = {
  dateRange: DateRange;
};

export default function TeamPerformancePage({ dateRange }: TeamPerformancePageProps) {
  const [params] = useSearchParams();
  // Selected season state and available seasons
  const [seasonRanges, setSeasonRanges] = useState<SeasonDateRange[]>([]);
  const [selectedSeason, setSelectedSeason] = useState<number | null>(null);
  // Header shows title; info note uses selectedSeason directly

  const mode = useMemo<'overall' | 'wl'>(() => {
    const m = (params.get('mode') || 'overall').toLowerCase();
    return m === 'wl' ? 'wl' : 'overall';
  }, [params]);

  const [rows, setRows] = useState<TeamPerformanceRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load available seasons from Supabase and choose default selection
  useEffect(() => {
    async function loadSeasons() {
      try {
        const resp = await fetchSeasonDateRanges();
        const ranges = (resp.ranges ?? [])
          .filter((r) => r.year >= 2020)
          .sort((a, b) => a.year - b.year);
        setSeasonRanges(ranges);

        // Default selection: last season within current dateRange, else latest
        const { startYear, endYear } = getYearRange(dateRange);
        const inRange = ranges
          .filter((r) => r.year >= startYear && r.year <= endYear)
          .map((r) => r.year);
        const defaultYear =
          (inRange.length > 0 ? inRange : ranges.map((r) => r.year)).at(-1) ?? null;
        setSelectedSeason(defaultYear);
      } catch (e) {
        console.error('Failed to load season ranges', e);
      }
    }
    loadSeasons();
  }, [dateRange]);

  // Fetch team performance for the selected season only
  useEffect(() => {
    async function fetchStatsForSeason() {
      if (!selectedSeason) return;
      setLoading(true);
      setError(null);
      try {
        const season = seasonRanges.find((r) => r.year === selectedSeason);
        const range: DateRange | null = season
          ? { startDate: season.startDate, endDate: season.endDate }
          : null;
        if (!range) {
          setRows([]);
          setLoading(false);
          return;
        }

        const [
          { data: battingData, error: battingError },
          { data: pitchingData, error: pitchingError },
        ] = await Promise.all([
          fetchAdvancedBattingStats(range),
          fetchAdvancedPitchingStats(range),
        ]);

        if (battingError) throw new Error(`Error fetching batting stats: ${battingError.message}`);
        if (pitchingError)
          throw new Error(`Error fetching pitching stats: ${pitchingError.message}`);

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
    fetchStatsForSeason();
  }, [selectedSeason, seasonRanges]);

  // If mode is W/L (no data yet), pass empty rows to show the empty state
  const rowsToShow = mode === 'wl' ? [] : rows;

  return (
    <Box sx={{ bgcolor: 'white', color: 'black', minHeight: '100vh', px: 4, py: 4 }}>
      <Typography variant="h4" sx={{ mb: 1, color: 'black' }}>
        Team Performance Metrics
      </Typography>
      {/* Removed duplicate date subheader; info + selector below convey season */}

      {/* Info and Season Selector */}
      <Box sx={{ width: '100%', maxWidth: 800, mb: 3 }}>
        <Alert severity="info" sx={{ mb: 2 }}>
          Team performance reflects a single season only. Showing{' '}
          <strong>{selectedSeason ?? '—'}</strong> season data.
        </Alert>
        {seasonRanges.length > 0 && (
          <FormControl size="small" sx={{ minWidth: 160 }}>
            <InputLabel id="team-season-select-label">Season</InputLabel>
            <Select
              labelId="team-season-select-label"
              id="team-season-select"
              label="Season"
              value={selectedSeason ?? ''}
              onChange={(e) => setSelectedSeason(Number(e.target.value))}
            >
              {seasonRanges.map((r) => (
                <MenuItem key={r.year} value={r.year}>
                  {r.year}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}
      </Box>

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
          <TeamPercent rows={rowsToShow} mode={mode} />
        ) : (
          <Typography variant="body1" sx={{ py: 2 }}>
            No team performance data available for the selected season.
          </Typography>
        ))}
    </Box>
  );
}
