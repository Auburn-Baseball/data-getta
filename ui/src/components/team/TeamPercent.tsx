// src/components/team/TeamPercent.tsx
import {
  Box,
  Typography,
  LinearProgress,
  Stack,
  Divider,
  ToggleButtonGroup,
  ToggleButton,
} from '@mui/material';
import { useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router';

export interface Row {
  team: string;
  label: string;
  raw_value: number | string;
  percentile: number | string;
}

// NEW: Mode toggle (overall vs wl)
function ModeToggle({ mode }: { mode: 'overall' | 'wl' }) {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const setMode = (m: 'overall' | 'wl') => {
    const next = new URLSearchParams(params);
    next.set('mode', m);
    navigate({ search: `?${next.toString()}` }, { replace: false });
  };
  return (
    <ToggleButtonGroup
      exclusive
      size="small"
      value={mode}
      onChange={(_, val) => val && setMode(val)}
      sx={{ ml: 2 }}
    >
      <ToggleButton value="overall">Overall</ToggleButton>
      <ToggleButton value="wl">W/L</ToggleButton>
    </ToggleButtonGroup>
  );
}

// ---------- helpers ----------
const norm = (s: string) => s.replace(/\s+/g, ' ').trim().toUpperCase();
const asNum = (x: number | string | null | undefined) =>
  x == null ? NaN : typeof x === 'number' ? x : Number(x);

const getBarColor = (value: number) => {
  if (value >= 90) return '#c62828';
  if (value >= 75) return '#ef5350';
  if (value >= 50) return '#ffa726';
  if (value >= 30) return '#ffeb3b';
  return '#90caf9';
};

const offensiveSet = new Set(['AVG', 'OBP', 'SLG', 'OPS'].map(norm));
const defensiveSet = new Set(['ERA', 'FIP', 'K/9', 'BB/9', 'OPPONENT BA'].map(norm));

const formatRaw = (label: string, v: number | string) => {
  if (typeof v !== 'number') return v;
  const L = norm(label);
  if (['AVG', 'OBP', 'SLG', 'OPS', 'OPPONENT BA'].includes(L)) return v.toFixed(3);
  if (['ERA', 'K/9', 'BB/9', 'FIP'].includes(L)) return v.toFixed(2);
  return String(v);
};

export default function CreateTeamPercent({
  seasonLabel,
  rows,
  mode,
}: {
  seasonLabel: string;
  rows: Row[];
  mode: 'overall' | 'wl';
}) {
  // Empty state if no rows (e.g., W/L mode for now)
  const hasData = rows && rows.length > 0;

  // Group rows by team code
  const groupedByTeam = useMemo(() => {
    return rows.reduce(
      (acc, row) => {
        (acc[row.team] ||= []).push(row);
        return acc;
      },
      {} as Record<string, Row[]>,
    );
  }, [rows]);

  // Rank teams by average percentile
  const rankedTeams = useMemo(() => {
    return Object.entries(groupedByTeam)
      .map(([team, stats]) => {
        const nums = stats.map((s) => asNum(s.percentile)).filter((v) => Number.isFinite(v));
        const avg = nums.length ? nums.reduce((a, b) => a + b, 0) / nums.length : 0;
        return { team, average: avg };
      })
      .sort((a, b) => b.average - a.average);
  }, [groupedByTeam]);

  const top10 = rankedTeams.slice(0, 10);
  const [first, second, third] = top10.slice(0, 3);
  const restRanked = top10.slice(3);

  const teamVisualOrder = useMemo(() => {
    const top10Teams = top10.map((t) => t.team);
    return top10Teams.includes('AUB_TIG')
      ? ['AUB_TIG', ...top10Teams.filter((t) => t !== 'AUB_TIG')]
      : top10Teams;
  }, [top10]);

  const renderStatBars = (category: Row[], prefix: string) =>
    category.map((stat, i) => {
      const p = asNum(stat.percentile);
      const pSafe = Number.isFinite(p) ? p : 0;
      const pRounded = Math.round(pSafe);
      return (
        <Box key={`${prefix}-${stat.label}-${i}`}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography>{stat.label}</Typography>
            <Typography fontWeight={600}>{formatRaw(stat.label, stat.raw_value)}</Typography>
          </Box>
          <Box sx={{ position: 'relative' }}>
            <LinearProgress
              variant="determinate"
              value={pSafe}
              sx={{
                height: 16,
                borderRadius: 8,
                backgroundColor: '#e0e0e0',
                '& .MuiLinearProgress-bar': { backgroundColor: getBarColor(pSafe) },
              }}
            />
            <Box
              sx={{
                position: 'absolute',
                top: '50%',
                left: `${pSafe}%`,
                transform: 'translate(-50%, -50%)',
                bgcolor: getBarColor(pSafe),
                color: 'white',
                width: 28,
                height: 28,
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 600,
                fontSize: 12,
                border: '2px solid white',
              }}
            >
              {pRounded}
            </Box>
          </Box>
        </Box>
      );
    });

  return (
    <Box sx={{ px: 8, py: 4, color: '#0b2341' }}>
      {/* Filters row (mode only; page handles title and season) */}
      <Box display="flex" justifyContent="center" alignItems="center" mt={1} mb={3}>
        <ModeToggle mode={mode} />
      </Box>

      {!hasData ? (
        <Box sx={{ textAlign: 'center', py: 10 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            No data to show yet
          </Typography>
          <Typography variant="body2">TODO: Implement a W/L leaderboard</Typography>
        </Box>
      ) : (
        <>
          {/* 🏆 Podium */}
          <Box sx={{ mt: 1, textAlign: 'center' }}>
            <Typography variant="h6" fontWeight={600} mb={2}>
              Top Performing Teams
            </Typography>
            <Box display="flex" justifyContent="center" alignItems="end" gap={0}>
              {[second, first, third].map((team, idx) => {
                if (!team) return null;
                return (
                  <Box key={team.team} textAlign="center" width={120}>
                    <Typography fontSize={22}>{['🥈', '🥇', '🥉'][idx]}</Typography>
                    <Box sx={{ height: [100, 140, 80][idx], bgcolor: '#0b2341' }}>
                      <Box sx={{ height: [80, 120, 60][idx] }} />
                    </Box>
                    <Typography fontSize={13} fontWeight={idx === 1 ? 700 : 600}>
                      {team.team}
                    </Typography>
                    <Typography fontSize={11}>{team.average.toFixed(1)}%</Typography>
                  </Box>
                );
              })}
            </Box>
          </Box>

          {/* 📋 Full Rankings (Top-10 only) */}
          {restRanked.length > 0 && (
            <Box sx={{ textAlign: 'center', mb: 6, maxWidth: 400, mx: 'auto' }}>
              <Typography variant="h6" fontWeight={600} mb={2}>
                Full Rankings
              </Typography>
              <Box
                component="table"
                sx={{
                  width: '100%',
                  borderCollapse: 'collapse',
                  fontSize: 14,
                  color: 'white',
                  backgroundColor: '#1c2a45',
                  borderRadius: 2,
                  overflow: 'hidden',
                }}
              >
                <thead>
                  <tr>
                    <th
                      style={{ textAlign: 'left', padding: '8px 12px', backgroundColor: '#233954' }}
                    >
                      #
                    </th>
                    <th
                      style={{ textAlign: 'left', padding: '8px 12px', backgroundColor: '#233954' }}
                    >
                      Team
                    </th>
                    <th
                      style={{
                        textAlign: 'right',
                        padding: '8px 12px',
                        backgroundColor: '#233954',
                      }}
                    >
                      Avg %
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {restRanked.map((team, idx) => (
                    <tr key={team.team} style={{ borderBottom: '1px solid #2c3e50' }}>
                      <td style={{ padding: '8px 12px' }}>{idx + 4}.</td>
                      <td style={{ padding: '8px 12px' }}>{team.team}</td>
                      <td style={{ padding: '8px 12px', textAlign: 'right' }}>
                        {team.average.toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Box>
            </Box>
          )}

          {/* 📈 Team Visual Stats */}
          {teamVisualOrder.map((teamCode) => {
            const stats = groupedByTeam[teamCode];
            if (!stats) return null;
            const offensive = stats.filter((s) => offensiveSet.has(norm(s.label)));
            const defensive = stats.filter((s) => defensiveSet.has(norm(s.label)));
            return (
              <Box key={teamCode} sx={{ mt: 6 }}>
                <Typography variant="h5" fontWeight={700} gutterBottom>
                  {teamCode}
                </Typography>
                {offensive.length > 0 && (
                  <>
                    <Typography variant="h6" fontWeight={600} gutterBottom mt={1}>
                      Offensive Stats
                    </Typography>
                    <Stack spacing={2}>{renderStatBars(offensive, `off-${teamCode}`)}</Stack>
                  </>
                )}
                {defensive.length > 0 && (
                  <>
                    <Typography variant="h6" fontWeight={600} gutterBottom mt={3}>
                      Defensive Stats
                    </Typography>
                    <Stack spacing={2}>{renderStatBars(defensive, `def-${teamCode}`)}</Stack>
                  </>
                )}
                <Divider sx={{ mt: 4, bgcolor: 'white', opacity: 0.2 }} />
              </Box>
            );
          })}
        </>
      )}
    </Box>
  );
}
