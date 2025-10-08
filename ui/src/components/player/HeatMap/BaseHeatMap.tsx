import { Box } from '@mui/material';
import * as d3 from 'd3';
import { useMemo } from 'react';
import type { BaseZone } from './zoneHelpers';
import { OUTER_ID, OUTER_LABELS } from './constants';

const DEFAULT_LAYOUT_SIZE = 520;

export type BaseHeatMapProps<T extends BaseZone> = {
  zoneMap: Map<number, T>;
  selectedZoneId: number | null;
  onZoneClick: (zoneId: number) => void;
  valueAccessor: (zone: T) => number;
  valueFormatter?: (value: number) => string;
  percentageFormatter?: (value: number, total: number) => string;
  layoutWidth?: number;
  layoutHeight?: number;
  ariaLabel?: string;
  innerOpacity?: number;
  outerOpacity?: number;
  colorValues?: number[];
};

function defaultValueFormatter(value: number): string {
  return Math.round(value).toLocaleString();
}

function defaultPercentageFormatter(value: number, total: number): string {
  const pct = total === 0 ? 0 : (value / total) * 100;
  return `${pct.toFixed(1)}%`;
}

export function BaseHeatMap<T extends BaseZone>({
  zoneMap,
  selectedZoneId,
  onZoneClick,
  valueAccessor,
  valueFormatter = defaultValueFormatter,
  percentageFormatter = defaultPercentageFormatter,
  layoutWidth = DEFAULT_LAYOUT_SIZE,
  layoutHeight = DEFAULT_LAYOUT_SIZE,
  ariaLabel = 'heat map',
  innerOpacity = 1,
  outerOpacity = 1,
  colorValues,
}: BaseHeatMapProps<T>) {
  const cells = useMemo(() => Array.from(zoneMap.values()), [zoneMap]);

  const valueSamples = useMemo(
    () =>
      colorValues && colorValues.length ? colorValues : cells.map((zone) => valueAccessor(zone)),
    [cells, colorValues, valueAccessor],
  );

  const values = useMemo(() => cells.map((zone) => valueAccessor(zone)), [cells, valueAccessor]);

  const maxValue = useMemo(() => Math.max(1, ...valueSamples), [valueSamples]);
  const totalValue = useMemo(
    () =>
      Math.max(
        1,
        values.reduce((acc, value) => acc + value, 0),
      ),
    [values],
  );

  const colorScale = useMemo(
    () =>
      d3
        .scaleLinear<string>()
        .domain([0, maxValue / 2, maxValue])
        .range(['#3333ff', '#ffffff', '#ff6060'])
        .clamp(true)
        .interpolate(d3.interpolateRgb),
    [maxValue],
  );

  const margin = { top: 9, right: 9, bottom: 9, left: 9 };
  const outerSize = Math.min(
    layoutWidth - margin.left - margin.right,
    layoutHeight - margin.top - margin.bottom,
  );
  const outerX = (layoutWidth - outerSize) / 2;
  const outerY = (layoutHeight - outerSize) / 2;
  const midX = outerX + outerSize / 2;
  const midY = outerY + outerSize / 2;
  const cellSize = outerSize / 6;
  const innerSize = cellSize * 3;
  const ix = midX - innerSize / 2;
  const iy = midY - innerSize / 2;

  const innerRectFor = (row: number, col: number) => {
    const x = ix + (col - 1) * cellSize;
    const y = iy + (3 - row) * cellSize;
    return { x, y, w: cellSize, h: cellSize };
  };

  const outerRectFor = (label: (typeof OUTER_LABELS)[number]) => {
    switch (label) {
      case 'OTL':
        return { x: outerX, y: outerY, w: outerSize / 2, h: outerSize / 2 };
      case 'OTR':
        return { x: midX, y: outerY, w: outerSize / 2, h: outerSize / 2 };
      case 'OBL':
        return { x: outerX, y: midY, w: outerSize / 2, h: outerSize / 2 };
      case 'OBR':
      default:
        return { x: midX, y: midY, w: outerSize / 2, h: outerSize / 2 };
    }
  };

  const signForOuter = {
    OTL: { sx: -1, sy: -1 },
    OTR: { sx: 1, sy: -1 },
    OBL: { sx: -1, sy: 1 },
    OBR: { sx: 1, sy: 1 },
  } as const;

  const outerTextPosition = (
    label: (typeof OUTER_LABELS)[number],
    rect: { x: number; y: number; w: number; h: number },
  ) => {
    const cx = rect.x + rect.w / 2;
    const cy = rect.y + rect.h / 2;
    const { sx, sy } = signForOuter[label];
    const offset = Math.min(rect.w, rect.h) * 0.14;
    return { x: cx + sx * offset, y: cy + sy * offset, sx, sy };
  };

  const getZone = (zoneId: number) => zoneMap.get(zoneId);

  return (
    <Box sx={{ flexShrink: 0 }}>
      <svg width={layoutWidth} height={layoutHeight} role="img" aria-label={ariaLabel}>
        {OUTER_LABELS.map((label) => {
          const zoneId = OUTER_ID[label];
          const zone = getZone(zoneId);
          const value = zone ? valueAccessor(zone) : 0;
          const rect = outerRectFor(label);
          const pos = outerTextPosition(label, rect);
          const pct = percentageFormatter(value, totalValue);
          const isSelected = selectedZoneId === zoneId;

          return (
            <g key={label} onClick={() => onZoneClick(zoneId)} style={{ cursor: 'pointer' }}>
              <rect
                x={rect.x}
                y={rect.y}
                width={rect.w}
                height={rect.h}
                fill={colorScale(value)}
                opacity={outerOpacity}
                stroke={isSelected ? '#000' : '#2d2d2d'}
                strokeWidth={isSelected ? 3 : 1.5}
              />
              <text
                x={pos.x}
                y={pos.y}
                fill="#000"
                textAnchor="middle"
                fontWeight={isSelected ? 700 : 600}
                fontSize={14}
              >
                {pct}
              </text>
              <text
                x={pos.x}
                y={pos.y + pos.sy * 16}
                fill="#000"
                textAnchor="middle"
                fontSize={13}
                fontWeight={isSelected ? 600 : 500}
                opacity={0.9}
              >
                {valueFormatter(value)}
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
            const zoneId = (row - 1) * 3 + col;
            const zone = getZone(zoneId);
            if (!zone) return null;
            const value = valueAccessor(zone);
            const { x, y, w, h } = innerRectFor(row, col);
            const pct = percentageFormatter(value, totalValue);
            const isSelected = selectedZoneId === zoneId;

            return (
              <g key={zoneId} onClick={() => onZoneClick(zoneId)} style={{ cursor: 'pointer' }}>
                <rect
                  x={x}
                  y={y}
                  width={w}
                  height={h}
                  fill={colorScale(value)}
                  opacity={innerOpacity}
                  stroke={isSelected ? '#000' : '#2d2d2d'}
                  strokeWidth={isSelected ? 3 : 1.5}
                />
                <text
                  x={x + w / 2}
                  y={y + h / 2 - 6}
                  fill="#000"
                  textAnchor="middle"
                  fontWeight={isSelected ? 700 : 600}
                  fontSize={14}
                >
                  {pct}
                </text>
                <text
                  x={x + w / 2}
                  y={y + h / 2 + 14}
                  fill="#000"
                  textAnchor="middle"
                  fontSize={13}
                  fontWeight={isSelected ? 600 : 500}
                  opacity={0.9}
                >
                  {valueFormatter(value)}
                </text>
              </g>
            );
          }),
        )}
      </svg>
    </Box>
  );
}

export default BaseHeatMap;
