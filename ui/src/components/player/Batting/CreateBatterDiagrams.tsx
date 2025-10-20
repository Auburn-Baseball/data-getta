import Grid from '@mui/material/Grid';
import BattingStatsTable from './BattingStatsTable';
import type { BatterStatsTable } from '@/types/db';

export default function CreateBatterDiagrams({ stats }: { stats: BatterStatsTable | null }) {
  if (!stats) {
    return null;
  }

  return (
    <Grid container spacing={2}>
      <Grid sx={{ width: '100%' }}>
        <BattingStatsTable stats={stats} />
      </Grid>
    </Grid>
  );
}
