import Grid from '@mui/material/Grid';
import type { PitchCountsTable, PitcherStatsTable } from '@/types/db';
import PitchingStatsTable from './PitchingStatsTable';
import PitchCountTable from './PitchCountTable';

type CreatePitcherDiagramsProps = {
  stats: PitcherStatsTable | null;
  pitchCounts: PitchCountsTable | null;
};

export default function CreatePitcherDiagrams({ stats, pitchCounts }: CreatePitcherDiagramsProps) {
  if (!stats && !pitchCounts) {
    return null;
  }

  return (
    <>
      {stats && (
        <Grid
          sx={{ display: 'flex', justifyContent: 'center', paddingY: 2, width: '100%' }}
          aria-label="Pitching stats"
        >
          <PitchingStatsTable stats={stats} />
        </Grid>
      )}
      {pitchCounts && (
        <Grid
          sx={{ display: 'flex', justifyContent: 'center', paddingY: 2, width: '100%' }}
          aria-label="Pitch count summary"
        >
          <PitchCountTable stats={pitchCounts} />
        </Grid>
      )}
    </>
  );
}
