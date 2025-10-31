import { useEffect, useState } from 'react';
import { useParams } from 'react-router';
import { Typography, Box } from '@mui/material';
import { useLocation } from 'react-router';

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

// Treat "practice off" as non-practice (false or null), same as team tabs
function filterByPractice<T extends Record<string, any>>(rows: T[], practice: boolean): T[] {
  if (!Array.isArray(rows)) return [];
  return practice
    ? rows.filter((r) => r?.is_practice === true)
    : rows.filter((r) => r?.is_practice === false || r?.is_practice == null);
}

export default function StatsTab({ startDate, endDate }: StatsTabProps) {
  const { trackmanAbbreviation, playerName } = useParams<{
    trackmanAbbreviation: string;
    playerName: string;
  }>();

  const location = useLocation();
  const practice = new URLSearchParams(location.search).get('practice') === 'true';

  const [batterStats, setBatterStats] = useState<BatterStatsTable | null>(null);
  const [pitcherStats, setPitcherStats] = useState<PitcherStatsTable | null>(null);
  const [pitchCounts, setPitchCounts] = useState<PitchCountsTable | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const decodedPlayerName = playerName ? decodeURIComponent(playerName).split('_').join(', ') : '';
  const decodedTeamName = trackmanAbbreviation ? decodeURIComponent(trackmanAbbreviation) : '';

  const isAuburn = decodedTeamName === 'AUB_TIG';
  const effectivePractice = isAuburn && practice;

  useEffect(() => {
    async function fetchStats() {
      if (!decodedPlayerName || !decodedTeamName || !startDate || !endDate) return;

      try {
        setLoading(true);
        setError(null);

        const range = { startDate, endDate };

        const opt = effectivePractice ? { practice: true } : {};

        // Only pass opt.practice when true; off = undefined (server returns all, so nulls aren't excluded)
        const batterResp = await fetchPlayerBatterStats(
          decodedPlayerName,
          decodedTeamName,
          range,
          opt
        );
        if (batterResp.error) throw batterResp.error;

        const pitcherResp = await fetchPlayerPitcherStats(
          decodedPlayerName,
          decodedTeamName,
          range,
          opt
        );
        if (pitcherResp.error) throw pitcherResp.error;

        const pitchResp = await fetchPlayerPitchCounts(
          decodedPlayerName,
          decodedTeamName,
          range,
          opt
        );
        if (pitchResp.error) throw pitchResp.error;

        // Client-side filter to exactly mimic Team tabs behavior
        const batterRows = filterByPractice(batterResp.data ?? [], practice);
        const pitcherRows = filterByPractice(pitcherResp.data ?? [], practice);
        const pitchRows = filterByPractice(pitchResp.data ?? [], practice);

        // Transforms with safe fallback: if transform returns [], show first raw row
        const transformedBatterStats = batterRows.length
          ? (batterStatsTransform(batterRows)[0] ?? batterRows[0] ?? null)
          : null;

        const transformedPitcherStats = pitcherRows.length
          ? (pitcherStatsTransform(pitcherRows)[0] ?? pitcherRows[0] ?? null)
          : null;

        const transformedPitchCounts = pitchRows.length
          ? (pitchCountsTransform(pitchRows)[0] ?? pitchRows[0] ?? null)
          : null;

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
  }, [decodedPlayerName, decodedTeamName, startDate, endDate, practice]);

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
  );
}
