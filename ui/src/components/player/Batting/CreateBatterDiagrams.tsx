import Grid from '@mui/material/Grid';
import BattingStatsTable from './BattingStatsTable';
import { batter_stats_forTable } from '@/utils/types';

export default function CreateBatterDiagrams({ stats }: { stats: batter_stats_forTable[] }) {
  return (
    <Grid container spacing={2}>
      {/* Render BattingStatsTable inside a responsive grid item */}
      <Grid sx={{ width: '100%' }}>
        <BattingStatsTable
          player={stats}
          teamName={undefined}
          playerName={undefined}
          startDate={undefined}
          endDate={undefined}
        />
      </Grid>
    </Grid>
  );
}
