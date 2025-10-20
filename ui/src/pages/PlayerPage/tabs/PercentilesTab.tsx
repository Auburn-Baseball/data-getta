import { useEffect, useState } from 'react';
import { useParams } from 'react-router';
import { Box, Typography, CircularProgress } from '@mui/material';

import StatBar from '@/components/player/StatBar';
import InfieldSprayChart from '@/components/player/Charts/InfieldSprayChart';
import { fetchAdvancedBattingStats } from '@/services/playerService';
import type { AdvancedBattingStatsTable } from '@/types/db';
import type { DateRange } from '@/types/dateRange';
import { formatYearRange } from '@/utils/dateRange';

type PercentilesTabProps = {
  dateRange: DateRange;
};

// Define a type for our stat keys to avoid 'any'
type StatKey = keyof AdvancedBattingStatsTable;

// Define our stat display configuration with proper typing
interface StatConfig {
  key: StatKey;
  label: string;
  isPercentage?: boolean;
}

export default function PercentilesTab({ dateRange }: PercentilesTabProps) {
  const { trackmanAbbreviation, playerName } = useParams<{
    trackmanAbbreviation: string;
    playerName: string;
  }>();

  const [stats, setStats] = useState<AdvancedBattingStatsTable | null>(null);
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

        const { data, error } = await fetchAdvancedBattingStats(decodedTeamName, dateRange);

        if (error) {
          console.error('Error fetching player stats:', error);
          setError(`Failed to load stats for ${formattedPlayerName}`);
          setLoading(false);
          return;
        }

        const playerStats = data?.find((entry) => entry.Batter === formattedPlayerName) ?? null;

        if (!playerStats) {
          setError(`No advanced stats found for ${formattedPlayerName} in ${seasonLabel}`);
          setLoading(false);
          return;
        }

        setStats(playerStats);
      } catch (error: unknown) {
        console.error('Error fetching percentile stats:', error);
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

  if (!stats) {
    return (
      <Typography variant="body1" sx={{ textAlign: 'center', py: '4rem' }}>
        No advanced stats data available for this player in {seasonLabel}.
      </Typography>
    );
  }

  // Define the stats we want to display with proper typing
  const statConfigs: StatConfig[] = [
    { key: 'avg_exit_velo', label: 'EV' },
    { key: 'k_per', label: 'K%', isPercentage: true },
    { key: 'bb_per', label: 'BB%', isPercentage: true },
    { key: 'la_sweet_spot_per', label: 'LA Sweet Spot %', isPercentage: true },
    { key: 'hard_hit_per', label: 'Hard Hit %', isPercentage: true },
    { key: 'whiff_per', label: 'Whiff %', isPercentage: true },
    { key: 'chase_per', label: 'Chase %', isPercentage: true },
    { key: 'barrel_per', label: 'Barrel %', isPercentage: true },
    { key: 'xba_per', label: 'xBA', isPercentage: true },
    { key: 'xslg_per', label: 'xSLG', isPercentage: true },
  ];

  return (
    <Box
      sx={{
        display: 'flex',
        width: '100%',
        maxWidth: 1200,
        margin: '40px auto',
        gap: 3,
        flexDirection: { xs: 'column', md: 'row' },
      }}
    >
      {/* Advanced Stats */}
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          mb: { xs: 4, md: 0 },
        }}
      >
        <Box sx={{ width: '100%', maxWidth: 400 }}>
          <Typography variant="h5" sx={{ textAlign: 'center', mb: 3 }}>
            Advanced Stats ({seasonLabel})
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {statConfigs.map((config) => {
              // Get the stat value and skip if undefined
              const statValue = stats[config.key];
              if (statValue === undefined) {
                return null;
              }

              // Get the rank value using explicit key construction
              const rankKey = `${config.key}_rank` as keyof AdvancedBattingStatsTable;
              const rankValue = stats[rankKey];
              const rank = typeof rankValue === 'number' ? Math.round(rankValue) : 50;

              // Format the displayed value
              const displayValue =
                typeof statValue === 'number'
                  ? config.isPercentage
                    ? `${(statValue * 100).toFixed(1)}%`
                    : statValue.toFixed(1)
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
      </Box>

      {/* Infield Spray Chart */}
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Box sx={{ textAlign: 'center', width: '100%' }}>
          <Typography variant="h5" sx={{ mb: 2 }}>
            Infield Spray Chart
          </Typography>
          <InfieldSprayChart stats={stats} />
        </Box>
      </Box>
    </Box>
  );
}
