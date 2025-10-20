import React from 'react';

interface StatBarProps {
  statName: string;
  percentile: number; // 1-99
  statValue: number | string;
  color?: string;
}

function getBarColor(percentile: number) {
  const p = Math.max(0, Math.min(percentile, 100));

  const lowBlue = { r: 0, g: 0, b: 255 }; // dark blue
  const highBlue = { r: 204, g: 229, b: 255 }; // light blue

  const lowRed = { r: 255, g: 204, b: 204 }; // light red
  const highRed = { r: 204, g: 0, b: 0 }; // bright red

  let r, g, b;

  if (p < 50) {
    const t = p / 50; // interpolate 0 → 50
    r = Math.round(lowBlue.r + t * (highBlue.r - lowBlue.r));
    g = Math.round(lowBlue.g + t * (highBlue.g - lowBlue.g));
    b = Math.round(lowBlue.b + t * (highBlue.b - lowBlue.b));
  } else {
    const t = (p - 50) / 50; // interpolate 51 → 100
    r = Math.round(lowRed.r + t * (highRed.r - lowRed.r));
    g = Math.round(lowRed.g + t * (highRed.g - lowRed.g));
    b = Math.round(lowRed.b + t * (highRed.b - lowRed.b));
  }

  return `rgb(${r},${g},${b})`;
}

const StatBar: React.FC<StatBarProps> = ({ statName, percentile, statValue }) => {
  const barColor = getBarColor(percentile);
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        minHeight: 28,
        marginBottom: 4,
        position: 'relative',
      }}
    >
      <div
        style={{
          width: 140,
          textAlign: 'right',
          fontWeight: 500,
          fontSize: 13,
          color: '#374151',
          paddingRight: 10,
          letterSpacing: 0.2,
        }}
      >
        {statName}
      </div>
      <div
        style={{
          flex: 1,
          height: 22,
          background: '#e3e8ee',
          borderRadius: 4,
          position: 'relative',
          marginRight: 16,
          marginLeft: 0,
          minWidth: 180,
          maxWidth: 400,
        }}
      >
        <div
          style={{
            width: `${percentile}%`,
            height: '100%',
            background: barColor,
            borderRadius: 4,
            position: 'absolute',
            left: 0,
            top: 0,
            transition: 'width 0.4s',
          }}
        />
        <div
          style={{
            position: 'absolute',
            right: `${Math.max(0, 100 - percentile)}%`,
            top: '50%',
            transform: 'translate(50%, -50%)',
            background: barColor,
            color: '#fff',
            borderRadius: '50%',
            width: 22,
            height: 22,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 700,
            fontSize: 12,
            boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
            border: `2px solid ${barColor}`,
          }}
        >
          {percentile}
        </div>
      </div>
      <div
        style={{
          width: 70,
          textAlign: 'left',
          fontWeight: 500,
          fontSize: 13,
          color: '#374151',
          paddingLeft: 10,
          letterSpacing: 0.2,
        }}
      >
        {statValue}
      </div>
    </div>
  );
};

export default StatBar;
