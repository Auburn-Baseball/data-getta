import React, { useEffect, useState } from "react";
import StatBar from "@/components/player/StatBar";
import { useParams } from "react-router";
import { supabase } from "@/utils/supabase/client";

const boxStyle: React.CSSProperties = {
  flex: 1,
  minHeight: "400px",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  margin: "0 12px",
};

// ------------------------------------------------------
// Infield Spray Chart Component
// ------------------------------------------------------
const InfieldSprayChart: React.FC<{ stats: any }> = ({ stats }) => {
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
    if (maxPercent === 0) return "rgb(255,255,255)";
    const intensity = percent / 50; // 50% maps to full red
    const red = 255;
    const green = Math.round(255 * (1 - intensity));
    const blue = Math.round(255 * (1 - intensity));
    return `rgb(${red},${green},${blue})`;
  };

  const slices = [
    { label: "Left", percent: percents[0] ?? 0 },
    { label: "Left-Center", percent: percents[1] ?? 0 },
    { label: "Center", percent: percents[2] ?? 0 },
    { label: "Right-Center", percent: percents[3] ?? 0 },
    { label: "Right", percent: percents[4] ?? 0 },
  ];

  return (
    <svg
      viewBox="-150 -50 300 200"
      style={{
        width: "100%",
        maxWidth: 400,
        margin: "auto",
        transform: "scale(1, -1)", // flip vertically (faces up)
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
  );
};




// ------------------------------------------------------
// Main PercentilesTab Component
// ------------------------------------------------------
const PercentilesTab: React.FC = () => {
  const { trackmanAbbreviation, playerName, year } = useParams<{
    trackmanAbbreviation: string;
    playerName: string;
    year: string;
  }>();

  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchStats() {
      setLoading(true);
      setError(null);

      try {
        const safeYear = year || "2025";
        const formattedPlayerName = playerName
          ? decodeURIComponent(playerName).replace("_", ", ")
          : "";
        const decodedTeamName = trackmanAbbreviation
          ? decodeURIComponent(trackmanAbbreviation)
          : "";

        const { data: allBatters, error } = await supabase
          .from("AdvancedBattingStats")
          .select("*")
          .eq("BatterTeam", decodedTeamName)
          .eq("Year", safeYear);

        if (error) throw error;

        const playerStats = allBatters.find(
          (b: any) => b.Batter === formattedPlayerName
        );
        setStats(playerStats);
      } catch (err: any) {
        console.error(err);
        setError("Failed to load player stats");
      } finally {
        setLoading(false);
      }
    }

    fetchStats();
  }, [trackmanAbbreviation, playerName, year]);

  const getRankColor = (rank: number): string => {
    const r = Math.max(0, Math.min(rank, 100));
    const blueRGB = { r: 0, g: 123, b: 255 };
    const greyRGB = { r: 153, g: 153, b: 153 };
    const t = Math.abs(r - 50) / 50;
    const rVal = Math.round(greyRGB.r + t * (blueRGB.r - greyRGB.r));
    const gVal = Math.round(greyRGB.g + t * (blueRGB.g - greyRGB.g));
    const bVal = Math.round(greyRGB.b + t * (blueRGB.b - greyRGB.b));
    return `rgb(${rVal},${gVal},${bVal})`;
  };

  return (
    <div
      style={{
        display: "flex",
        width: "100%",
        maxWidth: 1200,
        margin: "40px auto",
        gap: 24,
      }}
    >
      {/* ✅ Center: Advanced Stats */}
      <div style={boxStyle}>
        <div style={{ width: "100%", maxWidth: 400 }}>
          <h2 style={{ textAlign: "center", marginBottom: 24 }}>
            Advanced Stats
          </h2>
          {loading ? (
            <div style={{ textAlign: "center", padding: 32 }}>Loading...</div>
          ) : error ? (
            <div
              style={{ color: "#d32f2f", textAlign: "center", padding: 32 }}
            >
              {error}
            </div>
          ) : stats ? (
            <div>
              {[
                { key: "avg_exit_velo", label: "EV" },
                { key: "k_per", label: "K%" },
                { key: "bb_per", label: "BB%" },
                { key: "la_sweet_spot_per", label: "LA Sweet Spot %" },
                { key: "hard_hit_per", label: "Hard Hit %" },
                { key: "whiff_per", label: "Whiff %" },
                { key: "chase_per", label: "Chase %" },
              ].map(({ key, label }) => {
                const rankKey = `${key}_rank`;
                let rank =
                  typeof stats[rankKey] === "number" ? stats[rankKey] : 1;

                rank = Math.round(rank);

                const statValue =
                  typeof stats[key] === "number"
                    ? key.endsWith("per") || key === "k_per" || key === "bb_per"
                      ? `${(stats[key] * 100).toFixed(1)}%`
                      : stats[key].toFixed(1)
                    : "0.0";

                return (
                  <StatBar
                    key={key}
                    statName={label}
                    percentile={rank}
                    color={getRankColor(rank)}
                    statValue={statValue}
                  />
                );
              })}
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: 32 }}>
              No Data Available
            </div>
          )}
        </div>
      </div>

      {/* ✅ Right: Flipped Infield Spray Chart */}
      <div style={boxStyle}>
        {!loading && stats ? (
          <div style={{ textAlign: "center" }}>
            <h2 style={{ marginBottom: 16 }}>Infield Spray Chart</h2>
            <InfieldSprayChart stats={stats} />
          </div>
        ) : (
          <div style={{ textAlign: "center", padding: 32 }}>Loading chart...</div>
        )}
      </div>
    </div>
  );
};

export default PercentilesTab;
