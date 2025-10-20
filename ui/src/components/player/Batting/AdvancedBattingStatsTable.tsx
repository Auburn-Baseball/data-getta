import React, { useEffect, useState } from 'react';
import { useOutletContext, useParams } from 'react-router';

import StatBar from '@/components/player/StatBar';
import { fetchAdvancedBattingStats } from '@/services/playerService';
import type { AdvancedBattingStatsTable } from '@/types/db';
import type { DateRange } from '@/types/dateRange';
import { formatYearRange } from '@/utils/dateRange';

const boxStyle: React.CSSProperties = {
  flex: 1,
  minHeight: '400px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  margin: '0 12px',
};

const advancedStatKeys: Array<{
  key: keyof AdvancedBattingStatsTable;
  label: string;
}> = [
  { key: 'avg_exit_velo', label: 'EV' },
  { key: 'k_per', label: 'K%' },
  { key: 'bb_per', label: 'BB%' },
  { key: 'la_sweet_spot_per', label: 'LA Sweet Spot %' },
  { key: 'hard_hit_per', label: 'Hard Hit %' },
];

const PercentilesTab: React.FC = () => {
  const { trackmanAbbreviation, playerName } = useParams<{
    trackmanAbbreviation: string;
    playerName: string;
  }>();
  const dateRange = useOutletContext<DateRange>();
  const seasonLabel = formatYearRange(dateRange);

  const [stats, setStats] = useState<AdvancedBattingStatsTable | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchStats() {
      setLoading(true);
      setError(null);

      try {
        const formattedPlayerName = playerName
          ? decodeURIComponent(playerName).replace('_', ', ')
          : '';
        const decodedTeamName = trackmanAbbreviation
          ? decodeURIComponent(trackmanAbbreviation)
          : '';

        console.log('Fetching stats for:', formattedPlayerName, decodedTeamName, dateRange);

        const { data: allBatters, error } = await fetchAdvancedBattingStats(
          decodedTeamName,
          dateRange,
        );

        if (error) throw error;

        const playerStats = allBatters?.find((b) => b.Batter === formattedPlayerName) ?? null;

        console.log('Player stats fetched:', playerStats);

        setStats(playerStats as AdvancedBattingStatsTable | null);
      } catch (error: unknown) {
        console.error(error);
        setError('Failed to load player stats');
      } finally {
        setLoading(false);
      }
    }

    fetchStats();
  }, [dateRange, trackmanAbbreviation, playerName]);

  // Compute color based on rank
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
        display: 'flex',
        width: '100%',
        maxWidth: 1200,
        margin: '40px auto',
        gap: 24,
      }}
    >
      <div style={boxStyle}></div>
      <div style={boxStyle}>
        <div style={{ width: '100%', maxWidth: 400 }}>
          <h2 style={{ textAlign: 'center', marginBottom: 24 }}>Advanced Stats ({seasonLabel})</h2>
          {loading ? (
            <div style={{ textAlign: 'center', padding: 32 }}>Loading...</div>
          ) : error ? (
            <div style={{ color: '#d32f2f', textAlign: 'center', padding: 32 }}>{error}</div>
          ) : stats ? (
            <div>
              {advancedStatKeys.map(({ key, label }) => {
                const rankKey = `${key}_rank` as keyof AdvancedBattingStatsTable;
                const rankValue = stats[rankKey];
                const rank = typeof rankValue === 'number' ? rankValue : 1;
                const rawValue = stats[key];
                let statValue: string | number = '-';

                if (typeof rawValue === 'number') {
                  if (key.endsWith('per') || key === 'k_per' || key === 'bb_per') {
                    statValue = `${(rawValue * 100).toFixed(1)}%`;
                  } else {
                    statValue = rawValue;
                  }
                }

                return (
                  <StatBar
                    key={key}
                    statName={label}
                    percentile={Math.round(rank)}
                    color={getRankColor(Math.round(rank))}
                    statValue={statValue}
                  />
                );
              })}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: 32 }}>No Data Available</div>
          )}
        </div>
      </div>
      <div style={boxStyle}></div>
    </div>
  );
};

export default PercentilesTab;
