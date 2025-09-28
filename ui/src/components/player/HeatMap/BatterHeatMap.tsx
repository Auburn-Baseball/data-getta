import { Box, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material';
import { useCallback, useMemo, useState } from 'react';
import BaseHeatMap from '@/components/shared/heatmap/BaseHeatMap';
import { PITCH_TYPES, type PitchKey } from '@/components/shared/heatmap/constants';
import { buildZoneMap, zoneValuesArray } from '@/components/shared/heatmap/zoneHelpers';

type Side = 'Swing' | 'Contact';

type PitchCounts<TPrefix extends string> = {
  [K in (typeof PITCH_TYPES)[number]['key'] as `${TPrefix}_${K}`]: number;
};

export type BatterZoneSummary = {
  zoneId: number;
  inZone: boolean;
  zoneRow: number;
  zoneCol: number;
  zoneCell: number;
  outerLabel: 'NA' | 'OTL' | 'OTR' | 'OBL' | 'OBR';
  totalPitchCount: number;
  totalSwingCount: number;
  totalHitCount: number;
} & PitchCounts<'Count'> &
  PitchCounts<'SwingCount'> &
  PitchCounts<'HitCount'>;

type Props = {
  batterName: string;
  pitchTypeFilter:
    | 'All'
    | 'FourSeam'
    | 'Sinker'
    | 'Slider'
    | 'Curveball'
    | 'Changeup'
    | 'Cutter'
    | 'Splitter'
    | 'Other';
  bins: BatterZoneSummary[];
};

const makeZeroCounts = (): Record<string, number> => {
  const counts: Record<string, number> = {};
  PITCH_TYPES.forEach(({ key }) => {
    counts[`Count_${key}`] = 0;
    counts[`SwingCount_${key}`] = 0;
    counts[`HitCount_${key}`] = 0;
  });
  return counts;
};

export default function BatterHeatMap({ batterName, pitchTypeFilter, bins }: Props) {
  const [view, setView] = useState<Side>('Swing');
  const [selectedZoneId, setSelectedZoneId] = useState<number | null>(null);
  const [selectedPitchKey, setSelectedPitchKey] = useState<PitchKey | null>(null);

  const zoneMap = useMemo(
    () =>
      buildZoneMap<BatterZoneSummary>(bins, (meta) => ({
        zoneId: meta.zoneId,
        inZone: meta.inZone,
        zoneRow: meta.zoneRow,
        zoneCol: meta.zoneCol,
        zoneCell: meta.zoneCell,
        outerLabel: meta.outerLabel,
        totalPitchCount: 0,
        totalSwingCount: 0,
        totalHitCount: 0,
        ...makeZeroCounts(),
      })),
    [bins],
  );

  const cells = useMemo(() => zoneValuesArray(zoneMap), [zoneMap]);

  const resolvedPitchKey = useMemo<PitchKey | null>(() => {
    if (selectedPitchKey) return selectedPitchKey;
    if (pitchTypeFilter === 'All') return null;
    return pitchTypeFilter as PitchKey;
  }, [pitchTypeFilter, selectedPitchKey]);

  const activeCells = useMemo(() => {
    if (!selectedZoneId) return cells;
    const selected = zoneMap.get(selectedZoneId);
    return selected ? [selected] : cells;
  }, [cells, selectedZoneId, zoneMap]);

  const countForPitch = useCallback(
    (zone: BatterZoneSummary, key: PitchKey, metric: Side | 'Pitch') => {
      const column =
        metric === 'Pitch'
          ? (`Count_${key}` as const)
          : metric === 'Swing'
            ? (`SwingCount_${key}` as const)
            : (`HitCount_${key}` as const);
      return Number(zone[column] ?? 0);
    },
    [],
  );

  const zoneValue = useCallback(
    (zone: BatterZoneSummary) => {
      if (!resolvedPitchKey) {
        if (view === 'Swing') return zone.totalSwingCount;
        if (view === 'Contact') return zone.totalHitCount;
        return zone.totalPitchCount;
      }
      return countForPitch(zone, resolvedPitchKey, view);
    },
    [countForPitch, resolvedPitchKey, view],
  );

  const pitchSummary = useMemo(
    () =>
      PITCH_TYPES.map((def) => {
        const pitches = activeCells.reduce((sum, z) => sum + countForPitch(z, def.key, 'Pitch'), 0);
        const swings = activeCells.reduce((sum, z) => sum + countForPitch(z, def.key, 'Swing'), 0);
        const hits = activeCells.reduce((sum, z) => sum + countForPitch(z, def.key, 'Contact'), 0);
        return { ...def, pitches, swings, hits };
      }),
    [activeCells, countForPitch],
  );

  const totalDisplay = useMemo(
    () => pitchSummary.reduce((sum, row) => sum + (view === 'Swing' ? row.swings : row.hits), 0),
    [pitchSummary, view],
  );

  const onZoneClick = useCallback((zoneId: number) => {
    setSelectedZoneId((prev) => {
      const next = prev === zoneId ? null : zoneId;
      if (next !== null) {
        setSelectedPitchKey(null);
      }
      return next;
    });
  }, []);

  const onPitchClick = useCallback((key: PitchKey) => {
    setSelectedPitchKey((prev) => {
      const next = prev === key ? null : key;
      if (next !== null) {
        setSelectedZoneId(null);
      }
      return next;
    });
  }, []);

  const valueAccessor = useCallback((zone: BatterZoneSummary) => zoneValue(zone), [zoneValue]);

  return (
    <Box sx={{ textAlign: 'center', width: '100%' }}>
      <Typography variant="h5" fontWeight={600} mt={2}>
        Batter Heat Map - {batterName} {pitchTypeFilter !== 'All' ? `- ${pitchTypeFilter}` : ''}
      </Typography>

      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
        <Box sx={{ display: 'flex', gap: 4, alignItems: 'flex-start', flexWrap: 'wrap' }}>
          <BaseHeatMap
            zoneMap={zoneMap}
            selectedZoneId={selectedZoneId}
            onZoneClick={onZoneClick}
            valueAccessor={valueAccessor}
            ariaLabel="Batter heat map"
          />

          <Box
            sx={{
              minWidth: 260,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'stretch',
              textAlign: 'left',
            }}
          >
            <ToggleButtonGroup
              value={view}
              exclusive
              onChange={(_event, next: Side | null) => next && setView(next)}
              size="small"
              sx={{ mt: 1, mb: 1, display: 'flex', width: '100%' }}
            >
              <ToggleButton value="Swing" sx={{ flex: 1 }}>
                Swings
              </ToggleButton>
              <ToggleButton value="Contact" sx={{ flex: 1 }}>
                Contact
              </ToggleButton>
            </ToggleButtonGroup>

            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                px: 1.5,
              }}
            >
              <Box sx={{ width: '100%' }}>
                <Typography variant="subtitle1" fontWeight={600}>
                  Pitch Counts
                </Typography>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                  <Typography variant="subtitle2" fontWeight={500} sx={{ mt: -0.5 }}>
                    {view === 'Swing' ? 'Pitches' : 'Swings'}:{' '}
                    {Math.round(
                      pitchSummary.reduce(
                        (sum, row) => sum + (view === 'Swing' ? row.pitches : row.swings),
                        0,
                      ),
                    ).toLocaleString()}
                  </Typography>
                  <Typography variant="subtitle2" fontWeight={500} sx={{ mt: -0.5 }}>
                    {view === 'Swing' ? 'Swings' : 'Contact'}:{' '}
                    {Math.round(totalDisplay).toLocaleString()}
                  </Typography>
                </Box>
              </Box>
              {(selectedZoneId || selectedPitchKey) && (
                <Typography
                  variant="body2"
                  onClick={() => {
                    setSelectedZoneId(null);
                    setSelectedPitchKey(null);
                  }}
                  sx={{ color: '#1d4ed8', cursor: 'pointer', userSelect: 'none', fontWeight: 500 }}
                >
                  Clear
                </Typography>
              )}
            </Box>

            {pitchSummary.map(({ key, label, pitches, swings, hits }) => {
              const isActive = resolvedPitchKey === key;
              const metrics =
                view === 'Swing'
                  ? [
                      { label: 'Pitches', value: pitches },
                      { label: 'Swings', value: swings },
                    ]
                  : [
                      { label: 'Swings', value: swings },
                      { label: 'Contact', value: hits },
                    ];
              return (
                <Box
                  key={key}
                  onClick={() => onPitchClick(key)}
                  sx={{
                    py: 0.75,
                    px: 1.5,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 0.25,
                    borderBottom: '1px solid rgba(0,0,0,0.08)',
                    cursor: 'pointer',
                    backgroundColor: isActive ? 'rgba(30, 64, 175, 0.12)' : 'transparent',
                    transition: 'background-color 120ms ease',
                  }}
                >
                  <Typography variant="body2" fontWeight={isActive ? 600 : 500}>
                    {label}
                  </Typography>
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      gap: 1,
                      fontSize: 12,
                      color: '#334155',
                    }}
                  >
                    {metrics.map((metric) => (
                      <span key={metric.label}>
                        {metric.label}: {Math.round(metric.value).toLocaleString()}
                      </span>
                    ))}
                  </Box>
                </Box>
              );
            })}
          </Box>
        </Box>
      </Box>

      <Typography variant="body2" sx={{ mt: 1.5, opacity: 0.85 }}>
        Toggle between swing frequency and contact success to explore where {batterName} chases or
        squares up pitches. Cells reflect the active view and pitch-type filter; areas with no
        matching swings or contact still render with a zero total.
      </Typography>
    </Box>
  );
}
