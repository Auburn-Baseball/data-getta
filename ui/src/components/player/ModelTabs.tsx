import Box from '@mui/material/Box';
import Link from '@/components/ui/Link';
import { useLocation } from 'react-router';
import { useState, useEffect } from 'react';

type ModelTabsProps = {
  team: string;
  player: string;
  seasonSlug: string;
};

export default function ModelTabs({ team, player, seasonSlug }: ModelTabsProps) {
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
        href={`${baseURL}/stats/${seasonSlug}`}
        name="Stats"
        fontWeight={600}
        underline={statsUnderline}
      />
      <Link
        href={`${baseURL}/heat-map/${seasonSlug}`}
        name="Heat Maps"
        fontWeight={600}
        underline={heatMapUnderline}
      />
      <Link
        href={`${baseURL}/percentiles/${seasonSlug}`}
        name="Percentiles"
        fontWeight={600}
        underline={percentilesUnderline}
      />
    </Box>
  );
}
