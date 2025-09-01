/*
* Creates the pitcher stats table and bar chart
* 
* author: Braden Mosley
* lastEdit: 04-15-2024
*/

import Grid from '@mui/material/Unstable_Grid2';
import PitchingStatsTable from './PitchingStatsTable';
import PitchSumsBarChart from './PitchSumsBarChart';
import { pitcher_stats_forTable, pitch_sums_forTable } from "@/app/utils/types";

export default function CreatePitcherDiagrams({stats, sums}: {stats: pitcher_stats_forTable[], sums: pitch_sums_forTable[]}) {
    return (
        <>
            <Grid sm={6} md={4} xl={3}>
                <PitchingStatsTable player = {stats}/>
            </Grid>

            <Grid sm={12} md={8} xl={9}>
                <PitchSumsBarChart player = {sums}/>
            </Grid>
        </>
    );
}