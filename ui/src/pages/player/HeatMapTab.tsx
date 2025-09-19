import Box from '@mui/material/Box';
import { supabase } from '@/utils/supabase';
import HeatMap from '@/components/player/HeatMap/HeatMap';
import { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router';
import { CircularProgress, Typography } from '@mui/material';

export type ZoneBin = {
  zoneId: number;            // 1..13 (1..9 inner; 10..13 outer)
  inZone: boolean;           // true for inner
  zoneRow: number;           // 1..3 for inner, 0 outer
  zoneCol: number;           // 1..3 for inner, 0 outer
  zoneCell: number;          // 1..9 for inner, 0 outer
  outerLabel: 'NA' | 'OTL' | 'OTR' | 'OBL' | 'OBR';

  totalPitchCount: number;

  // per-pitch-type counts (match DB column names)
  Count_FourSeam: number;
  Count_Sinker: number;
  Count_Slider: number;
  Count_Curveball: number;
  Count_Changeup: number;
  Count_Cutter: number;
  Count_Splitter: number;
  Count_Other: number;

  // handedness
  Count_L: number;
  Count_R: number;
};

export default function HeatMapTab() {
  const { trackmanAbbreviation, playerName, year } = useParams<{
    trackmanAbbreviation: string;
    playerName: string;
    year: string;
  }>();

  const [searchParams] = useSearchParams();
  const team = trackmanAbbreviation ?? '';
  const decodedPlayerName = playerName ? playerName.replace('_', ', ') : '';

  const [bins, setBins] = useState<ZoneBin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const pitchType = (searchParams.get('pitch') || 'All') as
    | 'All'
    | 'FourSeam'
    | 'Sinker'
    | 'Slider'
    | 'Curveball'
    | 'Changeup'
    | 'Cutter'
    | 'Splitter'
    | 'Other';

  const batter = (searchParams.get('batter') || 'Both') as 'Both' | 'L' | 'R';

  useEffect(() => {
    async function fetchBins() {
      if (!decodedPlayerName || !year || !team) return;
      try {
        setLoading(true);
        setError(null);

        const { data, error } = await supabase
          .from('PitcherPitchBins')
          .select(`
            ZoneId, InZone, ZoneRow, ZoneCol, ZoneCell, OuterLabel,
            TotalPitchCount,
            Count_FourSeam, Count_Sinker, Count_Slider, Count_Curveball, Count_Changeup, Count_Cutter, Count_Splitter, Count_Other,
            Count_L, Count_R
          `)
          .eq('Pitcher', decodedPlayerName)
          .eq('Year', Number(year))
          .eq('PitcherTeam', team);

        if (error) throw error;

        const formatted: ZoneBin[] = (data ?? []).map((r: any) => ({
          zoneId: Number(r.ZoneId),
          inZone: !!r.InZone,
          zoneRow: Number(r.ZoneRow ?? 0),
          zoneCol: Number(r.ZoneCol ?? 0),
          zoneCell: Number(r.ZoneCell ?? 0),
          outerLabel: (r.OuterLabel ?? 'NA') as ZoneBin['outerLabel'],
          totalPitchCount: Number(r.TotalPitchCount) || 0,
          Count_FourSeam: Number(r.Count_FourSeam) || 0,
          Count_Sinker: Number(r.Count_Sinker) || 0,
          Count_Slider: Number(r.Count_Slider) || 0,
          Count_Curveball: Number(r.Count_Curveball) || 0,
          Count_Changeup: Number(r.Count_Changeup) || 0,
          Count_Cutter: Number(r.Count_Cutter) || 0,
          Count_Splitter: Number(r.Count_Splitter) || 0,
          Count_Other: Number(r.Count_Other) || 0,
          Count_L: Number(r.Count_L) || 0,
          Count_R: Number(r.Count_R) || 0,
        }));

        setBins(formatted);
      } catch (e: any) {
        console.error('Error fetching bins:', e);
        setError(e.message || 'Failed to load binned pitch data');
      } finally {
        setLoading(false);
      }
    }

    fetchBins();
  }, [decodedPlayerName, year, team]);

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
    <Box sx={{ width: '100%', display: 'flex', justifyContent: 'center', py: '2rem', minHeight: '100vh' }}>
      <HeatMap
        playerName={decodedPlayerName}
        batterFilter={batter}
        pitchTypeFilter={pitchType}
        bins={bins}
      />
    </Box>
  );
}
