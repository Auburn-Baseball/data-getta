import { Box, Typography } from '@mui/material';
import * as d3 from 'd3';
import { useMemo, useState } from 'react';
import type { ZoneBin } from '@/pages/player/HeatMapTab';
import CircleIcon from '@mui/icons-material/Circle';

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
  bins: ZoneBin[]; // sparse ok
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

export default function HeatMap({ playerName, batterFilter, pitchTypeFilter, bins }: Props) {
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
          Count_FourSeam: 0,
          Count_Sinker: 0,
          Count_Slider: 0,
          Count_Curveball: 0,
          Count_Changeup: 0,
          Count_Cutter: 0,
          Count_Splitter: 0,
          Count_Other: 0,
          Count_L: 0,
          Count_R: 0,
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
        Count_FourSeam: 0,
        Count_Sinker: 0,
        Count_Slider: 0,
        Count_Curveball: 0,
        Count_Changeup: 0,
        Count_Cutter: 0,
        Count_Splitter: 0,
        Count_Other: 0,
        Count_L: 0,
        Count_R: 0,
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
    if (selectedPitchKey) return selectedPitchKey;
    if (pitchTypeFilter === 'All') return null;
    return pitchTypeFilter as PitchKey;
  }, [pitchTypeFilter, selectedPitchKey]);

  const valueFor = (z: ZoneBin) => {
    if (!resolvedPitchKey) {
      return (
        z.Count_FourSeam +
        z.Count_Sinker +
        z.Count_Slider +
        z.Count_Curveball +
        z.Count_Changeup +
        z.Count_Cutter +
        z.Count_Splitter +
        z.Count_Other
      );
    }
    const key = ('Count_' + resolvedPitchKey) as keyof ZoneBin;
    return Number(z[key] ?? 0);
  };

  const pitchSummary = useMemo(
    () =>
      PITCH_TYPES.map((def) => {
        const key = ('Count_' + def.key) as keyof ZoneBin;
        const total = activeCells.reduce((sum, z) => sum + Number(z[key] ?? 0), 0);
        return { ...def, total };
      }),
    [activeCells],
  );

  const onPitchRowClick = (key: PitchKey) => {
    setSelectedPitchKey((prev) => (prev === key ? null : key));
  };

  const hasSide = (z: ZoneBin) => {
    if (batterFilter === 'Both') return true;
    return batterFilter === 'L' ? z.Count_L > 0 : z.Count_R > 0;
  };

  const totalShown = useMemo(() => {
    const sum = cells.reduce((acc, z) => acc + valueFor(z), 0);
    return Math.max(1, sum);
  }, [cells, resolvedPitchKey]);

  const sampleValues = useMemo(() => cells.map(valueFor), [cells, resolvedPitchKey]);
  const nonZeroValues = useMemo(() => sampleValues.filter((v) => v > 0), [sampleValues]);
  const minVal = nonZeroValues.length ? Math.min(...nonZeroValues) : 0;
  const maxVal = Math.max(1, ...sampleValues);

  const color = useMemo(
    () =>
      d3
        .scaleLinear<string>()
        .domain([minVal, maxVal / 2, maxVal])
        .range(['#3333ff', '#ffffff', '#ff6060'])
        .clamp(true)
        .interpolate(d3.interpolateRgb),
    [minVal, maxVal],
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

  // Layout: outer big 2x2, inner centered 3x3
  const W = 520;
  const H = 520;
  const margin = { top: 16, right: 16, bottom: 28, left: 16 };

  const outerSize = Math.min(W - margin.left - margin.right, H - margin.top - margin.bottom);
  const outerX = (W - outerSize) / 2;
  const outerY = (H - outerSize) / 2;
  const midX = outerX + outerSize / 2;
  const midY = outerY + outerSize / 2;

  const cell = outerSize / 6; // 3 inner cells + padding on each side (1 cell)
  const innerSize = cell * 3;
  const ix = midX - innerSize / 2;
  const iy = midY - innerSize / 2;

  const innerRectFor = (row: number, col: number) => {
    const x = ix + (col - 1) * cell;
    const y = iy + (3 - row) * cell;
    return { x, y, w: cell, h: cell };
  };

  const outerRectFor = (lab: OuterLabel) => {
    switch (lab) {
      case 'OTL':
        return { x: outerX, y: outerY, w: outerSize / 2, h: outerSize / 2 };
      case 'OTR':
        return { x: midX, y: outerY, w: outerSize / 2, h: outerSize / 2 };
      case 'OBL':
        return { x: outerX, y: midY, w: outerSize / 2, h: outerSize / 2 };
      case 'OBR':
        return { x: midX, y: midY, w: outerSize / 2, h: outerSize / 2 };
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
    const d = Math.min(r.w, r.h) * 0.14;
    return { x: cx + s.sx * d, y: cy + s.sy * d, sx: s.sx, sy: s.sy };
  }

  const resolvedPitchForDisplay = resolvedPitchKey;

  return (
    <Box sx={{ textAlign: 'center', width: '100%' }}>
      <Typography variant="h5" fontWeight={600} mt={2}>
        Pitch Heat Map - {playerName} {batterFilter !== 'Both' ? `(${batterFilter} batters)` : ''}{' '}
        {pitchTypeFilter !== 'All' ? `- ${pitchTypeFilter}` : ''}
      </Typography>

      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
        <Box sx={{ display: 'flex', gap: 4, alignItems: 'flex-start' }}>
          <svg width={W} height={H} role="img" aria-label="Pitch heatmap (3x3 + 4 outer)">
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

              const pos = outerTextPos(lab, r);
              const lineGap = 16;

              const handleClick = () => {
                setSelectedZoneId(isSelected ? null : id);
              };

              return (
                <g
                  key={`out-${lab}`}
                  onClick={handleClick}
                  style={{ cursor: 'pointer' }}
                  aria-label={`${lab} quadrant`}
                >
                  <rect
                    x={r.x}
                    y={r.y}
                    width={r.w}
                    height={r.h}
                    fill={fill}
                    opacity={dim ? 0.35 : 0.9}
                    stroke={isSelected ? '#000' : '#2d2d2d'}
                    strokeWidth={isSelected ? 3 : 1.5}
                  />
                  <text
                    x={pos.x}
                    y={pos.y}
                    fill={tColor}
                    textAnchor="middle"
                    fontWeight={600}
                    fontSize={14}
                  >
                    {pct}
                  </text>
                  <text
                    x={pos.x}
                    y={pos.y + pos.sy * lineGap}
                    fill={tColor}
                    textAnchor="middle"
                    fontSize={13}
                    opacity={0.9}
                  >
                    {v.toLocaleString()}
                  </text>
                </g>
              );
            })}

            <rect
              x={ix}
              y={iy}
              width={innerSize}
              height={innerSize}
              fill="none"
              stroke="#aab4e5"
              strokeWidth={2}
            />
            {[1, 2].map((i) => (
              <line
                key={`v${i}`}
                x1={ix + i * (innerSize / 3)}
                x2={ix + i * (innerSize / 3)}
                y1={iy}
                y2={iy + innerSize}
                stroke="#aab4e5"
                strokeWidth={1}
                opacity={0.85}
              />
            ))}
            {[1, 2].map((i) => (
              <line
                key={`h${i}`}
                x1={ix}
                x2={ix + innerSize}
                y1={iy + i * (innerSize / 3)}
                y2={iy + i * (innerSize / 3)}
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

                const handleClick = () => {
                  setSelectedZoneId(isSelected ? null : zid);
                };

                return (
                  <g
                    key={`in-${zid}`}
                    onClick={handleClick}
                    style={{ cursor: 'pointer' }}
                    aria-label={`Zone ${row}-${col}`}
                  >
                    <rect
                      x={x}
                      y={y}
                      width={w}
                      height={h}
                      fill={fill}
                      opacity={dim ? 0.35 : 1}
                      stroke={isSelected ? '#000' : '#2d2d2d'}
                      strokeWidth={isSelected ? 3 : 1.5}
                    />
                    <text
                      x={x + w / 2}
                      y={y + h / 2 - 6}
                      fill={tColor}
                      textAnchor="middle"
                      fontWeight={600}
                      fontSize={14}
                    >
                      {pct}
                    </text>
                    <text
                      x={x + w / 2}
                      y={y + h / 2 + 14}
                      fill={tColor}
                      textAnchor="middle"
                      fontSize={13}
                      opacity={0.9}
                    >
                      {v.toLocaleString()}
                    </text>
                  </g>
                );
              }),
            )}
          </svg>

          <Box
            sx={{
              minWidth: 220,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'stretch',
              textAlign: 'left',
            }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="subtitle1" fontWeight={600}>
                Pitch Counts - {selectedZoneLabel} - {selectedPitchLabel}
              </Typography>
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
            {pitchSummary.map(({ key, label, color: swatchColor, total }) => {
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
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CircleIcon sx={{ fontSize: 14, color: swatchColor }} />
                    <Typography variant="body2" fontWeight={isActive ? 600 : 500}>
                      {label}
                    </Typography>
                  </Box>
                  <Typography variant="body2" fontWeight={600}>
                    {total.toLocaleString()}
                  </Typography>
                </Box>
              );
            })}
          </Box>
        </Box>
      </Box>

      <Typography variant="body2" sx={{ mt: 1.5, opacity: 0.85 }}>
        Inner grid is a fixed 3x3 strike zone; four outer quadrants aggregate all pitches outside
        the zone and are split by the square's midlines. Percentages reflect the current pitch type
        filter; cells with no {batterFilter !== 'Both' ? `${batterFilter}-handed` : ''} pitches are
        dimmed.
      </Typography>
    </Box>
  );
}
