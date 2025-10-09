import React from "react";

interface StatBarProps {
  statName: string;
  percentile: number; // 1-99
  statValue: number | string;
  color?: string;
}


// Helper to interpolate between blue and red based on percentile
function getBarColor(percentile: number) {
  // 1% = blue (#1976d2), 99% = red (#c62828)
  const percent = (percentile - 1) / 98;
  const r1 = 25, g1 = 118, b1 = 210; // blue
  const r2 = 198, g2 = 40, b2 = 40; // red
  const r = Math.round(r1 + (r2 - r1) * percent);
  const g = Math.round(g1 + (g2 - g1) * percent);
  const b = Math.round(b1 + (b2 - b1) * percent);
  return `rgb(${r},${g},${b})`;
}

const StatBar: React.FC<StatBarProps> = ({ statName, percentile, statValue }) => {
  const barColor = getBarColor(percentile);
        return (
          <div style={{
            display: "flex",
            alignItems: "center",
            minHeight: 28,
            marginBottom: 4,
            position: "relative"
          }}>
            <div style={{
              width: 140,
              textAlign: "right",
              fontWeight: 500,
              fontSize: 13,
              color: "#374151",
              paddingRight: 10,
              letterSpacing: 0.2
            }}>{statName}</div>
            <div style={{
              flex: 1,
              height: 22,
              background: "#e3e8ee",
              borderRadius: 4,
              position: "relative",
              marginRight: 16,
              marginLeft: 0,
              minWidth: 180,
              maxWidth: 400
            }}>
              <div
                style={{
                  width: `${percentile}%`,
                  height: "100%",
                  background: barColor,
                  borderRadius: 4,
                  position: "absolute",
                  left: 0,
                  top: 0,
                  transition: "width 0.4s",
                }}
              />
              <div
                style={{
                  position: "absolute",
                  right: `${Math.max(0, 100 - percentile)}%`,
                  top: "50%",
                  transform: "translate(50%, -50%)",
                  background: barColor,
                  color: "#fff",
                  borderRadius: "50%",
                  width: 22,
                  height: 22,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontWeight: 700,
                  fontSize: 12,
                  boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
                  border: `2px solid ${barColor}`,
                }}
              >
                {percentile}
              </div>
            </div>
            <div style={{
              width: 70,
              textAlign: "left",
              fontWeight: 500,
              fontSize: 13,
              color: "#374151",
              paddingLeft: 10,
              letterSpacing: 0.2
            }}>{statValue}</div>
          </div>
        );
};

export default StatBar;
