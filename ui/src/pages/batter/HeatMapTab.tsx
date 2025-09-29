import Box from '@mui/material/Box';
import { CircularProgress, Typography } from '@mui/material';
import { useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'react-router';

import BatterHeatMap from '@/components/player/HeatMap/BatterHeatMap';
import { supabase } from '@/utils/supabase/client';
import { PitchType } from '@/types/types';

export type BatterZoneBin = {
  zoneId: number;
  inZone: boolean;
  zoneRow: number;
  zoneCol: number;
  zoneCell: number;
  outerLabel: 'NA' | 'OTL' | 'OTR' | 'OBL' | 'OBR';
  totalPitchCount: number;
  totalSwingCount: number;
  totalHitCount: number;
  Count_FourSeam: number;
  Count_Sinker: number;
  Count_Slider: number;
  Count_Curveball: number;
  Count_Changeup: number;
  Count_Cutter: number;
  Count_Splitter: number;
  Count_Other: number;
  SwingCount_FourSeam: number;
  SwingCount_Sinker: number;
  SwingCount_Slider: number;
  SwingCount_Curveball: number;
  SwingCount_Changeup: number;
  SwingCount_Cutter: number;
  SwingCount_Splitter: number;
  SwingCount_Other: number;
  HitCount_FourSeam: number;
  HitCount_Sinker: number;
  HitCount_Slider: number;
  HitCount_Curveball: number;
  HitCount_Changeup: number;
  HitCount_Cutter: number;
  HitCount_Splitter: number;
  HitCount_Other: number;
};

export default function BatterHeatMapTab() {
  const { batterName, batterTeam, year } = useParams<{
    batterName: string;
    batterTeam: string;
    year: string;
  }>();

  const [searchParams, setSearchParams] = useSearchParams();

  const decodedTeam = batterTeam ? decodeURIComponent(batterTeam) : '';
  const decodedBatterName = batterName
    ? decodeURIComponent(batterName).replace('_', ', ').replace(/_/g, ' ')
    : '';

  const [bins, setBins] = useState<BatterZoneBin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const pitchType = (searchParams.get('pitch') || 'All') as PitchType;

  useEffect(() => {
    async function fetchBins() {
      if (!decodedBatterName || !decodedTeam || !year) return;
      try {
        setLoading(true);
        setError(null);

        const { data, error } = await supabase
          .from('BatterPitchBins')
          .select(
            `
            ZoneId, InZone, ZoneRow, ZoneCol, ZoneCell, OuterLabel,
            TotalPitchCount, TotalSwingCount, TotalHitCount,
            Count_FourSeam, Count_Sinker, Count_Slider, Count_Curveball, Count_Changeup, Count_Cutter, Count_Splitter, Count_Other,
            SwingCount_FourSeam, SwingCount_Sinker, SwingCount_Slider, SwingCount_Curveball, SwingCount_Changeup, SwingCount_Cutter, SwingCount_Splitter, SwingCount_Other,
            HitCount_FourSeam, HitCount_Sinker, HitCount_Slider, HitCount_Curveball, HitCount_Changeup, HitCount_Cutter, HitCount_Splitter, HitCount_Other
          `,
          )
          .eq('Batter', decodedBatterName)
          .eq('Year', Number(year))
          .eq('BatterTeam', decodedTeam);

        if (error) throw error;

        const formatted: BatterZoneBin[] = (data ?? []).map((row: any) => ({
          zoneId: Number(row.ZoneId),
          inZone: !!row.InZone,
          zoneRow: Number(row.ZoneRow ?? 0),
          zoneCol: Number(row.ZoneCol ?? 0),
          zoneCell: Number(row.ZoneCell ?? 0),
          outerLabel: (row.OuterLabel ?? 'NA') as BatterZoneBin['outerLabel'],
          totalPitchCount: Number(row.TotalPitchCount) || 0,
          totalSwingCount: Number(row.TotalSwingCount) || 0,
          totalHitCount: Number(row.TotalHitCount) || 0,
          Count_FourSeam: Number(row.Count_FourSeam) || 0,
          Count_Sinker: Number(row.Count_Sinker) || 0,
          Count_Slider: Number(row.Count_Slider) || 0,
          Count_Curveball: Number(row.Count_Curveball) || 0,
          Count_Changeup: Number(row.Count_Changeup) || 0,
          Count_Cutter: Number(row.Count_Cutter) || 0,
          Count_Splitter: Number(row.Count_Splitter) || 0,
          Count_Other: Number(row.Count_Other) || 0,
          SwingCount_FourSeam: Number(row.SwingCount_FourSeam) || 0,
          SwingCount_Sinker: Number(row.SwingCount_Sinker) || 0,
          SwingCount_Slider: Number(row.SwingCount_Slider) || 0,
          SwingCount_Curveball: Number(row.SwingCount_Curveball) || 0,
          SwingCount_Changeup: Number(row.SwingCount_Changeup) || 0,
          SwingCount_Cutter: Number(row.SwingCount_Cutter) || 0,
          SwingCount_Splitter: Number(row.SwingCount_Splitter) || 0,
          SwingCount_Other: Number(row.SwingCount_Other) || 0,
          HitCount_FourSeam: Number(row.HitCount_FourSeam) || 0,
          HitCount_Sinker: Number(row.HitCount_Sinker) || 0,
          HitCount_Slider: Number(row.HitCount_Slider) || 0,
          HitCount_Curveball: Number(row.HitCount_Curveball) || 0,
          HitCount_Changeup: Number(row.HitCount_Changeup) || 0,
          HitCount_Cutter: Number(row.HitCount_Cutter) || 0,
          HitCount_Splitter: Number(row.HitCount_Splitter) || 0,
          HitCount_Other: Number(row.HitCount_Other) || 0,
        }));

        setBins(formatted);
      } catch (e: any) {
        console.error('Error fetching batter bins:', e);
        setError(e.message || 'Failed to load batter pitch bins');
      } finally {
        setLoading(false);
      }
    }

    fetchBins();
  }, [decodedBatterName, decodedTeam, year]);

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

  return (
    <Box
      sx={{
        width: '100%',
        display: 'flex',
        justifyContent: 'center',
        py: '2rem',
        minHeight: '100vh',
      }}
    >
      <BatterHeatMap batterName={decodedBatterName} pitchTypeFilter={pitchType} bins={bins} />
    </Box>
  );
}
