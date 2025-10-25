import { useEffect, useState } from 'react';
import { useParams } from 'react-router';
import { Typography, Box } from '@mui/material';
import { useLocation } from 'react-router';

import BattingStatsTable from '@/components/player/Batting/BattingStatsTable';
import PitchCountTable from '@/components/player/Pitching/PitchCountTable';
import PitchingStatsTable from '@/components/player/Pitching/PitchingStatsTable';
import StatsTableSkeleton from '@/components/player/StatsTableSkeleton';

import { batterStatsTransform } from '@/transforms/batterStatsTransform';
import { pitchCountsTransform, pitcherStatsTransform } from '@/transforms/pitcherStatsTransforms';

import {
  fetchPlayerBatterStats,
  fetchPlayerPitchCounts,
  fetchPlayerPitcherStats,
} from '@/services/playerService';

import type { BatterStatsTable, PitchCountsTable, PitcherStatsTable } from '@/types/db';

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

        // --- Batting: pass RAW + MODE to transform (prevents duplicates) ---
        const batterResp = await fetchPlayerBatterStats(
          decodedPlayerName,
          decodedTeamName,
          range,
          opt
        );
        if (batterResp.error) throw batterResp.error;

        const battingMode = effectivePractice ? 'practiceOnly' : 'gameOnly' as const;
        const bAgg = batterStatsTransform((batterResp.data ?? []) as BatterStatsTable[], {
          mode: battingMode,
        });
        // If transform ever returns [], show null (not raw rows)
        const bStat = bAgg[0] ?? null;

        // --- Pitcher & PitchCounts: keep simple client filter, then transform ---
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

        const pitcherRows = filterByPractice(pitcherResp.data ?? [], effectivePractice);
        const pitchRows = filterByPractice(pitchResp.data ?? [], effectivePractice);

        const pStat = pitcherRows.length
          ? (pitcherStatsTransform(pitcherRows as PitcherStatsTable[])[0] ??
              (pitcherRows as PitcherStatsTable[])[0] ??
              null)
          : null;

        const pcStat = pitchRows.length
          ? (pitchCountsTransform(pitchRows as PitchCountsTable[])[0] ??
              (pitchRows as PitchCountsTable[])[0] ??
              null)
          : null;

        setBatterStats(bStat);
        setPitcherStats(pStat);
        setPitchCounts(pcStat);
      } catch (e: any) {
        console.error('Error fetching player stats:', e);
        setError(e?.message ?? 'Failed to load stats');
        setBatterStats(null);
        setPitcherStats(null);
        setPitchCounts(null);
      } finally {
        setLoading(false);
      }
    }

    fetchStats();
  }, [decodedPlayerName, decodedTeamName, startDate, endDate, effectivePractice]);

  if (loading) return <StatsTableSkeleton />;

  const hasBatterData = !!batterStats;
  const hasPitcherData = !!pitcherStats;
  const hasPitchCountsData = !!pitchCounts;

  if (!hasBatterData && !hasPitcherData && !hasPitchCountsData) {
    return (
      <Box sx={{ mt: 3 }}>
        <Typography variant="body1">{error ?? 'No stats found for this range.'}</Typography>
      </Box>
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