import React, { useEffect, useState } from 'react';
import StatBar from '@/components/player/StatBar';
import { useParams } from 'react-router';
import { supabase } from '@/utils/supabase/client';

const boxStyle: React.CSSProperties = {
  flex: 1,
  minHeight: '400px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  margin: '0 12px',
};

const advancedStatKeys = [
  { key: 'avg_exit_velo', label: 'EV' },
  { key: 'k_per', label: 'K%' },
  { key: 'bb_per', label: 'BB%' },
  { key: 'la_sweet_spot_per', label: 'LA Sweet Spot %' },
  { key: 'hard_hit_per', label: 'Hard Hit %' },
];

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
        const safeYear = year || '2025';
        const formattedPlayerName = playerName
          ? decodeURIComponent(playerName).replace('_', ', ')
          : '';
        const decodedTeamName = trackmanAbbreviation
          ? decodeURIComponent(trackmanAbbreviation)
          : '';

        console.log('Fetching stats for:', formattedPlayerName, decodedTeamName, safeYear);

        const { data: allBatters, error } = await supabase
          .from('AdvancedBattingStats')
          .select('*')
          .eq('BatterTeam', decodedTeamName)
          .eq('Year', safeYear);

        if (error) throw error;

        const playerStats = allBatters.find((b: any) => b.Batter === formattedPlayerName);

        console.log('Player stats fetched:', playerStats);

        setStats(playerStats);
      } catch (err: any) {
        console.error(err);
        setError('Failed to load player stats');
      } finally {
        setLoading(false);
      }
    }

    fetchStats();
  }, [trackmanAbbreviation, playerName, year]);

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
          <h2 style={{ textAlign: 'center', marginBottom: 24 }}>Advanced Stats</h2>
          {loading ? (
            <div style={{ textAlign: 'center', padding: 32 }}>Loading...</div>
          ) : error ? (
            <div style={{ color: '#d32f2f', textAlign: 'center', padding: 32 }}>{error}</div>
          ) : stats ? (
            <div>
              {advancedStatKeys.map(({ key, label }) => {
                const rankKey = `${key}_rank`;
                const rank = typeof stats[rankKey] === 'number' ? stats[rankKey] : 1;

                return (
                  <StatBar
                    key={key}
                    statName={label}
                    percentile={Math.round(rank)}
                    color={getRankColor(Math.round(rank))}
                    statValue={
                      typeof stats[key] === 'number'
                        ? key.endsWith('per') || key === 'k_per' || key === 'bb_per'
                          ? `${(stats[key] * 100).toFixed(1)}%`
                          : stats[key]
                        : '-'
                    }
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
