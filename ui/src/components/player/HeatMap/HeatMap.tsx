import { Box, Typography } from '@mui/material';
import * as d3 from 'd3';
import { useMemo } from 'react';
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
  bins: ZoneBin[]; // sparse ok
};

// For drawing only (fixed visual)
const Z = { halfWidth: 0.8391667, yBot: 1.5, yTop: 3.5 };

// ZoneId mapping (1..9 inner; 10..13 outer)
const OUTER = ['OTL', 'OTR', 'OBL', 'OBR'] as const;
type OuterLabel = (typeof OUTER)[number];

export default function HeatMap({ playerName, batterFilter, pitchTypeFilter, bins }: Props) {
  // Build a complete 13-cell map with zeros, then overlay DB rows.
  const zoneMap = useMemo(() => {
    const m = new Map<number, ZoneBin>();
    // inner 3x3, row-major (row 1=bottom)
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
    // outer 4 (10..13): OTL, OTR, OBL, OBR
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
    // overlay real rows
    for (const b of bins) m.set(b.zoneId, b);
    return m;
  }, [bins]);

  const cells = useMemo(() => Array.from(zoneMap.values()), [zoneMap]);

  // Pick the value shown per cell
  const valueFor = (z: ZoneBin) => {
    if (pitchTypeFilter === 'All') {
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
    const key = ('Count_' + pitchTypeFilter) as keyof ZoneBin;
    return Number(z[key] ?? 0);
  };

  // Batter filter: dim cells with no pitches of that handedness
  const hasSide = (z: ZoneBin) => {
    if (batterFilter === 'Both') return true;
    return batterFilter === 'L' ? z.Count_L > 0 : z.Count_R > 0;
  };

  const totalShown = useMemo(() => {
    const s = cells.reduce((acc, z) => acc + valueFor(z), 0);
    return Math.max(1, s);
  }, [cells, pitchTypeFilter]);

  const maxVal = useMemo(() => Math.max(1, ...cells.map(valueFor)), [cells, pitchTypeFilter]);
  const color = d3.scaleSequential(d3.interpolatePlasma).domain([0, maxVal]);

  // Layout: outer big 2×2, inner centered 3×3
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

  // Helpers
  const innerRectFor = (row: number, col: number) => {
    // row 1 = bottom, SVG y grows downward
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

  const textFill = (fill: string) => {
    const { r, g, b } = d3.rgb(fill);
    const L = 0.2126 * r + 0.7152 * g + 0.0722 * b;
    return L < 140 ? '#fff' : '#222';
  };

  // --- New: offset outer labels away from center so they don't overlap inner grid ---
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
    // offset ~18% of the quadrant size outward from center (scales with lacd uiyout)
    const d = Math.min(r.w, r.h) * 0.14;
    return { x: cx + s.sx * d, y: cy + s.sy * d, sx: s.sx, sy: s.sy };
  }

  return (
    <Box sx={{ textAlign: 'center', width: '100%' }}>
      <Typography variant="h5" fontWeight={600} mt={2}>
        Pitch Heat Map — {playerName} {batterFilter !== 'Both' ? `(${batterFilter} batters)` : ''}{' '}
        {pitchTypeFilter !== 'All' ? `• ${pitchTypeFilter}` : ''}
      </Typography>

      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
        <svg width={W} height={H} role="img" aria-label="Pitch heatmap (3x3 + 4 outer)">
          {/* background & big frame */}
          <rect x={0} y={0} width={W} height={H} rx={12} fill="#111" />
          <rect
            x={outerX}
            y={outerY}
            width={outerSize}
            height={outerSize}
            rx={10}
            fill="#181818"
            stroke="#2a2a2a"
          />

          {/* outer 2×2 quadrants (below inner grid), labels offset away from center */}
          {OUTER.map((lab) => {
            const id = ({ OTL: 10, OTR: 11, OBL: 12, OBR: 13 } as const)[lab];
            const z = zoneMap.get(id)!;
            const v = valueFor(z);
            const fill = color(v);
            const dim = !hasSide(z);
            const r = outerRectFor(lab);
            const pct = ((v / totalShown) * 100).toFixed(1) + '%';
            const tColor = textFill(fill);

            const pos = outerTextPos(lab, r); // position nudged toward corner
            const lineGap = 16; // distance between % and count
            return (
              <g key={`out-${lab}`}>
                <rect
                  x={r.x}
                  y={r.y}
                  width={r.w}
                  height={r.h}
                  fill={fill}
                  opacity={dim ? 0.35 : 0.9}
                  stroke="#2d2d2d"
                />
                {/* percentage */}
                <text
                  x={pos.x}
                  y={pos.y}
                  fill={tColor}
                  textAnchor="middle"
                  fontWeight={700}
                  fontSize={13}
                >
                  {pct}
                </text>
                {/* count, further along the same outward direction */}
                <text
                  x={pos.x}
                  y={pos.y + pos.sy * lineGap}
                  fill={tColor}
                  textAnchor="middle"
                  fontSize={12}
                  opacity={0.9}
                >
                  {v.toLocaleString()}
                </text>
              </g>
            );
          })}

          {/* inner strike zone outline + grid */}
          <rect
            x={ix}
            y={iy}
            width={innerSize}
            height={innerSize}
            fill="none"
            stroke="#aab4e5"
            strokeWidth={2}
            rx={6}
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

          {/* inner 3×3 cells */}
          {Array.from({ length: 3 }).flatMap((_, r) =>
            Array.from({ length: 3 }).map((__, c) => {
              const row = r + 1,
                col = c + 1;
              const zid = (row - 1) * 3 + col;
              const z = zoneMap.get(zid)!;
              const v = valueFor(z);
              const fill = color(v);
              const dim = !hasSide(z);
              const { x, y, w, h } = innerRectFor(row, col);
              const pct = ((v / totalShown) * 100).toFixed(1) + '%';
              const tColor = textFill(fill);
              return (
                <g key={`in-${zid}`}>
                  <rect
                    x={x}
                    y={y}
                    width={w}
                    height={h}
                    fill={fill}
                    opacity={dim ? 0.35 : 1}
                    stroke="#2d2d2d"
                    rx={6}
                  />
                  <text
                    x={x + w / 2}
                    y={y + h / 2 - 6}
                    fill={tColor}
                    textAnchor="middle"
                    fontWeight={700}
                    fontSize={13}
                  >
                    {pct}
                  </text>
                  <text
                    x={x + w / 2}
                    y={y + h / 2 + 14}
                    fill={tColor}
                    textAnchor="middle"
                    fontSize={12}
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

      <Typography variant="body2" sx={{ mt: 1.5, opacity: 0.85 }}>
        Inner grid is a fixed 3×3 strike zone; four outer quadrants aggregate all pitches outside
        the zone and are split by the square’s midlines. Percentages reflect the current pitch type
        filter; cells with no {batterFilter !== 'Both' ? `${batterFilter}-handed` : ''} pitches are
        dimmed.
      </Typography>
    </Box>
  );
}
