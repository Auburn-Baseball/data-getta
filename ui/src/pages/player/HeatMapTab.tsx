import Box from '@mui/material/Box';
import { supabase } from '@/utils/supabase/client';
import HeatMap from '@/components/player/HeatMap/HeatMap';
import BatterHeatMap, { BatterZoneSummary } from '@/components/player/HeatMap/BatterHeatMap';
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
  const [batterBins, setBatterBins] = useState<BatterZoneSummary[]>([]);
  const [pitcherLoading, setPitcherLoading] = useState(true);
  const [batterLoading, setBatterLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [batterError, setBatterError] = useState<string | null>(null);

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
      if (!decodedPlayerName || !year || !team) {
        setPitcherLoading(false);
        return;
      }
      try {
        setPitcherLoading(true);
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
        setPitcherLoading(false);
      }
    }

    fetchBins();
  }, [decodedPlayerName, year, team]);

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

  useEffect(() => {
    async function fetchBatterBins() {
      if (!decodedPlayerName || !year || !team) {
        setBatterLoading(false);
        return;
      }
      try {
        setBatterLoading(true);
        setBatterError(null);

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
          .eq('Batter', decodedPlayerName)
          .eq('Year', Number(year))
          .eq('BatterTeam', team);

        if (error) throw error;

        const formatted: BatterZoneSummary[] = (data ?? []).map((row: any) => ({
          zoneId: Number(row.ZoneId),
          inZone: !!row.InZone,
          zoneRow: Number(row.ZoneRow ?? 0),
          zoneCol: Number(row.ZoneCol ?? 0),
          zoneCell: Number(row.ZoneCell ?? 0),
          outerLabel: (row.OuterLabel ?? 'NA') as BatterZoneSummary['outerLabel'],
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

        setBatterBins(formatted);
      } catch (e: any) {
        console.error('Error fetching batter bins:', e);
        setBatterError(e.message || 'Failed to load batter pitch data');
      } finally {
        setBatterLoading(false);
      }
    }

    fetchBatterBins();
  }, [decodedPlayerName, year, team]);

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
      {!!bins.length && (
        <HeatMap
          playerName={decodedPlayerName}
          batterFilter={batter}
          pitchTypeFilter={pitchType}
          bins={bins}
          onBatterFilterChange={handleBatterChange}
        />
      )}
      {!bins.length && (
        <Typography variant="body1" color="text.secondary">
          No pitcher heat-map data available.
        </Typography>
      )}

      {!!batterBins.length && (
        <BatterHeatMap
          batterName={decodedPlayerName}
          pitchTypeFilter={pitchType}
          bins={batterBins}
        />
      )}
      {!batterBins.length && (
        <Typography variant="body1" color="text.secondary">
          No batter heat-map data available.
        </Typography>
      )}

      {batterError && (
        <Typography variant="body2" color="#d32f2f">
          {batterError}
        </Typography>
      )}
    </Box>
  );
}
