/*
* Creates the table to display certain batter stats.
* 
* author: Braden Mosley
* lastEdit: 04-15-2024
*/

import { batter_stats_forTable } from "@/app/utils/types";
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';

export default function BattingStatsTable({player}: {player: batter_stats_forTable[]}) {
    return (
        <Paper 
            elevation={3}
            sx={{ paddingX: 1, paddingY: 1 }}
        >
            <TableContainer>
                <Table>
                    <TableBody>
                        <TableRow>
                            <TableCell component="th" scope="row">Games</TableCell>
                            <TableCell component="th" scope="row">{player[0].games}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell component="th" scope="row">Plate Appearances</TableCell>
                            <TableCell component="th" scope="row">{player[0].plate_appearances}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell component="th" scope="row">At Bats</TableCell>
                            <TableCell component="th" scope="row">{player[0].at_bats}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell component="th" scope="row">Batting Average</TableCell>
                            <TableCell component="th" scope="row">{player[0].batting_average}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell component="th" scope="row">Hits</TableCell>
                            <TableCell component="th" scope="row">{player[0].hits}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell component="th" scope="row">Strikes</TableCell>
                            <TableCell component="th" scope="row">{player[0].strikes}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell component="th" scope="row">Walks</TableCell>
                            <TableCell component="th" scope="row">{player[0].walks}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell component="th" scope="row">Strikeouts</TableCell>
                            <TableCell component="th" scope="row">{player[0].strikeouts}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell component="th" scope="row">Homeruns</TableCell>
                            <TableCell component="th" scope="row">{player[0].homeruns}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell component="th" scope="row">Extra Base Hits</TableCell>
                            <TableCell component="th" scope="row">{player[0].extra_base_hits}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell component="th" scope="row">Sacrifice</TableCell>
                            <TableCell component="th" scope="row">{player[0].sacrifice}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell component="th" scope="row">Hit By Pitch</TableCell>
                            <TableCell component="th" scope="row">{player[0].hit_by_pitch}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell component="th" scope="row">Total Bases</TableCell>
                            <TableCell component="th" scope="row">{player[0].total_bases}</TableCell>
                        </TableRow>
                    </TableBody>
                </Table>
            </TableContainer>
        </Paper>
    );

}