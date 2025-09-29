import { Box, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material';
import { useCallback, useMemo, useState } from 'react';
import BaseHeatMap from '@/components/shared/heatmap/BaseHeatMap';
import { PITCH_TYPES, type PitchKey } from '@/components/shared/heatmap/constants';
import { buildZoneMap, zoneValuesArray } from '@/components/shared/heatmap/zoneHelpers';
import type { PitcherPitchBinsTable } from '@/types/schemas';

type BatterFilter = 'Both' | 'L' | 'R';
type Side = 'L' | 'R';
type PitchCountField = `Count_${PitchKey}`;
type SidePitchCountField = `Count_${Side}_${PitchKey}`;
type CountField = PitchCountField | SidePitchCountField;

type ZoneBin = {
  zoneId: number;
  inZone: boolean;
  zoneRow: number;
  zoneCol: number;
  zoneCell: number;
  outerLabel: 'NA' | 'OTL' | 'OTR' | 'OBL' | 'OBR';
  totalPitchCount: number;
} & Record<CountField, number>;

const EMPTY_PITCHER_ROWS: PitcherPitchBinsTable[] = [];

const makeZeroCounts = (): Record<CountField, number> => {
  const counts = {} as Record<CountField, number>;
  PITCH_TYPES.forEach(({ key }) => {
    counts[`Count_${key}` as PitchCountField] = 0;
    counts[`Count_L_${key}` as SidePitchCountField] = 0;
    counts[`Count_R_${key}` as SidePitchCountField] = 0;
  });
  return counts;
};

type RawCountKey = `${'Count' | 'Count_L' | 'Count_R'}_${PitchKey}`;

const toNumeric = (value: unknown): number => {
  const numeric = Number(value ?? 0);
  return Number.isFinite(numeric) ? numeric : 0;
};

const normalizePitcherBin = (bin: PitcherPitchBinsTable): ZoneBin => {
  const record = bin as Record<RawCountKey, unknown>;
  const normalized: ZoneBin = {
    zoneId: toNumeric(bin.ZoneId),
    inZone: Boolean(bin.InZone),
    zoneRow: toNumeric(bin.ZoneRow ?? 0),
    zoneCol: toNumeric(bin.ZoneCol ?? 0),
    zoneCell: toNumeric(bin.ZoneCell ?? 0),
    outerLabel: (bin.OuterLabel ?? 'NA') as ZoneBin['outerLabel'],
    totalPitchCount: toNumeric(bin.TotalPitchCount),
    ...makeZeroCounts(),
  };

  PITCH_TYPES.forEach(({ key }) => {
    const totalKey = `Count_${key}` as RawCountKey;
    const leftKey = `Count_L_${key}` as RawCountKey;
    const rightKey = `Count_R_${key}` as RawCountKey;

    normalized[`Count_${key}` as PitchCountField] = toNumeric(record[totalKey]);
    normalized[`Count_L_${key}` as SidePitchCountField] = toNumeric(record[leftKey]);
    normalized[`Count_R_${key}` as SidePitchCountField] = toNumeric(record[rightKey]);
  });

  return normalized;
};

export default function PitcherHeatMap({ data }: { data: PitcherPitchBinsTable[] }) {
  const [batterFilter, setBatterFilter] = useState<BatterFilter>('Both');
  const [selectedZoneId, setSelectedZoneId] = useState<number | null>(null);
  const [selectedPitchKey, setSelectedPitchKey] = useState<PitchKey | null>(null);

  const sourceBins = data ?? EMPTY_PITCHER_ROWS;
  const pitcherName = sourceBins[0]?.Pitcher ?? 'Pitcher';

  const normalizedBins = useMemo(() => sourceBins.map(normalizePitcherBin), [sourceBins]);

  const zoneMap = useMemo(
    () =>
      buildZoneMap<ZoneBin>(normalizedBins, (meta) => ({
        zoneId: meta.zoneId,
        inZone: meta.inZone,
        zoneRow: meta.zoneRow,
        zoneCol: meta.zoneCol,
        zoneCell: meta.zoneCell,
        outerLabel: meta.outerLabel,
        totalPitchCount: 0,
        ...makeZeroCounts(),
      })),
    [normalizedBins],
  );
  const cells = useMemo(() => zoneValuesArray(zoneMap), [zoneMap]);

  const handleZoneSelect = useCallback((zoneId: number) => {
    setSelectedZoneId((prev) => {
      const next = prev === zoneId ? null : zoneId;
      if (next !== null) {
        setSelectedPitchKey(null);
      }
      return next;
    });
  }, []);

  const handlePitchSelect = useCallback((pitchKey: PitchKey) => {
    setSelectedPitchKey((prev) => {
      const next = prev === pitchKey ? null : pitchKey;
      if (next !== null) {
        setSelectedZoneId(null);
      }
      return next;
    });
  }, []);

  const activeCells = useMemo(() => {
    if (!selectedZoneId) return cells;
    const selected = zoneMap.get(selectedZoneId);
    return selected ? [selected] : cells;
  }, [cells, selectedZoneId, zoneMap]);

  const resolvedPitchKey = useMemo<PitchKey | null>(() => {
    if (selectedZoneId) return null;
    return selectedPitchKey;
  }, [selectedPitchKey, selectedZoneId]);

  const resolvedSide: Side | null = batterFilter === 'Both' ? null : batterFilter;

  const countForPitch = useCallback((zone: ZoneBin, pitch: PitchKey, side: Side | null) => {
    const key = (side ? `Count_${side}_${pitch}` : `Count_${pitch}`) as keyof ZoneBin;
    return Number(zone[key] ?? 0);
  }, []);

  const totalForSide = useCallback(
    (zone: ZoneBin, side: Side) =>
      PITCH_TYPES.reduce((sum, def) => sum + countForPitch(zone, def.key, side), 0),
    [countForPitch],
  );

  const zoneValue = useCallback(
    (zone: ZoneBin) => {
      if (!resolvedSide) {
        if (!resolvedPitchKey) return zone.totalPitchCount;
        return countForPitch(zone, resolvedPitchKey, null);
      }
      if (!resolvedPitchKey) return totalForSide(zone, resolvedSide);
      return countForPitch(zone, resolvedPitchKey, resolvedSide);
    },
    [countForPitch, resolvedPitchKey, resolvedSide, totalForSide],
  );

  const pitchSummary = useMemo(
    () =>
      PITCH_TYPES.map((def) => {
        const total = activeCells.reduce(
          (sum, zone) => sum + countForPitch(zone, def.key, resolvedSide),
          0,
        );
        return { ...def, total };
      }),
    [activeCells, countForPitch, resolvedSide],
  );

  const totalPitchDisplay = useMemo(
    () => pitchSummary.reduce((sum, row) => sum + row.total, 0),
    [pitchSummary],
  );

  const valueAccessor = useCallback((zone: ZoneBin) => zoneValue(zone), [zoneValue]);

  const selectedPitchLabel = useMemo(() => {
    if (!selectedPitchKey) return 'All pitches';
    return PITCH_TYPES.find((def) => def.key === selectedPitchKey)?.label ?? selectedPitchKey;
  }, [selectedPitchKey]);

  const tablePanel = (
    <Box
      key="table"
      sx={{
        minWidth: 220,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'stretch',
        textAlign: 'left',
      }}
    >
      <ToggleButtonGroup
        value={batterFilter}
        exclusive
        onChange={(_event, next) => {
          if (!next || next === batterFilter) return;
          setBatterFilter(next);
          setSelectedZoneId(null);
          setSelectedPitchKey(null);
        }}
        size="small"
        sx={{ mt: 1, mb: 1, display: 'flex', width: '100%' }}
      >
        <ToggleButton value="Both" sx={{ flex: 1 }}>
          Both
        </ToggleButton>
        <ToggleButton value="L" sx={{ flex: 1 }}>
          Left
        </ToggleButton>
        <ToggleButton value="R" sx={{ flex: 1 }}>
          Right
        </ToggleButton>
      </ToggleButtonGroup>

      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          pl: 1.5,
          pr: 1.5,
          mb: 1,
        }}
      >
        <Box>
          <Typography variant="subtitle1" fontWeight={600}>
            Pitch Counts
          </Typography>
          <Typography variant="subtitle2" fontWeight={500} sx={{ mt: -0.5 }}>
            Total: {Math.round(totalPitchDisplay).toLocaleString()}
          </Typography>
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

      {pitchSummary.map(({ key, label, total }) => {
        const isActive = resolvedPitchKey === key;
        return (
          <Box
            key={key}
            onClick={() => handlePitchSelect(key)}
            sx={{
              py: 0.75,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1px solid rgba(0,0,0,0.08)',
              cursor: 'pointer',
              backgroundColor: isActive ? 'rgba(30, 64, 175, 0.12)' : 'transparent',
              transition: 'background-color 120ms ease',
            }}
          >
            <Typography variant="body2" fontWeight={isActive ? 600 : 500} sx={{ pl: 1.5 }}>
              {label}
            </Typography>
            <Typography variant="body2" fontWeight={isActive ? 700 : 600} sx={{ pr: 1.5 }}>
              {total.toLocaleString()}
            </Typography>
          </Box>
        );
      })}
    </Box>
  );

  return (
    <Box sx={{ textAlign: 'center', width: '100%' }}>
      <Typography variant="h5" fontWeight={600} mt={2}>
        Pitch Heat Map - {pitcherName} ({batterFilter} batters, {selectedPitchLabel})
      </Typography>

      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
        <Box sx={{ display: 'flex', gap: 4, alignItems: 'flex-start', flexWrap: 'wrap' }}>
          <BaseHeatMap
            zoneMap={zoneMap}
            selectedZoneId={selectedZoneId}
            onZoneClick={handleZoneSelect}
            valueAccessor={valueAccessor}
            ariaLabel="Pitcher heat map"
          />
          {tablePanel}
        </Box>
      </Box>

      <Typography variant="body2" sx={{ mt: 1.5, opacity: 0.85 }}>
        Heat map shows pitch counts by location: inner 3×3 cells capture the strike zone, while the
        four outer panels gather pitches thrown outside. Percentages mirror the active pitch-type
        and handedness filters; areas with no matching pitches still render with a zero total.
      </Typography>
    </Box>
  );
}
