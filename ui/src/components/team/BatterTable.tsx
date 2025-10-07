import Link from '@/utils/Link';
import { DataGrid, GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import { Theme } from '@/utils/theme';
import { BatterStatsTable } from '@/types/schemas';

const playerURL: string = '/team/';

const columns: GridColDef[] = [
  {
    field: 'Batter',
    headerName: 'Name',
    width: 200,
    renderCell: (params: GridRenderCellParams) => {
      const name = params.row.Batter.split(', ');

      return (
        <Link
          href={playerURL.concat(params.row.BatterTeam + '/player/' + name.join('_'))}
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
    description: 'Games Played',
    width: 80,
  },
  {
    field: 'at_bats',
    headerName: 'AB',
    description: 'At Bats',
    width: 80,
  },
  {
    field: 'hits',
    headerName: 'H',
    description: 'Hits',
    width: 80,
  },
  {
    field: 'doubles',
    headerName: '2B',
    description: 'Doubles',
    width: 80,
  },
  {
    field: 'triples',
    headerName: '3B',
    description: 'Triples',
    width: 80,
  },
  {
    field: 'homeruns',
    headerName: 'HR',
    description: 'Homeruns',
    width: 80,
  },
  {
    field: 'total_bases',
    headerName: 'TB',
    description: 'Total Bases',
    width: 80,
  },
  {
    field: 'walks',
    headerName: 'BB',
    description: 'Walks',
    width: 80,
  },
  {
    field: 'strikeouts',
    headerName: 'SO',
    description: 'Strikeouts',
    width: 80,
  },
  {
    field: 'batting_average',
    headerName: 'AVG',
    description: 'Batting Average',
    width: 80,
    valueGetter: (value) => {
      if (value === null || value === undefined) {
        return '.000';
      }
      if (value === 1) {
        return Number(value).toFixed(3);
      }
      return Number(value).toFixed(3).replace(/^0/, '');
    },
  },
  {
    field: 'on_base_percentage',
    headerName: 'OBP',
    description: 'On Base Percentage',
    width: 80,
    valueGetter: (value) => {
      if (value === null || value === undefined) {
        return '.000';
      }
      return Number(value).toFixed(3).replace(/^0/, '');
    },
  },
  {
    field: 'slugging_percentage',
    headerName: 'SLUG',
    description: 'Slugging Percentage',
    width: 80,
    valueGetter: (value) => {
      if (value === null || value === undefined) {
        return '.000';
      }
      return Number(value).toFixed(3).replace(/^0/, '');
    },
  },
  {
    field: 'onbase_plus_slugging',
    headerName: 'OPS',
    description: 'On Base Plus Slugging',
    width: 80,
    valueGetter: (value) => {
      if (value === null || value === undefined) {
        return '.000';
      }
      return Number(value).toFixed(3).replace(/^0/, '');
    },
  },
  {
    field: 'isolated_power',
    headerName: 'ISO',
    description: 'Isolated Power',
    width: 80,
    valueGetter: (value) => {
      if (value === null || value === undefined) {
        return '.000';
      }
      return Number(value).toFixed(3).replace(/^0/, '');
    },
  },
];

export default function BatterTable({ players }: { players: BatterStatsTable[] }) {
  return (
    <DataGrid
      rows={players}
      getRowId={(row) => row.Batter}
      columns={columns}
      hideFooter={true}
      autoHeight={true}
      disableColumnSelector={true}
      sx={{
        '& .MuiDataGrid-container--top [role=row]': {
          backgroundColor: Theme.palette.secondary.main,
        },
        '& .MuiDataGrid-columnHeaderTitle': { fontWeight: 700 },
      }}
    />
  );
}
