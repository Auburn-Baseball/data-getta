import Link from '@/utils/Link';
import { DataGrid, GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import { Theme } from '@/utils/theme';
import { PlayersTable } from '@/types/schemas';

const playerURL: string = '/team/';

const columns: GridColDef[] = [
  {
    field: 'Name',
    headerName: 'Name',
    width: 200,
    renderCell: (params: GridRenderCellParams) => {
      const name = params.row.Name.split(', ');

      return (
        <Link
          href={playerURL.concat(params.row.TeamTrackmanAbbreviation + '/player/' + name.join('_'))}
          name={name.join(', ')}
          fontWeight={500}
          underline="always"
        />
      );
    },
  },
  {
    field: 'PitcherId',
    headerName: 'PitcherId',
    width: 200,
    renderCell: (params: GridRenderCellParams) => {
      return <span>{params.value ? params.value : '---'}</span>;
    },
  },
  {
    field: 'BatterId',
    headerName: 'BatterId',
    width: 200,
    renderCell: (params: GridRenderCellParams) => {
      return <span>{params.value ? params.value : '---'}</span>;
    },
  },
];

export default function RosterTable({ players }: { players: PlayersTable[] }) {
  return (
    <DataGrid
      rows={players}
      getRowId={(row) => row.Name}
      columns={columns}
      autoHeight={true}
      hideFooter={true}
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
