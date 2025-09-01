/*
* Page to display defensive shift models for the given pitcher.
* 
* author: Braden Mosley
* lastEdit: 04-15-2024
*/

import Box from "@mui/material/Box";
import Grid from '@mui/material/Unstable_Grid2';
import Typography from "@mui/material/Typography";
import CreateShiftingModels from "../../../components/ShiftModel/CreateShiftingModels";
import Divider from '@mui/material/Divider';
import { Suspense } from "react";
import StatsTableSkeleton from "../../../components/StatsTableSkeleton";

export default function Page (
    { params }:
    { params: { teamName: string, playerName: string } })
{
    const decodedTeamName = decodeURIComponent(params.teamName);
    const decodedPlayerName = decodeURIComponent(params.playerName);
    
    return (
        <Box>
            <Grid container spacing={2}>
                <Grid xs={4}>
                    <Typography align='center' variant="h6" fontWeight='700'>Left</Typography>
                </Grid>
                <Grid xs={4}>
                    <Typography align='center' variant="h6" fontWeight='700'>Pitch Type</Typography>
                </Grid>
                <Grid xs={4}>
                    <Typography align='center' variant="h6" fontWeight='700'>Right</Typography>
                </Grid>
            </Grid>

            <Divider sx={{ marginY: 2, borderColor: 'rgba(0, 0, 0, 0.24)' }}/>

            <Suspense fallback={<StatsTableSkeleton />}>
                <CreateShiftingModels
                    player = {decodedPlayerName}
                    team = {decodedTeamName}
                />
            </Suspense>
        </Box>
        
    );

}