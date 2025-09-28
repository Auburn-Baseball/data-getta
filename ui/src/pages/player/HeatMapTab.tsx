import Box from '@mui/material/Box';
import { supabase } from '@/utils/supabase/client';
import HeatMap from '@/components/player/HeatMap/HeatMap';
import { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router';
import { CircularProgress, Typography } from '@mui/material';

export type ZoneBin = {
  zoneId: number; // 1..13 (1..9 inner; 10..13 outer)
  inZone: boolean; // true for inner
  zoneRow: number; // 1..3 for inner, 0 outer
  zoneCol: number; // 1..3 for inner, 0 outer
  zoneCell: number; // 1..9 for inner, 0 outer
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

  // handedness split per pitch type
  Count_L_FourSeam: number;
  Count_L_Sinker: number;
  Count_L_Slider: number;
  Count_L_Curveball: number;
  Count_L_Changeup: number;
  Count_L_Cutter: number;
  Count_L_Splitter: number;
  Count_L_Other: number;
  Count_R_FourSeam: number;
  Count_R_Sinker: number;
  Count_R_Slider: number;
  Count_R_Curveball: number;
  Count_R_Changeup: number;
  Count_R_Cutter: number;
  Count_R_Splitter: number;
  Count_R_Other: number;
};

export default function HeatMapTab() {
  const { trackmanAbbreviation, playerName, year } = useParams<{
    trackmanAbbreviation: string;
    playerName: string;
    year: string;
  }>();

  const [searchParams, setSearchParams] = useSearchParams();
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
          .select(
            `
            ZoneId, InZone, ZoneRow, ZoneCol, ZoneCell, OuterLabel,
            TotalPitchCount,
            Count_FourSeam, Count_Sinker, Count_Slider, Count_Curveball, Count_Changeup, Count_Cutter, Count_Splitter, Count_Other,
            Count_L_FourSeam, Count_L_Sinker, Count_L_Slider, Count_L_Curveball, Count_L_Changeup, Count_L_Cutter, Count_L_Splitter, Count_L_Other,
            Count_R_FourSeam, Count_R_Sinker, Count_R_Slider, Count_R_Curveball, Count_R_Changeup, Count_R_Cutter, Count_R_Splitter, Count_R_Other
          `,
          )
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
          Count_L_FourSeam: Number(r.Count_L_FourSeam) || 0,
          Count_L_Sinker: Number(r.Count_L_Sinker) || 0,
          Count_L_Slider: Number(r.Count_L_Slider) || 0,
          Count_L_Curveball: Number(r.Count_L_Curveball) || 0,
          Count_L_Changeup: Number(r.Count_L_Changeup) || 0,
          Count_L_Cutter: Number(r.Count_L_Cutter) || 0,
          Count_L_Splitter: Number(r.Count_L_Splitter) || 0,
          Count_L_Other: Number(r.Count_L_Other) || 0,
          Count_R_FourSeam: Number(r.Count_R_FourSeam) || 0,
          Count_R_Sinker: Number(r.Count_R_Sinker) || 0,
          Count_R_Slider: Number(r.Count_R_Slider) || 0,
          Count_R_Curveball: Number(r.Count_R_Curveball) || 0,
          Count_R_Changeup: Number(r.Count_R_Changeup) || 0,
          Count_R_Cutter: Number(r.Count_R_Cutter) || 0,
          Count_R_Splitter: Number(r.Count_R_Splitter) || 0,
          Count_R_Other: Number(r.Count_R_Other) || 0,
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

  const handleBatterChange = (next: 'Both' | 'L' | 'R') => {
    if (next === batter) return;
    const nextParams = new URLSearchParams(searchParams);
    nextParams.set('batter', next);
    setSearchParams(nextParams);
  };

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
      <HeatMap
        playerName={decodedPlayerName}
        batterFilter={batter}
        pitchTypeFilter={pitchType}
        bins={bins}
        onBatterFilterChange={handleBatterChange}
      />
    </Box>
  );
}
