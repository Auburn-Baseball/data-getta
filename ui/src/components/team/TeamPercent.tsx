// src/components/team/TeamPercent.tsx
import { Box, Typography, LinearProgress, Stack, Divider, FormControl, Select, MenuItem } from '@mui/material';
import { useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router';

export interface Row {
  team: string;        // e.g., "Auburn" or "AUB_TIG" — whatever you're storing
  label: string;       // e.g., "AVG", "OBP", "ERA", etc.
  raw_value: number | string; // number preferred; string is OK (we just display it)
  percentile: number;  // 0..100
}

function YearDropdown({ year }: { year: string }) {
  const navigate = useNavigate();
  const [params] = useSearchParams();

  const setYear = (y: string) => {
    const next = new URLSearchParams(params);
    next.set('year', y);
    navigate({ search: `?${next.toString()}` }, { replace: false });
  };

  return (
    <FormControl size="small" sx={{ minWidth: 140 }}>
      <Select value={year} onChange={(e) => setYear(String(e.target.value))}>
        <MenuItem value="2024">2024</MenuItem>
        <MenuItem value="2025">2025</MenuItem>
      </Select>
    </FormControl>
  );
}

// If you ever need to invert some metrics (e.g., lower is better), do it here.
// Your SQL/view already bakes the percentiles correctly, so just return as-is.
const getAdjustedPercentile = (_label: string, percentile: number) => percentile;

const getBarColor = (value: number) => {
  if (value >= 90) return '#c62828';
  if (value >= 75) return '#ef5350';
  if (value >= 50) return '#ffa726';
  if (value >= 30) return '#ffeb3b';
  return '#90caf9';
};

const offensiveLabels = ['AVG', 'OBP', 'SLG', 'OPS', 'Runs/Game'];
const defensiveLabels = ['ERA', 'FIP', 'K/9', 'BB/9', 'Opponent BA'];

export default function CreateTeamPercent({ year, rows }: { year: string; rows: Row[] }) {
  // group rows by team
  const groupedByTeam = useMemo(() => {
    return rows.reduce((acc, row) => {
      (acc[row.team] ||= []).push(row);
      return acc;
    }, {} as Record<string, Row[]>);
  }, [rows]);

  // compute average percentile per team & sort desc
  const rankedTeams = useMemo(() => {
    return Object.entries(groupedByTeam)
      .map(([team, stats]) => {
        const avg =
          stats.reduce((sum, s) => sum + getAdjustedPercentile(s.label, s.percentile), 0) /
          Math.max(stats.length, 1);
        return { team, average: avg };
      })
      .sort((a, b) => b.average - a.average);
  }, [groupedByTeam]);

  const [first, second, third] = rankedTeams.slice(0, 3);
  const restRanked = rankedTeams.slice(3);

  // If you want a specific team first (e.g., Auburn), tweak here:
  const teamVisualOrder = useMemo(() => {
    const all = Object.keys(groupedByTeam);
    // Example: pin "Auburn" first if present. Adjust/remove as you prefer.
    return ['Auburn', ...all.filter((t) => t !== 'Auburn')];
  }, [groupedByTeam]);

  const renderStatBars = (category: Row[], prefix: string) =>
    category.map((stat, i) => (
      <Box key={`${prefix}-${stat.label}-${i}`}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Typography>{stat.label}</Typography>
          <Typography fontWeight={600}>
            {typeof stat.raw_value === 'number' ? stat.raw_value : stat.raw_value}
          </Typography>
        </Box>
        <Box sx={{ position: 'relative' }}>
          <LinearProgress
            variant="determinate"
            value={stat.percentile}
            sx={{
              height: 16,
              borderRadius: 8,
              backgroundColor: '#e0e0e0',
              '& .MuiLinearProgress-bar': {
                backgroundColor: getBarColor(stat.percentile),
              },
            }}
          />
          <Box
            sx={{
              position: 'absolute',
              top: '50%',
              left: `${stat.percentile}%`,
              transform: 'translate(-50%, -50%)',
              bgcolor: getBarColor(stat.percentile),
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
            {stat.percentile}
          </Box>
        </Box>
      </Box>
    ));

  return (
    <Box sx={{ px: 8, py: 4, color: 'white' }}>
      <Typography variant="h4" fontWeight={700} gutterBottom>
        SEC Performance
      </Typography>

      {/* Year Filter */}
      <Box display="flex" justifyContent="center" mt={1} mb={3}>
        <YearDropdown year={year} />
      </Box>

      {/* 🏆 Podium */}
      <Box sx={{ mt: 1, textAlign: 'center' }}>
        <Typography variant="h6" fontWeight={600} mb={2}>
          🏆 Top Performing Teams
        </Typography>
        <Box display="flex" justifyContent="center" alignItems="end" gap={0}>
          {[second, first, third].map((team, idx) => {
            if (!team) return null;
            return (
              <Box key={team.team} textAlign="center" width={120}>
                <Typography fontSize={22}>{['🥈', '🥇', '🥉'][idx]}</Typography>
                <Box sx={{ height: [100, 140, 80][idx], bgcolor: '#8B4513' }}>
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

      {/* 📋 Full Rankings */}
      {restRanked.length > 0 && (
        <Box sx={{ textAlign: 'center', mb: 6, maxWidth: 400, mx: 'auto' }}>
          <Typography variant="h6" fontWeight={600} mb={2}>
            📋 Full Rankings
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
                <th style={{ textAlign: 'left', padding: '8px 12px', backgroundColor: '#233954' }}>#</th>
                <th style={{ textAlign: 'left', padding: '8px 12px', backgroundColor: '#233954' }}>Team</th>
                <th style={{ textAlign: 'right', padding: '8px 12px', backgroundColor: '#233954' }}>Avg %</th>
              </tr>
            </thead>
            <tbody>
              {restRanked.map((team, idx) => (
                <tr key={team.team} style={{ borderBottom: '1px solid #2c3e50' }}>
                  <td style={{ padding: '8px 12px' }}>{idx + 4}.</td>
                  <td style={{ padding: '8px 12px' }}>{team.team}</td>
                  <td style={{ padding: '8px 12px', textAlign: 'right' }}>{team.average.toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </Box>
        </Box>
      )}

      {/* 📈 Team Visual Stats */}
      {teamVisualOrder.map((teamName) => {
        const stats = groupedByTeam[teamName];
        if (!stats) return null;

        const offensive = stats.filter((s) => offensiveLabels.includes(s.label));
        const defensive = stats.filter((s) => defensiveLabels.includes(s.label));

        return (
          <Box key={teamName} sx={{ mt: 6 }}>
            <Typography variant="h5" fontWeight={700} gutterBottom>
              {teamName}
            </Typography>

            {offensive.length > 0 && (
              <>
                <Typography variant="h6" fontWeight={600} gutterBottom mt={2}>
                  Offensive Stats
                </Typography>
                <Stack spacing={2}>{renderStatBars(offensive, `off-${teamName}`)}</Stack>
              </>
            )}

            {defensive.length > 0 && (
              <>
                <Typography variant="h6" fontWeight={600} gutterBottom mt={4}>
                  Defensive Stats
                </Typography>
                <Stack spacing={2}>{renderStatBars(defensive, `def-${teamName}`)}</Stack>
              </>
            )}

            <Divider sx={{ mt: 5, bgcolor: 'white', opacity: 0.2 }} />
          </Box>
        );
      })}
    </Box>
  );
}
