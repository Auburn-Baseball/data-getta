import { Box } from '@mui/material';
import { AdvancedBattingStatsTable } from '@/types/db';

type InfieldSprayChartProps = {
  stats: AdvancedBattingStatsTable;
};

export default function InfieldSprayChart({ stats }: InfieldSprayChartProps) {
  if (!stats) return null;

  // Calculate total and per-slice counts
  const counts = [
    stats.infield_left_slice ?? 0,
    stats.infield_lc_slice ?? 0,
    stats.infield_center_slice ?? 0,
    stats.infield_rc_slice ?? 0,
    stats.infield_right_slice ?? 0,
  ];

  const total = counts.reduce((a, b) => a + b, 0);
  const percents = total > 0 ? counts.map((c) => (c / total) * 100) : counts;

  // Find max % (for scaling)
  const maxPercent = Math.max(...percents, 0);

  // White → red gradient
  const getColor = (percent: number) => {
    if (maxPercent === 0) return 'rgb(255,255,255)';
    const intensity = percent / 50; // 50% maps to full red
    const red = 255;
    const green = Math.round(255 * (1 - intensity));
    const blue = Math.round(255 * (1 - intensity));
    return `rgb(${red},${green},${blue})`;
  };

  const slices = [
    { label: 'Left', percent: percents[0] ?? 0 },
    { label: 'Left-Center', percent: percents[1] ?? 0 },
    { label: 'Center', percent: percents[2] ?? 0 },
    { label: 'Right-Center', percent: percents[3] ?? 0 },
    { label: 'Right', percent: percents[4] ?? 0 },
  ];

  return (
    <Box sx={{ width: '100%', maxWidth: 400, mx: 'auto' }}>
      <svg
        viewBox="-150 -50 300 200"
        style={{
          width: '100%',
          margin: 'auto',
          transform: 'scale(1, -1)', // flip vertically (faces up)
        }}
      >
        {slices.map((slice, i) => {
          const startAngle = -45 + i * 18;
          const endAngle = startAngle + 18;
          const largeArc = endAngle - startAngle > 180 ? 1 : 0;
          const radius = 120;

          const x1 = radius * Math.sin((Math.PI / 180) * startAngle);
          const y1 = radius * Math.cos((Math.PI / 180) * startAngle);
          const x2 = radius * Math.sin((Math.PI / 180) * endAngle);
          const y2 = radius * Math.cos((Math.PI / 180) * endAngle);

          const d = `M 0 0 L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`;

          const color = getColor(slice.percent);
          const label = `${slice.percent.toFixed(0)}%`;

          const midAngle = (startAngle + endAngle) / 2;
          const labelX = (radius + 15) * Math.sin((Math.PI / 180) * midAngle);
          const labelY = (radius + 15) * Math.cos((Math.PI / 180) * midAngle);

          return (
            <g key={slice.label}>
              <path d={d} fill={color} stroke="#333" strokeWidth="1" />
              <text
                transform={`scale(1, -1)`}
                x={labelX}
                y={-labelY}
                textAnchor="middle"
                alignmentBaseline="middle"
                fontSize="12"
                fill="#222"
                fontWeight="bold"
              >
                {label}
              </text>
            </g>
          );
        })}

        {/* Home plate marker */}
        <circle cx="0" cy="0" r="4" fill="#333" transform="scale(1, -1)" />
      </svg>
    </Box>
  );
}
