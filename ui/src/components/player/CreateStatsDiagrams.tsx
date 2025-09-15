import { prisma } from '@/utils/db';
import { batter_stats, pitcher_stats, pitch_sums } from '@/utils/types';
import { batter_replacer, pitcher_replacer } from '@/utils/replacer';
import Grid from '@mui/material/Grid';
import { Typography, Box } from '@mui/material';
import CreateBatterDiagrams from './Batting/CreateBatterDiagrams';
import CreatePitcherDiagrams from './Pitching/CreatePitcherDiagrams';

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

  // Use the date parameters for data fetching only, without rendering a DateSelector component
  // The dates come from URL or default values set in the parent component

  // https://www.prisma.io/docs/orm/more/upgrade-guides/upgrading-versions/upgrading-to-prisma-4#raw-query-mapping-postgresql-type-casts
  // In SQL function, get_batter_stats takes the params (text, text, date, date)
  // ::date explicitly casts the startDate and endDate strings to a SQL date type

  const batter = await prisma.$queryRaw<
    batter_stats[]
  >`SELECT * FROM get_batter_stats(${player}, ${team}, ${safeStartDate}::date, ${safeEndDate}::date)`;
  const pitcher = await prisma.$queryRaw<
    pitcher_stats[]
  >`SELECT * FROM get_pitcher_stats(${player}, ${team}, ${safeStartDate}::date, ${safeEndDate}::date)`;
  const pitches = await prisma.$queryRaw<
    pitch_sums[]
  >`SELECT * FROM get_pitch_count(${player}, ${team}, ${safeStartDate}::date, ${safeEndDate}::date)`;

  if (batter.length != 0 && pitcher.length != 0) {
    return (
      <Box sx={{ mt: 6 }}>
        <Grid container spacing={2}>
          <CreateBatterDiagrams stats={JSON.parse(JSON.stringify(batter, batter_replacer))} />

          <CreatePitcherDiagrams
            stats={JSON.parse(JSON.stringify(pitcher, pitcher_replacer))}
            sums={JSON.parse(JSON.stringify(pitches, pitcher_replacer))}
          />
        </Grid>
      </Box>
    );
  } else if (batter.length != 0) {
    return (
      <Box sx={{ mt: 6 }}>
        <Grid container spacing={2}>
          <CreateBatterDiagrams stats={JSON.parse(JSON.stringify(batter, batter_replacer))} />
        </Grid>
      </Box>
    );
  } else if (pitcher.length != 0) {
    return (
      <Box sx={{ mt: 6 }}>
        <Grid container spacing={2}>
          <CreatePitcherDiagrams
            stats={JSON.parse(JSON.stringify(pitcher, pitcher_replacer))}
            sums={JSON.parse(JSON.stringify(pitches, pitcher_replacer))}
          />
        </Grid>
      </Box>
    );
  } else {
    return (
      <Typography variant="h6" color="#d32f2f">
        <strong>Strikeout!</strong>
        <br />
        No stats found for this date range.
      </Typography>
    );
  }
}
