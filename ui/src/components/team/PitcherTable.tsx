import Link from '@/utils/Link';
import { DataGrid, GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import { PitcherStatsTable } from '@/types/schemas';
import { Theme } from '@/utils/theme';
import Box from '@mui/material/Box';

const playerURL: string = '/team/';

const columns: GridColDef[] = [
  {
    field: 'Pitcher',
    headerName: 'Name',
    width: 200,
    renderCell: (params: GridRenderCellParams) => {
      const name = params.row.Pitcher.split(', ');

      return (
        <Link
          href={playerURL.concat(params.row.PitcherTeam + '/player/' + name.join('_'))}
          name={name.join(', ')}
          fontWeight={500}
          underline="always"
        />
      );
    },
  },
  {
    field: 'games',
    headerName: 'GP',
    description: 'Games Plauyed',
    width: 80,
  },
  {
    field: 'games_started',
    headerName: 'GS',
    description: 'Games Started',
    width: 80,
  },
  {
    field: 'total_innings_pitched',
    headerName: 'IP',
    description: 'Innings Pitched',
    width: 80,
  },
  {
    field: 'hits',
    headerName: 'H',
    description: 'Hits Allowed',
    width: 80,
  },
  {
    field: 'runs_allowed',
    headerName: 'R',
    description: 'Runs Allowed',
    width: 80,
  },
  {
    field: 'homeruns',
    headerName: 'HR',
    description: 'Home Runs',
    width: 80,
  },
  {
    field: 'total_walks_pitcher',
    headerName: 'BB',
    description: 'Total Walks',
    width: 80,
  },
  {
<<<<<<< HEAD
    field: 'total_strikeouts_pitcher',
    headerName: 'K',
    description: 'Total Strikeouts',
=======
    field: 'total_out_of_zone_pitches',
    headerName: 'OoZ',
    description: 'Out of Zone Percentage',
    width: 80,
    valueGetter: (value, row) => {
      const pitches = row?.pitches;
      if (value === null || value === undefined || !pitches) {
        return '0%';
      }
      return `${Number(((Number(value) / Number(pitches)) * 100).toFixed(0))}%`;
    },
  },
  {
    field: 'misses_in_zone',
    headerName: 'MiZ',
    description: 'Misses in Zone Percentage',
    width: 80,
    valueGetter: (value, row) => {
      const pitches = row?.pitches;
      if (value === null || value === undefined || !pitches) {
        return '0%';
      }
      return `${Number(((Number(value) / Number(pitches)) * 100).toFixed(0))}%`;
    },
  },
  {
    field: 'swings_in_zone',
    headerName: 'SiZ',
    description: 'Swings in Zone Percentage',
    width: 80,
    valueGetter: (value, row) => {
      const pitches = row?.pitches;
      if (value === null || value === undefined || !pitches) {
        return '0%';
      }
      return `${Number(((Number(value) / Number(pitches)) * 100).toFixed(0))}%`;
    },
  },
  {
    field: 'total_num_chases',
    headerName: 'Chases',
    description: 'Total Number of Chases',
>>>>>>> upstream/main
    width: 80,
  },
  {
    field: 'k_per_9',
    headerName: 'K/9',
    description: 'Strikeouts Per 9 Innings',
    width: 80,
    valueGetter: (value) => {
      if (value === null || value === undefined) {
        return '0.0';
      }
      return Number(value).toFixed(1);
    },
  },
  {
    field: 'bb_per_9',
    headerName: 'BB/9',
    description: 'Walks Per 9 Innings',
    width: 80,
    valueGetter: (value) => {
      if (value === null || value === undefined) {
        return '0.0';
      }
      return Number(value).toFixed(1);
    },
  },
  {
    field: 'whip',
    headerName: 'WHIP',
    description: 'Walks Hits Per Innings Pitched',
    width: 80,
    valueGetter: (value) => {
      if (value === null || value === undefined) {
        return '0.00';
      }
      return Number(value).toFixed(2);
    },
  },
];

export default function PitcherTable({ players }: { players: PitcherStatsTable[] }) {
  return (
    <Box sx={{ height: 350 }}>
      <DataGrid
        rows={players}
        getRowId={(row) => row.Pitcher}
        columns={columns}
        hideFooter={true}
        sx={{
          '& .MuiDataGrid-container--top [role=row]': {
            backgroundColor: Theme.palette.secondary.main,
          },
          '& .MuiDataGrid-columnHeaderTitle': { fontWeight: 700 },
        }}
      />
    </Box>
  );
}
