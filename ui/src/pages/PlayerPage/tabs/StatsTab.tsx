import { useEffect, useState } from 'react';
import { useParams } from 'react-router';
import { Typography, Box } from '@mui/material';

import BattingStatsTable from '@/components/player/Batting/BattingStatsTable';
import PitchCountTable from '@/components/player/Pitching/PitchCountTable';
import PitchingStatsTable from '@/components/player/Pitching/PitchingStatsTable';
import StatsTableSkeleton from '@/components/player/StatsTableSkeleton';
import {
  fetchPlayerBatterStats,
  fetchPlayerPitchCounts,
  fetchPlayerPitcherStats,
} from '@/services/playerService';
import type { BatterStatsTable, PitchCountsTable, PitcherStatsTable } from '@/types/db';
import { batterStatsTransform } from '@/transforms/batterStatsTransform';
import { pitcherStatsTransform, pitchCountsTransform } from '@/transforms/pitcherStatsTransforms';

type StatsTabProps = {
  startDate: string;
  endDate: string;
};

export default function StatsTab({ startDate, endDate }: StatsTabProps) {
  const { trackmanAbbreviation, playerName } = useParams<{
    trackmanAbbreviation: string;
    playerName: string;
  }>();

  const [batterStats, setBatterStats] = useState<BatterStatsTable | null>(null);
  const [pitcherStats, setPitcherStats] = useState<PitcherStatsTable | null>(null);
  const [pitchCounts, setPitchCounts] = useState<PitchCountsTable | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const decodedPlayerName = playerName ? decodeURIComponent(playerName).replace('_', ', ') : '';
  const decodedTeamName = trackmanAbbreviation ? decodeURIComponent(trackmanAbbreviation) : '';

  useEffect(() => {
    async function fetchStats() {
      if (!decodedPlayerName || !decodedTeamName || !startDate || !endDate) return;

      try {
        setLoading(true);
        setError(null);

        // Fetch batting stats
        const { data: batterData, error: batterError } = await fetchPlayerBatterStats(
          decodedPlayerName,
          decodedTeamName,
          startDate,
          endDate,
        );

        if (batterError) throw batterError;

        // Fetch pitching stats
        const { data: pitcherData, error: pitcherError } = await fetchPlayerPitcherStats(
          decodedPlayerName,
          decodedTeamName,
          startDate,
          endDate,
        );

        if (pitcherError) throw pitcherError;

        // Fetch pitch count data
        const { data: pitchData, error: pitchError } = await fetchPlayerPitchCounts(
          decodedPlayerName,
          decodedTeamName,
          startDate,
          endDate,
        );

        if (pitchError) throw pitchError;

        // Transform data using the appropriate transforms
        const transformedBatterStats = batterData?.length
          ? (batterStatsTransform(batterData)[0] ?? null)
          : null;

        const transformedPitcherStats = pitcherData?.length
          ? (pitcherStatsTransform(pitcherData)[0] ?? null)
          : null;

        const transformedPitchCounts = pitchData?.length
          ? (pitchCountsTransform(pitchData)[0] ?? null)
          : null;

        // Set state with transformed data
        setBatterStats(transformedBatterStats);
        setPitcherStats(transformedPitcherStats);
        setPitchCounts(transformedPitchCounts);
      } catch (err) {
        console.error('Error fetching stats:', err);
        setError('Failed to load player stats');
      } finally {
        setLoading(false);
      }
    }

    fetchStats();
  }, [decodedPlayerName, decodedTeamName, startDate, endDate]);

  if (loading) return <StatsTableSkeleton />;

  if (error) {
    return (
      <Typography variant="h6" color="#d32f2f">
        <strong>Error!</strong>
        <br />
        {error}
      </Typography>
    );
  }

  const hasBatterData = !!batterStats;
  const hasPitcherData = !!pitcherStats;
  const hasPitchCountsData = !!pitchCounts;

  if (!hasBatterData && !hasPitcherData && !hasPitchCountsData) {
    return (
      <Typography variant="h6" color="#d32f2f">
        <strong>Strikeout!</strong>
        <br />
        No stats found for this player between {startDate} and {endDate}.
      </Typography>
    );
  }

  return (
    <>
      <Box sx={{ mt: 2, mb: 6 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
          {hasBatterData && (
            <div>
              <BattingStatsTable stats={batterStats} />
            </div>
          )}
          {hasPitcherData && (
            <div>
              <PitchingStatsTable stats={pitcherStats} />
            </div>
          )}
          {hasPitchCountsData && (
            <div>
              <PitchCountTable stats={pitchCounts} />
            </div>
          )}
        </div>
      </Box>
    </>
  );
}
