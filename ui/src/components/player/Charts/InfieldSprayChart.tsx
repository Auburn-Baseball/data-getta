import { Box } from '@mui/material';
import { AdvancedBattingStatsTable } from '@/types/db';
import fieldImage from '@/assets/plainsman-park.png'; // adjust path as needed

type InfieldSprayChartProps = {
  stats: AdvancedBattingStatsTable;
};

export default function InfieldSprayChart({ stats }: InfieldSprayChartProps) {
  if (!stats) return null;

  const counts = [
    stats.infield_left_slice ?? 0,
    stats.infield_lc_slice ?? 0,
    stats.infield_center_slice ?? 0,
    stats.infield_rc_slice ?? 0,
    stats.infield_right_slice ?? 0,
  ];

  const total = counts.reduce((a, b) => a + b, 0);
  const percents = total > 0 ? counts.map((c) => (c / total) * 100) : counts;
  const maxPercent = Math.max(...percents, 0);

  const getColor = (percent: number) => {
    if (maxPercent === 0) return 'rgba(255,255,255,0.5)'; // fallback transparent white
    const intensity = percent / 50;
    const red = 255;
    const green = Math.round(255 * (1 - intensity));
    const blue = Math.round(255 * (1 - intensity));
    return `rgba(${red},${green},${blue},0.8)`; // 0.8 = 20% transparent
  };

  const slices = [
    { label: 'Left', percent: percents[0] ?? 0 },
    { label: 'Left-Center', percent: percents[1] ?? 0 },
    { label: 'Center', percent: percents[2] ?? 0 },
    { label: 'Right-Center', percent: percents[3] ?? 0 },
    { label: 'Right', percent: percents[4] ?? 0 },
  ];

  return (
    <Box
      sx={{
        position: 'relative',
        width: '100%',
        maxWidth: 400,
        mx: 'auto',
        aspectRatio: '1 / 1',
        overflow: 'hidden', // clip anything outside the box
      }}
    >
      {/* Cropped Field Image */}
      <Box
        component="img"
        src={fieldImage}
        alt="Plainsman Park"
        sx={{
          width: '100%',
          height: '110%',        // double the height so top half fits in container
          objectFit: 'cover',
          transform: 'translateY(-12.9%) translateX(-0.4%)', // show the top half
          display: 'block',
        }}
      />


      {/* Overlay Spray Chart */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          pointerEvents: 'none',
        }}
      >
        <svg
          viewBox="-150 -50 300 200"
          style={{
            width: '100%',
            height: '100%',
            transform: 'scale(1, -1) rotate(0.75deg)', // rotate 1 degree counterclockwise
            transformOrigin: '50% 50%', // rotate around the center',
          }}
        >
          {slices.map((slice, i) => {
            const totalAngle = 87.5; // new total arc
            const sliceAngle = totalAngle / slices.length; // ~17.6°
            
            const startAngle = -totalAngle / 2 + i * sliceAngle; // center at 0
            const endAngle = startAngle + sliceAngle;
            const radius = 120;
            const largeArc = endAngle - startAngle > 180 ? 1 : 0;

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
                  transform="scale(1, -1)"
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
          <circle cx="0" cy="0" r="0" fill="#333" transform="scale(1, -1)" />
        </svg>
      </Box>
    </Box>
  );
}
