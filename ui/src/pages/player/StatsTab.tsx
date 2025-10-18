import { supabase } from '@/utils/supabase/client';
import { cachedQuery, createCacheKey } from '@/utils/supabase/cache';
import { BatterStatsTable, PitcherStatsTable, PitchCountsTable } from '@/types/schemas';
import { Typography, Box } from '@mui/material';
import BattingStatsTable from '@/components/player/Batting/BattingStatsTable';
import AdvancedBattingStatsTable from '@/components/player/Batting/AdvancedBattingStatsTable';
import PitchingStatsTable from '@/components/player/Pitching/PitchingStatsTable';
import { useState, useEffect } from 'react';
import StatsTableSkeleton from '@/components/player/StatsTableSkeleton';
import { useParams } from 'react-router';

type StatsTabProps = {
  startDate: string | null;
  endDate: string | null;
};

export default function StatsTab({ startDate, endDate }: StatsTabProps) {
  const { trackmanAbbreviation, playerName, year } = useParams<{
    trackmanAbbreviation: string;
    playerName: string;
    year: string;
  }>();

  const [batter, setBatter] = useState<BatterStatsTable[]>([]);
  const [pitcher, setPitcher] = useState<PitcherStatsTable[]>([]);
  const [pitches, setPitches] = useState<PitchCountsTable[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Parse the player name correctly
  const decodedPlayerName = playerName ? decodeURIComponent(playerName).replace('_', ', ') : '';
  const decodedTeamName = trackmanAbbreviation ? decodeURIComponent(trackmanAbbreviation) : '';
  const safeYear = year || '2025';

  useEffect(() => {
    async function fetchStats() {
      if (!decodedPlayerName || !decodedTeamName) return;

      try {
        setLoading(true);
        setError(null);

        const { data: batterData, error: batterError } = await cachedQuery({
          key: createCacheKey('BatterStats', {
            select: '*',
            eq: {
              Batter: decodedPlayerName,
              BatterTeam: decodedTeamName,
              Year: safeYear,
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
              .eq('Year', safeYear)
              .overrideTypes<BatterStatsTable[], { merge: false }>(),
        });

        if (batterError) throw batterError;

        const { data: pitcherData, error: pitcherError } = await cachedQuery({
          key: createCacheKey('PitcherStats', {
            select: '*',
            eq: {
              Pitcher: decodedPlayerName,
              PitcherTeam: decodedTeamName,
              Year: safeYear,
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
              .eq('Year', safeYear)
              .overrideTypes<PitcherStatsTable[], { merge: false }>(),
        });

        if (pitcherError) throw pitcherError;

        const { data: pitchData, error: pitchError } = await cachedQuery({
          key: createCacheKey('PitchCounts', {
            select: '*',
            eq: {
              Pitcher: decodedPlayerName,
              PitcherTeam: decodedTeamName,
              Year: safeYear,
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
              .eq('Year', safeYear)
              .overrideTypes<PitchCountsTable[], { merge: false }>(),
        });

        if (pitchError) throw pitchError;

        setBatter(batterData || []);
        setPitcher(pitcherData || []);
        setPitches(pitchData || []);
      } catch (err) {
        console.error('Error fetching stats:', err);
        setError('Failed to load player stats');
      } finally {
        setLoading(false);
      }
    }

    fetchStats();
  }, [decodedPlayerName, decodedTeamName, safeYear, startDate, endDate]);

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

  const hasBatterData = batter.length > 0;
  const hasPitcherData = pitcher.length > 0;
  const hasPitchData = pitches.length > 0;

  if (!hasBatterData && !hasPitcherData && !hasPitchData) {
    return (
      <Typography variant="h6" color="#d32f2f">
        <strong>Strikeout!</strong>
        <br />
        No stats found for this player.
      </Typography>
    );
  }

  return (
    <>
      {/* Stats Tables */}
      <Box sx={{ mt: 2, mb: 6 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
          {hasBatterData && (
            <>
              <div>
                <BattingStatsTable
                  teamName={decodedTeamName}
                  playerName={decodedPlayerName}
                  year={safeYear}
                />
              </div>
            </>
          )}
          {hasPitcherData && (
            <div>
              <PitchingStatsTable
                teamName={decodedTeamName}
                playerName={decodedPlayerName}
                year={safeYear}
              />
            </div>
          )}
        </div>
      </Box>
    </>
  );
}
