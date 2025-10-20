import { useEffect, useState } from 'react';
import { useParams } from 'react-router';
import Box from '@mui/material/Box';
import { CircularProgress, Typography } from '@mui/material';

import BatterHeatMap from '@/components/player/HeatMap/BatterHeatMap';
import PitcherHeatMap from '@/components/player/HeatMap/PitcherHeatMap';
import { fetchBatterHeatMapBins, fetchPitcherHeatMapBins } from '@/services/playerService';
import type { BatterPitchBinsTable, PitcherPitchBinsTable } from '@/types/db';
import { transformPitcherPitchBins } from '@/transforms/pitcherPitchBinTransform';
import { transformBatterPitchBins } from '@/transforms/batterPitchBinTransform';

type HeatMapTabProps = {
  startDate: string;
  endDate: string;
};

export default function HeatMapTab({ startDate, endDate }: HeatMapTabProps) {
  const { trackmanAbbreviation, playerName } = useParams<{
    trackmanAbbreviation: string;
    playerName: string;
  }>();

  const decodedTrackmanAbbreviation = trackmanAbbreviation
    ? decodeURIComponent(trackmanAbbreviation)
    : '';
  const decodedPlayerName = playerName ? decodeURIComponent(playerName).split('_').join(', ') : '';

  const [pitcherBins, setPitcherBins] = useState<PitcherPitchBinsTable[]>([]);
  const [batterBins, setBatterBins] = useState<BatterPitchBinsTable[]>([]);
  const [pitcherLoading, setPitcherLoading] = useState(true);
  const [batterLoading, setBatterLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchBins() {
      if (!trackmanAbbreviation || !playerName) {
        setPitcherBins([]);
        setPitcherLoading(false);
        return;
      }

      try {
        setPitcherLoading(true);
        setError(null);
        const range = { startDate, endDate };
        const { data, error } = await fetchPitcherHeatMapBins(
          decodedPlayerName,
          decodedTrackmanAbbreviation,
          range,
        );

        if (error) throw error;

        // Transform the data before setting state
        const transformedData = transformPitcherPitchBins(data || []);
        setPitcherBins(transformedData);
      } catch (error: unknown) {
        console.error('Error fetching pitcher bins:', error);
        const message = error instanceof Error ? error.message : null;
        setError(message || 'Failed to load binned pitch data');
      } finally {
        setPitcherLoading(false);
      }
    }

    fetchBins();
  }, [
    decodedPlayerName,
    decodedTrackmanAbbreviation,
    endDate,
    playerName,
    startDate,
    trackmanAbbreviation,
  ]);

  useEffect(() => {
    async function fetchBatterBins() {
      if (!trackmanAbbreviation || !playerName) {
        setBatterBins([]);
        setBatterLoading(false);
        return;
      }

      try {
        setBatterLoading(true);
        const range = { startDate, endDate };
        const { data, error } = await fetchBatterHeatMapBins(
          decodedPlayerName,
          decodedTrackmanAbbreviation,
          range,
        );

        if (error) throw error;

        // Transform the data before setting state
        const transformedData = transformBatterPitchBins(data || []);
        setBatterBins(transformedData);
      } catch (error: unknown) {
        console.error('Error fetching batter bins:', error);
        setError('Failed to load batter heat-map data');
      } finally {
        setBatterLoading(false);
      }
    }

    fetchBatterBins();
  }, [
    decodedPlayerName,
    decodedTrackmanAbbreviation,
    endDate,
    playerName,
    startDate,
    trackmanAbbreviation,
  ]);

  if (!trackmanAbbreviation || !playerName) {
    return (
      <Typography variant="h6" color="#d32f2f" sx={{ py: '2rem' }}>
        <strong>Error!</strong>
      </Typography>
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
            No pitcher heat-map data available between {startDate} and {endDate}.
          </Typography>
          <Typography variant="body1" color="text.secondary">
            No batter heat-map data available between {startDate} and {endDate}.
          </Typography>
        </>
      )}
    </Box>
  );
}
