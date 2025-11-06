import { useEffect, useState } from 'react';
import { useParams, useLocation } from 'react-router';
import {
  Box,
  Typography,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  ToggleButton,
  ToggleButtonGroup,
} from '@mui/material';

import StatBar from '@/components/player/StatBar';
import InfieldSprayChart from '@/components/player/Charts/InfieldSprayChart';
import { fetchAdvancedBattingStats, fetchAdvancedPitchingStats } from '@/services/playerService';
import { fetchSeasonDateRanges } from '@/services/seasonService';
import type { SeasonDateRange } from '@/types/dateRange';
import type { AdvancedBattingStatsTable, AdvancedPitchingStatsTable } from '@/types/db';
import type { DateRange } from '@/types/dateRange';
import { formatYearRange, getYearRange } from '@/utils/dateRange';

type PercentilesTabProps = {
  dateRange: DateRange;
};

type BattingStatKey = keyof AdvancedBattingStatsTable;
type PitchingStatKey = keyof AdvancedPitchingStatsTable;

type RankType = 'Overall' | 'Team';

interface StatConfig<T extends string> {
  key: T;
  label: string;
  isPercentage?: boolean;
}

export default function PercentilesTab({ dateRange }: PercentilesTabProps) {
  const { trackmanAbbreviation, playerName } = useParams<{
    trackmanAbbreviation: string;
    playerName: string;
  }>();
  const location = useLocation();
  const decodedTeam = trackmanAbbreviation ? decodeURIComponent(trackmanAbbreviation) : '';

  const [battingRows, setBattingRows] = useState<AdvancedBattingStatsTable[]>([]);
  const [pitchingRows, setPitchingRows] = useState<AdvancedPitchingStatsTable[]>([]);
  const [seasons, setSeasons] = useState<number[]>([]);
  const [selectedSeason, setSelectedSeason] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rankType, setRankType] = useState<RankType>('Overall');

  const seasonLabel = selectedSeason ? String(selectedSeason) : formatYearRange(dateRange);
  const practice = new URLSearchParams(location.search).get('practice') === 'true';

  useEffect(() => {
    async function fetchStats() {
      if (!trackmanAbbreviation || !playerName) return;
      setLoading(true);
      setError(null);

      try {
        const formattedPlayerName = decodeURIComponent(playerName).replace('_', ', ');
        const decodedTeamName = decodeURIComponent(trackmanAbbreviation);
        const isAuburn = decodedTeamName === 'AUB_TIG';
        
        // Determine which team to fetch from
        // If practice is enabled and it's Auburn, use AUB_PRC for practice data
        const teamToFetch = practice && isAuburn ? 'AUB_PRC' : decodedTeamName;

        // Load tracked seasons from Supabase (same source as SeasonDateRangeSelect)
        const seasonsResp = await fetchSeasonDateRanges();
        const allRanges: SeasonDateRange[] = (seasonsResp.ranges ?? []).filter(
          (r) => r.year >= 2020,
        );

        // Determine a full span covering all tracked seasons to fetch once
        const earliest = allRanges.reduce<string | null>((acc, r) => {
          return !acc || r.startDate < acc ? r.startDate : acc;
        }, null);
        const latest = allRanges.reduce<string | null>((acc, r) => {
          return !acc || r.endDate > acc ? r.endDate : acc;
        }, null);

        // Fallback to provided dateRange if seasons table empty
        const fullRange =
          earliest && latest
            ? { startDate: earliest, endDate: latest }
            : { startDate: dateRange.startDate, endDate: dateRange.endDate };

        const [battingResponse, pitchingResponse] = await Promise.all([
          fetchAdvancedBattingStats(formattedPlayerName, teamToFetch, fullRange),
          fetchAdvancedPitchingStats(formattedPlayerName, teamToFetch, fullRange),
        ]);

        // Only show error if both responses failed (not just missing data)
        if (battingResponse.error && pitchingResponse.error) {
          setError(`Failed to load stats for ${formattedPlayerName}`);
          setLoading(false);
          return;
        }

        const battingData = battingResponse.data ?? [];
        const pitchingData = pitchingResponse.data ?? [];

        setBattingRows(battingData);
        setPitchingRows(pitchingData);

        // Season list from SeasonDates (preferred), else derive from data
        const seasonsFromService = allRanges.map((r) => r.year).sort((a, b) => a - b);
        const derivedYears = Array.from(
          new Set([...battingData.map((r) => r.Year), ...pitchingData.map((r) => r.Year)]),
        ).sort((a, b) => a - b);
        const seasonList = seasonsFromService.length > 0 ? seasonsFromService : derivedYears;
        setSeasons(seasonList);

        // Auto-select: prefer last year within current app dateRange; otherwise latest tracked season
        const { startYear, endYear } = getYearRange(dateRange);
        const inRange = seasonList.filter((y) => y >= startYear && y <= endYear);
        const defaultYear = (inRange.length > 0 ? inRange : seasonList).at(-1) ?? null;
        setSelectedSeason(defaultYear);
      } catch (err: unknown) {
        console.error('Error fetching stats:', err);
        setError('Failed to load player stats');
      } finally {
        setLoading(false);
      }
    }

    fetchStats();
  }, [dateRange, trackmanAbbreviation, playerName, practice]);

  const battingStats: AdvancedBattingStatsTable | null =
    selectedSeason != null ? (battingRows.find((r) => r.Year === selectedSeason) ?? null) : null;

  const pitchingStats: AdvancedPitchingStatsTable | null =
    selectedSeason != null ? (pitchingRows.find((r) => r.Year === selectedSeason) ?? null) : null;

  const getRankColor = (rank: number): string => {
    const r = Math.max(0, Math.min(rank, 100));
    const blueRGB = { r: 0, g: 123, b: 255 };
    const greyRGB = { r: 153, g: 153, b: 153 };
    const t = Math.abs(r - 50) / 50;
    const rVal = Math.round(greyRGB.r + t * (blueRGB.r - greyRGB.r));
    const gVal = Math.round(greyRGB.g + t * (blueRGB.g - greyRGB.g));
    const bVal = Math.round(greyRGB.b + t * (blueRGB.b - greyRGB.b));
    return `rgb(${rVal},${gVal},${bVal})`;
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: '4rem' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Typography variant="h6" color="#d32f2f" sx={{ py: '2rem' }}>
        <strong>Error!</strong>
        <br />
        {error}
      </Typography>
    );
  }

  // Do not early-return on no data; we still show the info + season selector.

  // ---- CONFIGS ----
  const battingConfigs: StatConfig<BattingStatKey>[] = [
    { key: 'xwoba_per', label: 'xwOBA' },
    { key: 'xba_per', label: 'xBA' },
    { key: 'xslg_per', label: 'xSLG' },
    { key: 'avg_exit_velo', label: 'Avg Exit Velo' },
    { key: 'barrel_per', label: 'Barrel %', isPercentage: true },
    { key: 'hard_hit_per', label: 'Hard Hit %', isPercentage: true },
    { key: 'la_sweet_spot_per', label: 'LA Sweet Spot %', isPercentage: true },
    { key: 'chase_per', label: 'Chase %', isPercentage: true },
    { key: 'whiff_per', label: 'Whiff %', isPercentage: true },
    { key: 'k_per', label: 'K %', isPercentage: true },
    { key: 'bb_per', label: 'BB %', isPercentage: true },
  ];

  const pitchingConfigs: StatConfig<PitchingStatKey>[] = [
    { key: 'xwoba_per', label: 'xwOBA' },
    { key: 'xba_per', label: 'xBA' },
    { key: 'xslg_per', label: 'xSLG' },
    { key: 'avg_fastball_velo', label: 'Avg Fastball Velo' },
    { key: 'avg_exit_velo', label: 'Avg Exit Velo' },
    { key: 'chase_per', label: 'Chase %', isPercentage: true },
    { key: 'whiff_per', label: 'Whiff %', isPercentage: true },
    { key: 'k_per', label: 'K %', isPercentage: true },
    { key: 'bb_per', label: 'BB %', isPercentage: true },
    { key: 'barrel_per', label: 'Barrel %', isPercentage: true },
    { key: 'hard_hit_per', label: 'Hard Hit %', isPercentage: true },
    { key: 'gb_per', label: 'GB %', isPercentage: true },
  ];

  const renderStatBars = <
    StatsType extends AdvancedBattingStatsTable | AdvancedPitchingStatsTable,
    KeyType extends keyof StatsType,
  >(
    stats: StatsType,
    configs: StatConfig<KeyType & string>[],
    title: string,
  ) => (
    <Box
      sx={{
        width: '100%',
        maxWidth: 400,
        mx: 'auto',
        mb: 6,
      }}
    >
      <Typography variant="h5" sx={{ textAlign: 'center', mb: 3 }}>
        {title} ({seasonLabel})
      </Typography>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        {configs.map((config) => {
          const value = stats[config.key];
          if (value === undefined) return null;

          const rankSuffix = rankType === 'Team' ? '_rank_team' : '_rank';
          const rankKey = `${config.key}${rankSuffix}` as keyof StatsType;
          const rankValue = stats[rankKey];
          const rank = typeof rankValue === 'number' ? Math.round(rankValue) : 50;

          const displayValue =
            typeof value === 'number'
              ? (() => {
                  switch (config.key) {
                    case 'k_per':
                    case 'bb_per':
                    case 'barrel_per':
                    case 'hard_hit_per':
                    case 'la_sweet_spot_per':
                    case 'chase_per':
                    case 'whiff_per':
                    case 'gb_per':
                      return `${(value * 100).toFixed(1)}%`;

                    case 'xwoba_per':
                    case 'xba_per':
                    case 'xslg_per':
                      return (value as number).toFixed(3);

                    case 'plate_app':
                    case 'fastballs':
                    case 'batted_balls':
                      return (value as number).toFixed(0);

                    default:
                      return (value as number).toFixed(1);
                  }
                })()
              : '0.0';

          return (
            <StatBar
              key={config.key}
              statName={config.label}
              percentile={rank}
              color={getRankColor(rank)}
              statValue={displayValue}
            />
          );
        })}
      </Box>
    </Box>
  );

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column', // Always stacked vertically
        alignItems: 'center',
        width: '100%',
        maxWidth: 1200,
        margin: '40px auto',
      }}
    >
      {/* Rank Type Toggle */}
      <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3, width: '100%' }}>
        <ToggleButtonGroup
          value={rankType}
          exclusive
          onChange={(_event, next: RankType | null) => next && setRankType(next)}
          size="small"
          sx={{ display: 'flex', width: '100%', maxWidth: 300 }}
        >
          <ToggleButton value="Overall" sx={{ flex: 1 }}>
            Overall
          </ToggleButton>
          <ToggleButton value="Team" sx={{ flex: 1 }}>
            Team
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {/* Info and Season Selector */}
      <Box sx={{ width: '100%', maxWidth: 800, mb: 2 }}>
        <Alert severity="info" sx={{ mb: 2 }}>
          Advanced stats reflect a single season only. Showing{' '}
          <strong>{selectedSeason ?? '—'}</strong> season data.
        </Alert>
        {seasons.length > 0 && (
          <FormControl size="small" sx={{ minWidth: 160 }}>
            <InputLabel id="season-select-label">Season</InputLabel>
            <Select
              labelId="season-select-label"
              id="season-select"
              label="Season"
              value={selectedSeason ?? ''}
              onChange={(e) => setSelectedSeason(Number(e.target.value))}
            >
              {seasons.map((y) => (
                <MenuItem key={y} value={y}>
                  {y}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}
      </Box>

      {/* No data message */}
      {!battingStats && !pitchingStats && (
        <Typography variant="body1" sx={{ textAlign: 'center', py: '2rem' }}>
          No percentile data available for the selected season.
        </Typography>
      )}
      {/* Batting Stats + Chart */}
      {battingStats && (
        <Box sx={{ width: '100%', mb: 8 }}>
          {renderStatBars(battingStats, battingConfigs, 'Batting Stats')}
          <Box sx={{ textAlign: 'center', width: '100%', mt: 3 }}>
            <Typography variant="h5" sx={{ mb: 2 }}>
              Infield Spray Chart
            </Typography>
            <InfieldSprayChart stats={battingStats} />
          </Box>
        </Box>
      )}

      {/* Pitching Stats (stacked below, no spray chart) */}
      {pitchingStats ? (
        <Box sx={{ width: '100%', mb: 6 }}>
          {renderStatBars(pitchingStats, pitchingConfigs, 'Pitching Stats')}
        </Box>
      ) : practice ? (
        <Box sx={{ width: '100%', mb: 6, textAlign: 'center' }}>
          <Typography variant="body1" sx={{ py: '2rem' }}>
            No practice pitching stats available for this player.
          </Typography>
        </Box>
      ) : null}
    </Box>
  );
}
