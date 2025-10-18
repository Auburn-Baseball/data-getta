import Link from '@/utils/Link';
import { DataGrid, GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import { PitchCountsTable } from '@/types/db';
import { Theme } from '@/styles/theme';
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
    field: 'total_pitches',
    headerName: 'Total',
    description: 'Total Pitches',
    width: 120,
  },
  {
    field: 'fourseam_count',
    headerName: 'Four Seam',
    description: 'Total Four Seams',
    width: 120,
  },
  {
    field: 'twoseam_count',
    headerName: 'Two Seam',
    description: 'Total Two Seams',
    width: 120,
  },
  {
    field: 'curveball_count',
    headerName: 'Curveball',
    description: 'Total Curveballs',
    width: 120,
  },

  {
    field: 'sinker_count',
    headerName: 'Sinker',
    description: 'Total Sinkers',
    width: 120,
  },
  {
    field: 'slider_count',
    headerName: 'Slider',
    description: 'Total Sliders',
    width: 120,
  },
  {
    field: 'changeup_count',
    headerName: 'Changeup',
    description: 'Total Changeups',
    width: 120,
  },
  {
    field: 'cutter_count',
    headerName: 'Cutter',
    description: 'Total Cutters',
    width: 120,
  },
  {
    field: 'splitter_count',
    headerName: 'Splitter',
    description: 'Total Splitters',
    width: 120,
  },
  {
    field: 'other_count',
    headerName: 'Other',
    description: 'Total Others',
    width: 120,
  },
];

export default function PitchSumsTable({ players }: { players: PitchCountsTable[] }) {
  return (
    <Box sx={{ height: 350, paddingTop: 4 }}>
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
