import { supabase } from '@/utils/supabase/client';
import { cachedQuery, createCacheKey } from '@/utils/supabase/cache';
import { BatterStatsTable, PitcherStatsTable, PitchCountsTable } from '@/types/schemas';
import { Typography, Box } from '@mui/material';
import BattingStatsTable from '@/components/player/Batting/BattingStatsTable';
import PitchingStatsTable from '@/components/player/Pitching/PitchingStatsTable';
import PitchCountTable from '@/components/player/Pitching/PitchCountTable';
import { useState, useEffect } from 'react';
import StatsTableSkeleton from '@/components/player/StatsTableSkeleton';
import { useParams } from 'react-router';
import { batterStatsTransform } from '@/transforms/batterStatsTransform';
import { pitcherStatsTransform, pitchCountsTransform } from '@/transforms/pitcherStatsTransforms';

type StatsTabProps = {
  startDate: string;
  endDate: string;
};

export default function StatsTab({ startDate, endDate }: StatsTabProps) {
  const { trackmanAbbreviation, playerName, year } = useParams<{
    trackmanAbbreviation: string;
    playerName: string;
    year: string;
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

        console.log(`Fetching stats for ${decodedPlayerName} from ${startDate} to ${endDate}`);

        // Fetch batting stats
        const { data: batterData, error: batterError } = await cachedQuery({
          key: createCacheKey('BatterStats', {
            select: '*',
            eq: {
              Batter: decodedPlayerName,
              BatterTeam: decodedTeamName,
            },
            range: {
              startDate,
              endDate,
            },
          }),
          query: () =>
            supabase
              .from('BatterStats')
              .select('*')
              .eq('Batter', decodedPlayerName)
              .eq('BatterTeam', decodedTeamName)
              .gte('Date', startDate)
              .lte('Date', endDate)
              .overrideTypes<BatterStatsTable[], { merge: false }>(),
        });

        if (batterError) throw batterError;

        // Fetch pitching stats
        const { data: pitcherData, error: pitcherError } = await cachedQuery({
          key: createCacheKey('PitcherStats', {
            select: '*',
            eq: {
              Pitcher: decodedPlayerName,
              PitcherTeam: decodedTeamName,
            },
            range: {
              startDate,
              endDate,
            },
          }),
          query: () =>
            supabase
              .from('PitcherStats')
              .select('*')
              .eq('Pitcher', decodedPlayerName)
              .eq('PitcherTeam', decodedTeamName)
              .gte('Date', startDate)
              .lte('Date', endDate)
              .overrideTypes<PitcherStatsTable[], { merge: false }>(),
        });

        if (pitcherError) throw pitcherError;

        // Fetch pitch count data
        const { data: pitchData, error: pitchError } = await cachedQuery({
          key: createCacheKey('PitchCounts', {
            select: '*',
            eq: {
              Pitcher: decodedPlayerName,
              PitcherTeam: decodedTeamName,
            },
            range: {
              startDate,
              endDate,
            },
          }),
          query: () =>
            supabase
              .from('PitchCounts')
              .select('*')
              .eq('Pitcher', decodedPlayerName)
              .eq('PitcherTeam', decodedTeamName)
              .gte('Date', startDate)
              .lte('Date', endDate)
              .overrideTypes<PitchCountsTable[], { merge: false }>(),
        });

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
              <BattingStatsTable stats={batterStats} teamName={decodedTeamName} />
            </div>
          )}
          {hasPitcherData && (
            <div>
              <PitchingStatsTable stats={pitcherStats} teamName={decodedTeamName} />
            </div>
          )}
          {hasPitchCountsData && (
            <div>
              <PitchCountTable stats={pitchCounts} teamName={decodedTeamName} />
            </div>
          )}
        </div>
      </Box>
    </>
  );
}
