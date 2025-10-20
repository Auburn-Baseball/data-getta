import { Box, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material';
import { useCallback, useMemo, useState } from 'react';
import BaseHeatMap from '@/components/player/HeatMap/BaseHeatMap';
import { PITCH_TYPES, type PitchKey } from '@/components/player/HeatMap/constants';
import { buildZoneMap, zoneValuesArray } from '@/components/player/HeatMap/zoneHelpers';
import type { PitcherPitchBinsTable } from '@/types/db';
import { HEATMAP_ZONE_DESCRIPTION, ensureRows, selectedPitchLabel, toNumeric } from './utils';
import { useHeatMapSelections } from './useHeatMapSelections';

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

  const sourceRows = ensureRows(data);
  const pitcherName = sourceRows[0]?.Pitcher ?? 'Pitcher';

  const normalizedRows = useMemo(() => sourceRows.map(normalizePitcherBin), [sourceRows]);
  const zoneMap = useMemo(
    () =>
      buildZoneMap<ZoneBin>(normalizedRows, (meta) => ({
        zoneId: meta.zoneId,
        inZone: meta.inZone,
        zoneRow: meta.zoneRow,
        zoneCol: meta.zoneCol,
        zoneCell: meta.zoneCell,
        outerLabel: meta.outerLabel,
        totalPitchCount: 0,
        ...makeZeroCounts(),
      })),
    [normalizedRows],
  );

  const cells = useMemo(() => zoneValuesArray(zoneMap), [zoneMap]);

  const {
    selectedZoneId,
    selectedPitchKey,
    resolvedPitchKey,
    activeCells,
    onZoneSelect,
    onPitchSelect,
    clearSelections,
    hasSelection,
  } = useHeatMapSelections(zoneMap, cells);

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

  const colorValues = useMemo(() => cells.map((zone) => zoneValue(zone)), [cells, zoneValue]);

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

  const headerPitchLabel = selectedPitchLabel(selectedPitchKey);

  return (
    <Box sx={{ textAlign: 'center', width: '100%' }}>
      <Typography variant="h5" fontWeight={600} mt={2}>
        Pitch Heat Map - {pitcherName} ({batterFilter} batters, {headerPitchLabel})
      </Typography>

      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
        <Box sx={{ display: 'flex', gap: 4, alignItems: 'flex-start', flexWrap: 'wrap' }}>
          <BaseHeatMap
            zoneMap={zoneMap}
            selectedZoneId={selectedZoneId}
            onZoneClick={onZoneSelect}
            valueAccessor={valueAccessor}
            colorValues={colorValues}
            ariaLabel="Pitcher heat map"
          />

          <Box
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
                clearSelections();
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
              <Box sx={{ width: '100%' }}>
                <Box
                  sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                >
                  <Typography variant="subtitle1" fontWeight={600}>
                    Pitch Counts
                  </Typography>
                  {hasSelection && (
                    <Typography
                      variant="body2"
                      onClick={clearSelections}
                      sx={{
                        color: '#1d4ed8',
                        cursor: 'pointer',
                        userSelect: 'none',
                        fontWeight: 500,
                      }}
                    >
                      Clear
                    </Typography>
                  )}
                </Box>
                <Typography variant="subtitle2" fontWeight={500} sx={{ mt: -0.5 }}>
                  Total: {Math.round(totalPitchDisplay).toLocaleString()}
                </Typography>
              </Box>
            </Box>

            {pitchSummary.map(({ key, label, total }) => {
              const isActive = resolvedPitchKey === key;
              return (
                <Box
                  key={key}
                  onClick={() => onPitchSelect(key)}
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
        </Box>
      </Box>

      <Typography variant="body2" sx={{ mt: 1.5, opacity: 0.85 }}>
        {HEATMAP_ZONE_DESCRIPTION}
      </Typography>
    </Box>
  );
}
