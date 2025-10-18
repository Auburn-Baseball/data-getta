import { PitchCountsTable as PitchCountsTableType } from '@/types/db';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import Divider from '@mui/material/Divider';
import Tooltip from '@mui/material/Tooltip';

export default function PitchCountTable({
  stats,
  teamName,
}: {
  stats: PitchCountsTableType | null;
  teamName: string;
}) {
  // Calculate percentages
  const calculatePercentage = (
    count: number | null | undefined,
    total: number | null | undefined,
  ): string => {
    if (!count || !total || total === 0) return '0%';
    return `${Math.round((count / total) * 100)}%`;
  };

  return (
    <Paper elevation={3} sx={{ paddingX: 2, paddingY: 2, width: '100%', overflowX: 'auto' }}>
      <Divider textAlign="center" sx={{ mb: 2 }}>
        Pitch Type Distribution
      </Divider>

      <TableContainer>
        <Table sx={{ minWidth: 800 }} size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center' }}>Total</TableCell>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center' }}>
                <Tooltip title="Four-Seam Fastball" arrow placement="top">
                  <span>FB</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center' }}>
                <Tooltip title="Sinker" arrow placement="top">
                  <span>SI</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center' }}>
                <Tooltip title="Slider" arrow placement="top">
                  <span>SL</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center' }}>
                <Tooltip title="Curveball" arrow placement="top">
                  <span>CB</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center' }}>
                <Tooltip title="Changeup" arrow placement="top">
                  <span>CH</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center' }}>
                <Tooltip title="Cutter" arrow placement="top">
                  <span>CT</span>
                </Tooltip>
              </TableCell>
              <TableCell sx={{ fontWeight: 'bold', textAlign: 'center' }}>
                <Tooltip title="Splitter" arrow placement="top">
                  <span>SP</span>
                </Tooltip>
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {stats ? (
              <>
                <TableRow>
                  <TableCell sx={{ textAlign: 'center' }}>{stats.total_pitches}</TableCell>
                  <TableCell sx={{ textAlign: 'center' }}>{stats.fourseam_count}</TableCell>
                  <TableCell sx={{ textAlign: 'center' }}>{stats.sinker_count}</TableCell>
                  <TableCell sx={{ textAlign: 'center' }}>{stats.slider_count}</TableCell>
                  <TableCell sx={{ textAlign: 'center' }}>{stats.curveball_count}</TableCell>
                  <TableCell sx={{ textAlign: 'center' }}>{stats.changeup_count}</TableCell>
                  <TableCell sx={{ textAlign: 'center' }}>{stats.cutter_count}</TableCell>
                  <TableCell sx={{ textAlign: 'center' }}>{stats.splitter_count}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ textAlign: 'center' }}>100%</TableCell>
                  <TableCell sx={{ textAlign: 'center' }}>
                    {calculatePercentage(stats.fourseam_count, stats.total_pitches)}
                  </TableCell>
                  <TableCell sx={{ textAlign: 'center' }}>
                    {calculatePercentage(stats.sinker_count, stats.total_pitches)}
                  </TableCell>
                  <TableCell sx={{ textAlign: 'center' }}>
                    {calculatePercentage(stats.slider_count, stats.total_pitches)}
                  </TableCell>
                  <TableCell sx={{ textAlign: 'center' }}>
                    {calculatePercentage(stats.curveball_count, stats.total_pitches)}
                  </TableCell>
                  <TableCell sx={{ textAlign: 'center' }}>
                    {calculatePercentage(stats.changeup_count, stats.total_pitches)}
                  </TableCell>
                  <TableCell sx={{ textAlign: 'center' }}>
                    {calculatePercentage(stats.cutter_count, stats.total_pitches)}
                  </TableCell>
                  <TableCell sx={{ textAlign: 'center' }}>
                    {calculatePercentage(stats.splitter_count, stats.total_pitches)}
                  </TableCell>
                </TableRow>
              </>
            ) : (
              <TableRow>
                <TableCell colSpan={8} sx={{ textAlign: 'center' }}>
                  No Pitch Data Available
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
}
