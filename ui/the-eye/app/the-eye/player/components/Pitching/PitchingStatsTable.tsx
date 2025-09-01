/*
* Creates the table to display certain pitcher stats.
* 
* author: Braden Mosley
* lastEdit: 04-23-2024
*/

import { pitcher_stats_forTable } from "@/app/utils/types";
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';

export default function PitchingStatsTable({player}: {player: pitcher_stats_forTable[]}) {    
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
                            <TableCell component="th" scope="row">Games Started</TableCell>
                            <TableCell component="th" scope="row">{player[0].games_started}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell component="th" scope="row">Pitches</TableCell>
                            <TableCell component="th" scope="row">{player[0].pitches}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell component="th" scope="row">Innings Pitched</TableCell>
                            <TableCell component="th" scope="row">{player[0].total_innings_pitched}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell component="th" scope="row">Batters Faced</TableCell>
                            <TableCell component="th" scope="row">{player[0].total_batters_faced}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell component="th" scope="row">Strikeouts</TableCell>
                            <TableCell component="th" scope="row">{player[0].total_strikeouts_pitcher}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell component="th" scope="row">Walks</TableCell>
                            <TableCell component="th" scope="row">{player[0].total_walks_pitcher}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell component="th" scope="row">Out of Zone</TableCell>
                            <TableCell component="th" scope="row">{player[0].total_out_of_zone_pitches}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell component="th" scope="row">Misses in Zone</TableCell>
                            <TableCell component="th" scope="row">{player[0].misses_in_zone}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell component="th" scope="row">Swings in Zone</TableCell>
                            <TableCell component="th" scope="row">{player[0].swings_in_zone}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell component="th" scope="row">Chases</TableCell>
                            <TableCell component="th" scope="row">{player[0].total_num_chases}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell component="th" scope="row">In Zone Whiff Percentage</TableCell>
                            <TableCell component="th" scope="row">{(player[0].in_zone_whiff_percentage * 100).toFixed(0)}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell component="th" scope="row">Chase Percentage</TableCell>
                            <TableCell component="th" scope="row">{(player[0].chase_percentage * 100).toFixed(0)}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell component="th" scope="row">K Percentage</TableCell>
                            <TableCell component="th" scope="row">{(player[0].k_percentage * 100).toFixed(0)}</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell component="th" scope="row">Base on Ball Percentage</TableCell>
                            <TableCell component="th" scope="row">{(player[0].base_on_ball_percentage * 100).toFixed(0)}</TableCell>
                        </TableRow>
                    </TableBody>
                </Table>
            </TableContainer>
        </Paper>
    );

}