import { Box, Typography, Grid, Chip } from '@mui/material';
import FilterDropdowns from './FilterDropdowns';
import { useSearchParams } from 'react-router';
import * as d3 from 'd3';
import * as d3Contour from 'd3-contour';
import { useMemo } from 'react';

type Pitch = {
  x: number;
  y: number;
  pitchType: string;
  batterSide: string;
};

type DensityContour = d3Contour.ContourMultiPolygon & { value: number };

const pitchColors: Record<string, string> = {
  Fastball: '#e6194B',
  Curveball: '#3cb44b',
  Slider: '#ffe119',
  Changeup: '#4363d8',
  Sinker: '#f58231',
};

const customAuburnInterpolator = d3
  .scaleLinear<string>()
  .domain([0, 0.5, 1])
  .range(['#fcd5b5', '#e87722', '#0c2340'])
  .interpolate(d3.interpolateRgb);

export default function HeatMap({
  playerName,
  batterFilter,
  pitches,
}: {
  playerName: string;
  batterFilter: string;
  pitches: Pitch[];
}) {
  const [searchParams] = useSearchParams();
  const viewMode = searchParams.get('view') || 'Density';
  const showDensity = viewMode === 'Density';

  const width = 500;
  const height = 750;
  const padding = 50;

  const xMin = -1.5;
  const xMax = 1.5;
  const yMin = -0.5;
  const yMax = 5.0;

  const svgX = d3
    .scaleLinear()
    .domain([xMin, xMax])
    .range([padding, width - padding]);
  const svgY = d3
    .scaleLinear()
    .domain([yMax, yMin])
    .range([padding, height - padding]);

  const strikeZoneTop = 3.5;
  const strikeZoneBottom = 1.5;
  const strikeZoneHalfWidth = 1.417 / 2;

  const validPitches = useMemo<Pitch[]>(
    () =>
      pitches.filter(
        (p) =>
          typeof p.x === 'number' &&
          typeof p.y === 'number' &&
          !isNaN(p.x) &&
          !isNaN(p.y) &&
          p.y >= 0 &&
          p.x >= xMin &&
          p.x <= xMax &&
          p.y <= yMax,
      ),
    [pitches, xMin, xMax, yMax],
  );

  const filteredPitches = useMemo<Pitch[]>(() => {
    if (batterFilter === 'Both') return validPitches;
    console.log(`Filtering by batter side: ${batterFilter}`);
    return validPitches.filter((p) => p.batterSide === batterFilter);
  }, [validPitches, batterFilter]);

  const densityContours = useMemo<DensityContour[]>(() => {
    if (!showDensity || filteredPitches.length === 0) return [];
    const thresholds = Math.min(filteredPitches.length, 20);
    const rawContours: d3Contour.ContourMultiPolygon[] = d3Contour
      .contourDensity<Pitch>()
      .x((d: Pitch) => svgX(d.x))
      .y((d: Pitch) => svgY(d.y))
      .size([width, height])
      .bandwidth(20)
      .thresholds(thresholds)(filteredPitches);

    // Scale density values to sum to the point count
    const total: number =
      d3.sum<d3Contour.ContourMultiPolygon>(rawContours, (contour: d3Contour.ContourMultiPolygon) => contour.value) || 1;
    return rawContours.map(
      (contour: d3Contour.ContourMultiPolygon): DensityContour =>
      ({
        ...contour,
        value: (contour.value * filteredPitches.length) / total,
      }) as DensityContour,
    );
  }, [filteredPitches, showDensity, svgX, svgY, width, height]);

  const maxCount: number = Math.round(d3.max(densityContours, (contour: DensityContour) => contour.value) ?? 1);
  const colorScale = d3
    .scaleSequential((t: number) => customAuburnInterpolator(t))
    .domain([0, maxCount]);

  return (
    <Box textAlign="center">
      <Typography variant="h5" fontWeight={600} mt={2}>
        {showDensity ? 'Pitch Density Heat Map' : 'Pitch Location Heat Map'}
      </Typography>

      <FilterDropdowns player={playerName} />

      <Box
        mt={2}
        sx={{
          display: 'flex',
          justifyContent: 'center',
          width: '100%',
        }}
      >
        <Box
          sx={{
            display: 'inline-block',
            marginLeft: showDensity ? '-40px' : '0px',
          }}
        >
          <svg width={width + 100} height={height}>
            <defs>
              <linearGradient id="color-gradient" x1="0" y1="1" x2="0" y2="0">
                {Array.from({ length: 20 }, (_, index) => {
                  const t = index / 19;
                  return (
                    <stop
                      key={index}
                      offset={`${t * 100}%`}
                      stopColor={colorScale(t * maxCount)}
                    />
                  );
                })}
              </linearGradient>
            </defs>

            {showDensity && densityContours.length > 0
              ? densityContours.map((contour, i) => {
                  const key = `contour-${Math.round(contour.value)}-${i}`;
                  return (
                    <path
                      key={key}
                      d={d3.geoPath()(contour)!}
                      fill={colorScale(contour.value)}
                      stroke="none"
                      opacity={0.9}
                    />
                  );
                })
              : filteredPitches.map((p, i) => {
                  const key = `${p.batterSide}-${p.pitchType}-${p.x.toFixed(3)}-${p.y.toFixed(3)}-${i}`;
                  return (
                    <circle
                      key={key}
                      cx={svgX(p.x)}
                      cy={svgY(p.y)}
                      r={4}
                      fill={pitchColors[p.pitchType] || 'gray'}
                      opacity={0.7}
                    />
                  );
                })}

            <rect
              x={svgX(-strikeZoneHalfWidth)}
              y={svgY(strikeZoneTop)}
              width={svgX(strikeZoneHalfWidth) - svgX(-strikeZoneHalfWidth)}
              height={svgY(strikeZoneBottom) - svgY(strikeZoneTop)}
              stroke="black"
              fill="none"
              strokeWidth={2}
            />

            {[1, 2].map((i) => {
              const frac = i / 3;
              return (
                <g key={i}>
                  <line
                    x1={svgX(-strikeZoneHalfWidth + frac * (strikeZoneHalfWidth * 2))}
                    y1={svgY(strikeZoneTop)}
                    x2={svgX(-strikeZoneHalfWidth + frac * (strikeZoneHalfWidth * 2))}
                    y2={svgY(strikeZoneBottom)}
                    stroke="gray"
                    strokeWidth={0.5}
                  />
                  <line
                    x1={svgX(-strikeZoneHalfWidth)}
                    y1={svgY(strikeZoneBottom + frac * (strikeZoneTop - strikeZoneBottom))}
                    x2={svgX(strikeZoneHalfWidth)}
                    y2={svgY(strikeZoneBottom + frac * (strikeZoneTop - strikeZoneBottom))}
                    stroke="gray"
                    strokeWidth={0.5}
                  />
                </g>
              );
            })}

            <polygon
              points={`
                ${svgX(-0.354)},${svgY(0)}
                ${svgX(0.354)},${svgY(0)}
                ${svgX(0.3)},${svgY(-0.2)}
                ${svgX(0)},${svgY(-0.354)}
                ${svgX(-0.3)},${svgY(-0.2)}
              `}
              fill="white"
              stroke="black"
              strokeWidth="1.5"
            />

            {[0, 1, 2, 3, 4, 5].map((tick) => (
              <text
                key={`y-${tick}`}
                x={padding - 10}
                y={svgY(tick)}
                fontSize="10"
                textAnchor="end"
                alignmentBaseline="middle"
                fill="#444"
              >
                {tick.toFixed(1)}
              </text>
            ))}

            {[-1, -0.5, 0, 0.5, 1].map((tick) => (
              <text
                key={`x-${tick}`}
                x={svgX(tick)}
                y={height - padding + 15}
                fontSize="10"
                textAnchor="middle"
                fill="#444"
              >
                {tick}
              </text>
            ))}

            <text
              x={15}
              y={height / 2}
              fontSize="10"
              transform={`rotate(-90 15,${height / 2})`}
              textAnchor="middle"
              fill="#444"
            >
              Height Above Ground
            </text>
            <text x={width / 2} y={height - 5} fontSize="10" textAnchor="middle" fill="#444">
              Horizontal Location
            </text>

            {showDensity && (
              <>
                <rect
                  x={width + 30}
                  y={padding}
                  width={20}
                  height={height - 2 * padding}
                  fill="url(#color-gradient)"
                />
                <text x={width + 55} y={padding + 8} fontSize="10" fill="#444" textAnchor="start">
                  {maxCount}
                </text>
                <text
                  x={width + 55}
                  y={height - padding}
                  fontSize="10"
                  fill="#444"
                  textAnchor="start"
                >
                  0
                </text>
              </>
            )}
          </svg>
        </Box>
      </Box>

      <Box mt={3}>
        {!showDensity && (
          <>
            <Typography variant="subtitle1" fontWeight={500}>
              Pitch Type Legend
            </Typography>
            <Grid container spacing={1} justifyContent="center" mt={1}>
              {Object.entries(pitchColors).map(([type, color]) => (
                <Grid key={type}>
                  <Chip label={type} style={{ backgroundColor: color, color: 'white' }} />
                </Grid>
              ))}
            </Grid>
          </>
        )}

        <Typography
          variant="body1"
          fontWeight={600}
          mt={3}
          sx={{ width: '100%', textAlign: 'center' }}
        >
          Total Pitches: {filteredPitches.length.toLocaleString()}
        </Typography>
      </Box>
    </Box>
  );
}
