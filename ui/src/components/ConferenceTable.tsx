import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Link from '@/components/ui/Link';
import { ConferenceGroup } from '@/types';

interface ConferenceTableProps {
  conferenceGroup: ConferenceGroup;
}

export default function ConferenceTable({ conferenceGroup }: ConferenceTableProps) {
  const { ConferenceName: name, teams } = conferenceGroup;
  const teamURL: string = '/team/';
  const table: string = '/roster';

  return (
    <Paper elevation={3} sx={{ paddingX: 1, paddingY: 1 }}>
      <Typography variant="h6" fontWeight={700} paddingLeft={1.5}>
        {name}
      </Typography>

      <TableContainer>
        <Table sx={{ minWidth: 250 }}>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 700 }}>Team</TableCell>
            </TableRow>
          </TableHead>

          <TableBody>
            {teams.map((team, index) => (
              <TableRow key={index} sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
                <TableCell component="th" scope="row">
                  <Link
                    href={teamURL.concat(team.TrackmanAbbreviation).concat(table)}
                    name={team.TeamName as string}
                    fontWeight={600}
                    underline="always"
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
}
