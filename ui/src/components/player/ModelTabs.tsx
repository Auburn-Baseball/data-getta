import Box from '@mui/material/Box';
import Link from '@/utils/Link';
import { useLocation } from 'react-router';
import { useState, useEffect } from 'react';

export default function ModelTabs({ team, player }: { team: string; player: string }) {
  const baseURL = `/team/${team}/player/${player}`;

  const location = useLocation();
  const pathName = location.pathname;

  const [statsUnderline, setStatsUnderline] = useState<'none' | 'hover' | 'always'>('hover');
  const [heatMapUnderline, setHeatMapUnderline] = useState<'none' | 'hover' | 'always'>('hover');
  const [percentilesUnderline, setPercentilesUnderline] = useState<'none' | 'hover' | 'always'>(
    'hover',
  );

  useEffect(() => {
    setStatsUnderline('hover');
    setHeatMapUnderline('hover');
    setPercentilesUnderline('hover');

    if (pathName.includes('/stats')) {
      setStatsUnderline('always');
    } else if (pathName.includes('/heat-map')) {
      setHeatMapUnderline('always');
    } else if (pathName.includes('/percentiles')) {
      setPercentilesUnderline('always');
    }
  }, [pathName]);

  return (
    <Box
      sx={{
        display: 'flex',
        gap: 2,
        flexWrap: 'wrap',
      }}
    >
      <Link
        href={`${baseURL}/stats/2025`}
        name="Stats"
        fontWeight={600}
        underline={statsUnderline}
      />
      <Link
        href={`${baseURL}/heat-map/2025`}
        name="Heat Maps"
        fontWeight={600}
        underline={heatMapUnderline}
      />
      <Link
        href={`${baseURL}/percentiles/2025`}
        name="Percentiles"
        fontWeight={600}
        underline={percentilesUnderline}
      />
    </Box>
  );
}
