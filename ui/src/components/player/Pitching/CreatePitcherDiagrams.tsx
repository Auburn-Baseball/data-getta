import Grid from '@mui/material/Grid';
import PitchingStatsTable from './PitchingStatsTable';
import { pitcher_stats_forTable, pitch_sums_forTable } from '@/utils/types';

export default function CreatePitcherDiagrams({
  stats,
  sums,
}: {
  stats: pitcher_stats_forTable[];
  sums: pitch_sums_forTable[];
}) {
  const hasPitchSummary = sums.length > 0;

  return (
    <>
      {/* The grid container centers the PitchingStatsTable component */}
      <Grid
        sx={{ display: 'flex', justifyContent: 'center', paddingY: 2, width: '100%' }}
        aria-label={hasPitchSummary ? 'Pitching stats with summary data' : 'Pitching stats'}
      >
        <PitchingStatsTable
          player={stats}
          teamName={undefined} // Default value; can be updated when real team data is provided
          playerName={undefined} // Default value; placeholder until a valid player name is available
          startDate={undefined} // Default start date is managed within PitchingStatsTable
          endDate={undefined} // Default end date is calculated in PitchingStatsTable
        />
      </Grid>
    </>
  );
}
