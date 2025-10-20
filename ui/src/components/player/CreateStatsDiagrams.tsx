import { Typography, Box } from '@mui/material';
import CreateBatterDiagrams from './Batting/CreateBatterDiagrams';
import CreatePitcherDiagrams from './Pitching/CreatePitcherDiagrams';
import {
  fetchPlayerBatterStats,
  fetchPlayerPitchCounts,
  fetchPlayerPitcherStats,
} from '@/services/playerService';
import {
  resolveBatterStats,
  resolvePitchCounts,
  resolvePitcherStats,
} from '@/transforms/playerStatResolvers';

export default async function CreateStatsDiagrams({
  player,
  team,
  startDate,
  endDate,
}: {
  player: string;
  team: string;
  startDate: string;
  endDate: string;
}) {
  // Safety check for valid dates - use current date range if invalid
  const safeStartDate =
    startDate && startDate.match(/^\d{4}-\d{2}-\d{2}$/) ? startDate : '2024-02-16';

  const safeEndDate =
    endDate && endDate.match(/^\d{4}-\d{2}-\d{2}$/)
      ? endDate
      : new Date().toISOString().split('T')[0];

  const range = { startDate: safeStartDate, endDate: safeEndDate };

  const [batterResult, pitcherResult, pitchCountResult] = await Promise.all([
    fetchPlayerBatterStats(player, team, range),
    fetchPlayerPitcherStats(player, team, range),
    fetchPlayerPitchCounts(player, team, range),
  ]);

  if (batterResult.error) {
    console.error('Failed to fetch batter stats:', batterResult.error);
  }
  if (pitcherResult.error) {
    console.error('Failed to fetch pitcher stats:', pitcherResult.error);
  }
  if (pitchCountResult.error) {
    console.error('Failed to fetch pitch count stats:', pitchCountResult.error);
  }

  const resolvedBatterStats = resolveBatterStats(batterResult.data);
  const resolvedPitcherStats = resolvePitcherStats(pitcherResult.data);
  const resolvedPitchCounts = resolvePitchCounts(pitchCountResult.data);

  if (!resolvedBatterStats && !resolvedPitcherStats && !resolvedPitchCounts) {
    return (
      <Typography variant="h6" color="#d32f2f">
        <strong>Strikeout!</strong>
        <br />
        No stats found for this date range.
      </Typography>
    );
  }

  return (
    <Box sx={{ mt: 6 }}>
      {resolvedBatterStats && <CreateBatterDiagrams stats={resolvedBatterStats} />}
      {(resolvedPitcherStats || resolvedPitchCounts) && (
        <CreatePitcherDiagrams stats={resolvedPitcherStats} pitchCounts={resolvedPitchCounts} />
      )}
    </Box>
  );
}
