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
      // Don't make "Total" row a hyperlink
      if (params.row.Batter === 'Total') {
        return <span style={{ fontWeight: 'bold' }}>Total</span>;
      }

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
  // Compute summary stats
  const summary = {
    Batter: 'Total',
    BatterTeam: '',
    Year: 0,
    games: players.length > 0 ? Math.max(...players.map((p) => p.games || 0)) : 0,
    plate_appearances: players.reduce((sum, p) => sum + (p.plate_appearances || 0), 0),
    at_bats: players.reduce((sum, p) => sum + (p.at_bats || 0), 0),
    hits: players.reduce((sum, p) => sum + (p.hits || 0), 0),
    doubles: players.reduce((sum, p) => sum + (p.doubles || 0), 0),
    triples: players.reduce((sum, p) => sum + (p.triples || 0), 0),
    homeruns: players.reduce((sum, p) => sum + (p.homeruns || 0), 0),
    total_bases: players.reduce((sum, p) => sum + (p.total_bases || 0), 0),
    walks: players.reduce((sum, p) => sum + (p.walks || 0), 0),
    strikeouts: players.reduce((sum, p) => sum + (p.strikeouts || 0), 0),
    batting_average:
      players.length > 0
        ? players.reduce((sum, p) => sum + (p.batting_average || 0), 0) / players.length
        : 0,
    on_base_percentage:
      players.length > 0
        ? players.reduce((sum, p) => sum + (p.on_base_percentage || 0), 0) / players.length
        : 0,
    slugging_percentage:
      players.length > 0
        ? players.reduce((sum, p) => sum + (p.slugging_percentage || 0), 0) / players.length
        : 0,
    onbase_plus_slugging:
      players.length > 0
        ? players.reduce((sum, p) => sum + (p.onbase_plus_slugging || 0), 0) / players.length
        : 0,
    isolated_power:
      players.length > 0
        ? players.reduce((sum, p) => sum + (p.isolated_power || 0), 0) / players.length
        : 0,
    // Fill other required fields with defaults
    strikes: 0,
    extra_base_hits: 0,
    sacrifice: 0,
    hit_by_pitch: 0,
    k_percentage: 0,
    base_on_ball_percentage: 0,
    chase_percentage: 0,
    in_zone_whiff_percentage: 0,
  };

  const rowsWithSummary = [...players, summary];

  return (
    <DataGrid
      rows={rowsWithSummary}
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
        '& .MuiDataGrid-row:last-child': {
          fontWeight: 'bold',
          backgroundColor: '#f5f5f5',
        },
      }}
    />
  );
}
