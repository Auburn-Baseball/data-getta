import Box from '@mui/material/Box';
import { supabase } from '@/utils/supabase/client';
import { cachedQuery, createCacheKey } from '@/utils/supabase/cache';
import PitcherHeatMap from '@/components/player/HeatMap/PitcherHeatMap';
import BatterHeatMap from '@/components/player/HeatMap/BatterHeatMap';
import { useState, useEffect } from 'react';
import { useParams } from 'react-router';
import { CircularProgress, Typography } from '@mui/material';
import { PitcherPitchBinsTable, BatterPitchBinsTable } from '@/types/schemas';

type HeatMapTabProps = {
  startDate: string | null;
  endDate: string | null;
};

export default function HeatMapTab({ startDate, endDate }: HeatMapTabProps) {
  const { trackmanAbbreviation, playerName, year } = useParams<{
    trackmanAbbreviation: string;
    playerName: string;
    year: string;
  }>();

  if (!trackmanAbbreviation || !playerName || !year) {
    return (
      <Typography variant="h6" color="#d32f2f" sx={{ py: '2rem' }}>
        <strong>Error!</strong>
      </Typography>
    );
  }

  const decodedTrackmanAbbreviation = decodeURIComponent(trackmanAbbreviation);
  const decodedPlayerName = decodeURIComponent(playerName).split('_').join(', ');

  const [pitcherBins, setPitcherBins] = useState<PitcherPitchBinsTable[]>([]);
  const [batterBins, setBatterBins] = useState<BatterPitchBinsTable[]>([]);
  const [pitcherLoading, setPitcherLoading] = useState(true);
  const [batterLoading, setBatterLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchBins() {
      try {
        setPitcherLoading(true);
        setError(null);
        const pitcherSelect = `
            ZoneId, InZone, ZoneRow, ZoneCol, ZoneCell, OuterLabel,
            TotalPitchCount,
            Count_FourSeam, Count_Sinker, Count_Slider, Count_Curveball, Count_Changeup, Count_Cutter, Count_Splitter, Count_Other,
            Count_L_FourSeam, Count_L_Sinker, Count_L_Slider, Count_L_Curveball, Count_L_Changeup, Count_L_Cutter, Count_L_Splitter, Count_L_Other,
            Count_R_FourSeam, Count_R_Sinker, Count_R_Slider, Count_R_Curveball, Count_R_Changeup, Count_R_Cutter, Count_R_Splitter, Count_R_Other
          `.trim();
        const { data, error } = await cachedQuery({
          key: createCacheKey('PitcherPitchBins', {
            select: pitcherSelect,
            eq: {
              Pitcher: decodedPlayerName,
              Year: Number(year),
              PitcherTeam: decodedTrackmanAbbreviation,
            },
            range: {
              startDate,
              endDate,
            },
          }),
          query: () =>
            supabase
              .from('PitcherPitchBins')
              .select(pitcherSelect)
              .eq('Pitcher', decodedPlayerName)
              .eq('Year', Number(year))
              .eq('PitcherTeam', decodedTrackmanAbbreviation)
              .overrideTypes<PitcherPitchBinsTable[], { merge: false }>(),
        });

        if (error) throw error;
        setPitcherBins(data);
      } catch (e: any) {
        console.error('Error fetching bins:', e);
        setError(e.message || 'Failed to load binned pitch data');
      } finally {
        setPitcherLoading(false);
      }
    }

    fetchBins();
  }, [decodedPlayerName, year, decodedTrackmanAbbreviation, startDate, endDate]);

  if (error) {
    return (
      <Typography variant="h6" color="#d32f2f" sx={{ py: '2rem' }}>
        <strong>Error!</strong>
        <br />
        {error}
      </Typography>
    );
  }

  useEffect(() => {
    async function fetchBatterBins() {
      try {
        setBatterLoading(true);
        const batterSelect = `
            ZoneId, InZone, ZoneRow, ZoneCol, ZoneCell, OuterLabel,
            TotalPitchCount, TotalSwingCount, TotalHitCount,
            Count_FourSeam, Count_Sinker, Count_Slider, Count_Curveball, Count_Changeup, Count_Cutter, Count_Splitter, Count_Other,
            SwingCount_FourSeam, SwingCount_Sinker, SwingCount_Slider, SwingCount_Curveball, SwingCount_Changeup, SwingCount_Cutter, SwingCount_Splitter, SwingCount_Other,
            HitCount_FourSeam, HitCount_Sinker, HitCount_Slider, HitCount_Curveball, HitCount_Changeup, HitCount_Cutter, HitCount_Splitter, HitCount_Other
          `.trim();
        const { data, error } = await cachedQuery({
          key: createCacheKey('BatterPitchBins', {
            select: batterSelect,
            eq: {
              Batter: decodedPlayerName,
              Year: Number(year),
              BatterTeam: decodedTrackmanAbbreviation,
            },
            range: {
              startDate,
              endDate,
            },
          }),
          query: () =>
            supabase
              .from('BatterPitchBins')
              .select(batterSelect)
              .eq('Batter', decodedPlayerName)
              .eq('Year', Number(year))
              .eq('BatterTeam', decodedTrackmanAbbreviation)
              .overrideTypes<BatterPitchBinsTable[], { merge: false }>(),
        });

        if (error) throw error;
        setBatterBins(data);
      } catch (e: any) {
        console.error('Error fetching batter bins:', e);
      } finally {
        setBatterLoading(false);
      }
    }

    fetchBatterBins();
  }, [decodedPlayerName, year, decodedTrackmanAbbreviation, startDate, endDate]);

  if (pitcherLoading || batterLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: '4rem' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box
      sx={{
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        py: '2rem',
        minHeight: '100vh',
        gap: 3,
      }}
    >
      {!!pitcherBins.length && <PitcherHeatMap data={pitcherBins} />}
      {!!batterBins.length && <BatterHeatMap data={batterBins} />}

      {!pitcherBins.length && !batterBins.length && (
        <>
          <Typography variant="body1" color="text.secondary">
            No pitcher heat-map data available.
          </Typography>
          <Typography variant="body1" color="text.secondary">
            No batter heat-map data available.
          </Typography>
        </>
      )}
    </Box>
  );
}
