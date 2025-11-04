import { useEffect, useState } from 'react';
import { useParams } from 'react-router';
import { Box, Typography, CircularProgress } from '@mui/material';

import StatBar from '@/components/player/StatBar';
import InfieldSprayChart from '@/components/player/Charts/InfieldSprayChart';
import { fetchAdvancedBattingStats, fetchAdvancedPitchingStats } from '@/services/playerService';
import type { AdvancedBattingStatsTable, AdvancedPitchingStatsTable } from '@/types/db';
import type { DateRange } from '@/types/dateRange';
import { formatYearRange } from '@/utils/dateRange';

type PercentilesTabProps = {
  dateRange: DateRange;
};

type BattingStatKey = keyof AdvancedBattingStatsTable;
type PitchingStatKey = keyof AdvancedPitchingStatsTable;

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

  const [battingStats, setBattingStats] = useState<AdvancedBattingStatsTable | null>(null);
  const [pitchingStats, setPitchingStats] = useState<AdvancedPitchingStatsTable | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const seasonLabel = formatYearRange(dateRange);

  useEffect(() => {
    async function fetchStats() {
      if (!trackmanAbbreviation || !playerName) return;
      setLoading(true);
      setError(null);

      try {
        const formattedPlayerName = decodeURIComponent(playerName).replace('_', ', ');
        const decodedTeamName = decodeURIComponent(trackmanAbbreviation);

        const [battingResponse, pitchingResponse] = await Promise.all([
          fetchAdvancedBattingStats(formattedPlayerName, decodedTeamName, dateRange),
          fetchAdvancedPitchingStats(formattedPlayerName, decodedTeamName, dateRange),
        ]);

        if (battingResponse.error && pitchingResponse.error) {
          setError(`Failed to load stats for ${formattedPlayerName}`);
          setLoading(false);
          return;
        }

        const battingData =
          battingResponse.data?.find((entry) => entry.Batter === formattedPlayerName) ?? null;
        const pitchingData =
          pitchingResponse.data?.find((entry) => entry.Pitcher === formattedPlayerName) ?? null;

        setBattingStats(battingData);
        setPitchingStats(pitchingData);
      } catch (err: unknown) {
        console.error('Error fetching stats:', err);
        setError('Failed to load player stats');
      } finally {
        setLoading(false);
      }
    }

    fetchStats();
  }, [dateRange, trackmanAbbreviation, playerName, seasonLabel]);

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

  if (!battingStats && !pitchingStats) {
    return (
      <Typography variant="body1" sx={{ textAlign: 'center', py: '4rem' }}>
        0
      </Typography>
    );
  }

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

          const rankKey = `${config.key}_rank` as keyof StatsType;
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
      {pitchingStats && (
        <Box sx={{ width: '100%', mb: 6 }}>
          {renderStatBars(pitchingStats, pitchingConfigs, 'Pitching Stats')}
        </Box>
      )}
    </Box>
  );
}
