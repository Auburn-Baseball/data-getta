import { Box, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material';
import * as d3 from 'd3';
import { useMemo, useState } from 'react';
import type { ZoneBin } from '@/pages/player/HeatMapTab';

type Props = {
  playerName: string;
  batterFilter: 'Both' | 'L' | 'R';
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
  bins: ZoneBin[];
  onBatterFilterChange?: (next: 'Both' | 'L' | 'R') => void;
};

const PITCH_TYPES = [
  { key: 'FourSeam', label: 'Four-seam', color: '#f97316' },
  { key: 'Sinker', label: 'Sinker', color: '#0ea5e9' },
  { key: 'Slider', label: 'Slider', color: '#a855f7' },
  { key: 'Curveball', label: 'Curveball', color: '#22c55e' },
  { key: 'Changeup', label: 'Changeup', color: '#14b8a6' },
  { key: 'Cutter', label: 'Cutter', color: '#f43f5e' },
  { key: 'Splitter', label: 'Splitter', color: '#8b5cf6' },
  { key: 'Other', label: 'Other', color: '#6b7280' },
] as const;

type PitchKey = (typeof PITCH_TYPES)[number]['key'];

// ZoneId mapping (1..9 inner; 10..13 outer)
const OUTER = ['OTL', 'OTR', 'OBL', 'OBR'] as const;
type OuterLabel = (typeof OUTER)[number];

type Side = 'L' | 'R';

type PitchCountField = `Count_${PitchKey}`;
type SidePitchCountField = `Count_${Side}_${PitchKey}`;
type CountField = PitchCountField | SidePitchCountField;

const makeZeroCounts = (): Record<CountField, number> => {
  const counts = {} as Record<CountField, number>;
  PITCH_TYPES.forEach(({ key }) => {
    counts[`Count_${key}` as PitchCountField] = 0;
    counts[`Count_L_${key}` as SidePitchCountField] = 0;
    counts[`Count_R_${key}` as SidePitchCountField] = 0;
  });
  return counts;
};

export default function HeatMap({
  playerName,
  batterFilter,
  pitchTypeFilter,
  bins,
  onBatterFilterChange,
}: Props) {
  const [selectedZoneId, setSelectedZoneId] = useState<number | null>(null);
  const [selectedPitchKey, setSelectedPitchKey] = useState<PitchKey | null>(null);

  // Build a complete 13-cell map with zeros, then overlay DB rows.
  const zoneMap = useMemo(() => {
    const m = new Map<number, ZoneBin>();
    for (let row = 1; row <= 3; row++) {
      for (let col = 1; col <= 3; col++) {
        const cell = (row - 1) * 3 + col; // 1..9
        m.set(cell, {
          zoneId: cell,
          inZone: true,
          zoneRow: row,
          zoneCol: col,
          zoneCell: cell,
          outerLabel: 'NA',
          totalPitchCount: 0,
          ...makeZeroCounts(),
        });
      }
    }

    const outerIds: Record<OuterLabel, number> = { OTL: 10, OTR: 11, OBL: 12, OBR: 13 };
    OUTER.forEach((lab) => {
      const zid = outerIds[lab];
      m.set(zid, {
        zoneId: zid,
        inZone: false,
        zoneRow: 0,
        zoneCol: 0,
        zoneCell: 0,
        outerLabel: lab,
        totalPitchCount: 0,
        ...makeZeroCounts(),
      });
    });

    for (const b of bins) m.set(b.zoneId, b);
    return m;
  }, [bins]);

  const cells = useMemo(() => Array.from(zoneMap.values()), [zoneMap]);

  const activeCells = useMemo(() => {
    if (!selectedZoneId) return cells;
    const selected = zoneMap.get(selectedZoneId);
    return selected ? [selected] : cells;
  }, [cells, selectedZoneId, zoneMap]);

  const resolvedPitchKey = useMemo<PitchKey | null>(() => {
    if (selectedZoneId) return null;
    if (selectedPitchKey) return selectedPitchKey;
    if (pitchTypeFilter === 'All') return null;
    return pitchTypeFilter as PitchKey;
  }, [pitchTypeFilter, selectedPitchKey, selectedZoneId]);

  const resolvedSide: Side | null = batterFilter === 'Both' ? null : batterFilter;

  const countForPitch = (z: ZoneBin, pitch: PitchKey, side: Side | null) => {
    const key = (side ? `Count_${side}_${pitch}` : `Count_${pitch}`) as keyof ZoneBin;
    return Number(z[key] ?? 0);
  };

  const totalForSide = (z: ZoneBin, side: Side) =>
    PITCH_TYPES.reduce((sum, def) => sum + countForPitch(z, def.key, side), 0);

  const valueFor = (z: ZoneBin) => {
    if (!resolvedSide) {
      if (!resolvedPitchKey) return z.totalPitchCount;
      return countForPitch(z, resolvedPitchKey, null);
    }
    if (!resolvedPitchKey) return totalForSide(z, resolvedSide);
    return countForPitch(z, resolvedPitchKey, resolvedSide);
  };

  const pitchSummary = useMemo(
    () =>
      PITCH_TYPES.map((def) => {
        const total = activeCells.reduce(
          (sum, z) => sum + countForPitch(z, def.key, resolvedSide),
          0,
        );
        return { ...def, total };
      }),
    [activeCells, resolvedSide],
  );

  const totalPitchDisplay = useMemo(
    () => pitchSummary.reduce((sum, entry) => sum + entry.total, 0),
    [pitchSummary],
  );

  const onPitchRowClick = (key: PitchKey) => {
    setSelectedPitchKey((prev) => {
      if (prev === key) return null;
      setSelectedZoneId(null);
      return key;
    });
  };

  const handleZoneSelect = (zoneId: number) => {
    setSelectedZoneId((prev) => (prev === zoneId ? null : zoneId));
    setSelectedPitchKey(null);
  };

  const hasSide = (z: ZoneBin) => {
    if (!resolvedSide) return z.totalPitchCount > 0;
    return totalForSide(z, resolvedSide) > 0;
  };

  const totalShown = useMemo(() => {
    const sum = cells.reduce((acc, z) => acc + valueFor(z), 0);
    return Math.max(1, sum);
  }, [cells, resolvedPitchKey, resolvedSide]);

  const sampleValues = useMemo(() => cells.map(valueFor), [cells, resolvedPitchKey, resolvedSide]);
  const displayMax = useMemo(() => {
    if (!sampleValues.length) return 1;
    const maxSample = Math.max(...sampleValues);
    return Math.max(1, maxSample);
  }, [sampleValues]);

  const color = useMemo(
    () =>
      d3
        .scaleLinear<string>()
        .domain([0, displayMax / 2, displayMax])
        .range(['#3333ff', '#ffffff', '#ff6060'])
        .clamp(true)
        .interpolate(d3.interpolateRgb),
    [displayMax],
  );

  const selectedZoneLabel = useMemo(() => {
    if (!selectedZoneId) return 'All zones';
    const zone = zoneMap.get(selectedZoneId);
    if (!zone) return 'All zones';
    if (zone.inZone) {
      return `Zone ${zone.zoneRow}-${zone.zoneCol}`;
    }
    return `${zone.outerLabel} quadrant`;
  }, [selectedZoneId, zoneMap]);

  const selectedPitchLabel = useMemo(() => {
    if (!resolvedPitchKey) return 'All pitches';
    const hit = PITCH_TYPES.find((p) => p.key === resolvedPitchKey);
    return hit ? hit.label : resolvedPitchKey;
  }, [resolvedPitchKey]);

  // Layout: derive a compact square that tightly wraps the four outer quadrants.
  const margin = { top: 12, right: 12, bottom: 12, left: 12 };
  const baseCell = 80;
  const outerSize = baseCell * 6;
  const midX = outerSize / 2;
  const midY = outerSize / 2;

  const cell = outerSize / 6;
  const innerSize = cell * 3;
  const ix = midX - innerSize / 2;
  const iy = midY - innerSize / 2;

  const quadrantSize = outerSize / 2.5;
  const heatmapOriginX = midX - quadrantSize;
  const heatmapOriginY = midY - quadrantSize;
  const heatmapSize = quadrantSize * 2;
  const svgWidth = heatmapSize + margin.left + margin.right;
  const svgHeight = heatmapSize + margin.top + margin.bottom;

  const toSvgX = (value: number) => value - heatmapOriginX + margin.left;
  const toSvgY = (value: number) => value - heatmapOriginY + margin.top;

  const innerRectFor = (row: number, col: number) => {
    const x = ix + (col - 1) * cell;
    const y = iy + (3 - row) * cell;
    return { x, y, w: cell, h: cell };
  };

  const outerRectFor = (lab: OuterLabel) => {
    const w = quadrantSize;
    const h = quadrantSize;
    const left = midX - w;
    const top = midY - h;
    switch (lab) {
      case 'OTL':
        return { x: left, y: top, w, h };
      case 'OTR':
        return { x: midX, y: top, w, h };
      case 'OBL':
        return { x: left, y: midY, w, h };
      case 'OBR':
        return { x: midX, y: midY, w, h };
    }
  };

  const signFor: Record<OuterLabel, { sx: number; sy: number }> = {
    OTL: { sx: -1, sy: -1 },
    OTR: { sx: 1, sy: -1 },
    OBL: { sx: -1, sy: 1 },
    OBR: { sx: 1, sy: 1 },
  };

  function outerTextPos(lab: OuterLabel, r: { x: number; y: number; w: number; h: number }) {
    const cx = r.x + r.w / 2;
    const cy = r.y + r.h / 2;
    const s = signFor[lab];
    const d = Math.min(r.w, r.h) * 0.25;
    return { x: cx + s.sx * d, y: cy + s.sy * d, sx: s.sx, sy: s.sy };
  }

  const resolvedPitchForDisplay = resolvedPitchKey;

  const heatMapGraphic = (
    <Box
      key="heatmap"
      sx={{
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <svg
        width={svgWidth}
        height={svgHeight}
        viewBox={`0 0 ${svgWidth} ${svgHeight}`}
        role="img"
        aria-label="Pitch heatmap (3x3 + 4 outer)"
      >
        {OUTER.map((lab) => {
          const id = ({ OTL: 10, OTR: 11, OBL: 12, OBR: 13 } as const)[lab];
          const z = zoneMap.get(id)!;
          const v = valueFor(z);
          const fill = color(v);
          const dim = !hasSide(z);
          const r = outerRectFor(lab)!;
          const pct = ((v / totalShown) * 100).toFixed(1) + '%';
          const tColor = '#000';
          const isSelected = selectedZoneId === id;
          const pctWeight = isSelected ? 800 : 600;
          const countWeight = isSelected ? 700 : 500;

          const pos = outerTextPos(lab, r);
          const lineGap = 16;

          const handleClick = () => {
            handleZoneSelect(id);
          };

          return (
            <g
              key={`out-${lab}`}
              onClick={handleClick}
              style={{ cursor: 'pointer' }}
              aria-label={`${lab} quadrant`}
            >
              <rect
                x={toSvgX(r.x)}
                y={toSvgY(r.y)}
                width={r.w}
                height={r.h}
                fill={fill}
                opacity={dim ? 0.35 : 0.9}
                stroke={isSelected ? '#000' : '#2d2d2d'}
                strokeWidth={isSelected ? 3 : 1.5}
              />
              <text
                x={toSvgX(pos.x)}
                y={toSvgY(pos.y)}
                fill={tColor}
                textAnchor="middle"
                fontWeight={pctWeight}
                fontSize={14}
              >
                {pct}
              </text>
              <text
                x={toSvgX(pos.x)}
                y={toSvgY(pos.y + pos.sy * lineGap)}
                fill={tColor}
                textAnchor="middle"
                fontSize={13}
                fontWeight={countWeight}
                opacity={0.9}
              >
                {v.toLocaleString()}
              </text>
            </g>
          );
        })}

        <rect
          x={toSvgX(ix)}
          y={toSvgY(iy)}
          width={innerSize}
          height={innerSize}
          fill="none"
          stroke="#aab4e5"
          strokeWidth={2}
        />
        {[1, 2].map((i) => (
          <line
            key={`v${i}`}
            x1={toSvgX(ix + i * (innerSize / 3))}
            x2={toSvgX(ix + i * (innerSize / 3))}
            y1={toSvgY(iy)}
            y2={toSvgY(iy + innerSize)}
            stroke="#aab4e5"
            strokeWidth={1}
            opacity={0.85}
          />
        ))}
        {[1, 2].map((i) => (
          <line
            key={`h${i}`}
            x1={toSvgX(ix)}
            x2={toSvgX(ix + innerSize)}
            y1={toSvgY(iy + i * (innerSize / 3))}
            y2={toSvgY(iy + i * (innerSize / 3))}
            stroke="#aab4e5"
            strokeWidth={1}
            opacity={0.85}
          />
        ))}

        {Array.from({ length: 3 }).flatMap((_, r) =>
          Array.from({ length: 3 }).map((__, c) => {
            const row = r + 1;
            const col = c + 1;
            const zid = (row - 1) * 3 + col;
            const z = zoneMap.get(zid)!;
            const v = valueFor(z);
            const fill = color(v);
            const dim = !hasSide(z);
            const { x, y, w, h } = innerRectFor(row, col);
            const pct = ((v / totalShown) * 100).toFixed(1) + '%';
            const tColor = '#000';
            const isSelected = selectedZoneId === zid;
            const pctWeight = isSelected ? 800 : 600;
            const countWeight = isSelected ? 700 : 500;

            const handleClick = () => {
              handleZoneSelect(zid);
            };

            return (
              <g
                key={`in-${zid}`}
                onClick={handleClick}
                style={{ cursor: 'pointer' }}
                aria-label={`Zone ${row}-${col}`}
              >
                <rect
                  x={toSvgX(x)}
                  y={toSvgY(y)}
                  width={w}
                  height={h}
                  fill={fill}
                  opacity={dim ? 0.35 : 1}
                  stroke={isSelected ? '#000' : '#2d2d2d'}
                  strokeWidth={isSelected ? 3 : 1.5}
                />
                <text
                  x={toSvgX(x + w / 2)}
                  y={toSvgY(y + h / 2 - 6)}
                  fill={tColor}
                  textAnchor="middle"
                  fontWeight={pctWeight}
                  fontSize={14}
                >
                  {pct}
                </text>
                <text
                  x={toSvgX(x + w / 2)}
                  y={toSvgY(y + h / 2 + 14)}
                  fill={tColor}
                  textAnchor="middle"
                  fontSize={13}
                  fontWeight={countWeight}
                  opacity={0.9}
                >
                  {v.toLocaleString()}
                </text>
              </g>
            );
          }),
        )}
      </svg>
    </Box>
  );

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
          onBatterFilterChange?.(next);
        }}
        size="small"
        disabled={!onBatterFilterChange}
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
          <Typography variant="subtitle2" fontWeight={500} sx={{ mt: -0.75 }}>
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
      {pitchSummary.map(({ key, label, total }) => {
        const isActive = resolvedPitchForDisplay === key;
        return (
          <Box
            key={key}
            onClick={() => onPitchRowClick(key)}
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
        Pitch Heat Map {`(${batterFilter} batters)`}
        {pitchTypeFilter !== 'All' ? `- ${pitchTypeFilter}` : ''}
      </Typography>

      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
        <Box sx={{ display: 'flex', gap: 4, alignItems: 'flex-start', flexWrap: 'wrap' }}>
          {heatMapGraphic}
          {tablePanel}
        </Box>
      </Box>

      <Typography variant="body2" sx={{ mt: 1.5, opacity: 0.85 }}>
        Heat map shows pitch counts by location: inner 3×3 cells capture the strike zone, while the
        four outer panels gather pitches thrown outside. Percentages mirror the active pitch-type
        and handedness filters; locations with no matching pitches are dimmed.
      </Typography>
    </Box>
  );
}
