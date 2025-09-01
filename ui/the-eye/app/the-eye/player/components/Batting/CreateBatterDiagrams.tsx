/*
* Creates the batter stats table and bar chart
* 
* author: Braden Mosley
* lastEdit: 04-15-2024
*/

import Grid from '@mui/material/Unstable_Grid2';
import BattingStatsBarChart from './BattingStatsBarChart';
import BattingStatsTable from './BattingStatsTable';
import { batter_stats_forTable } from "@/app/utils/types";

export default function CreateBatterDiagrams({stats}: {stats: batter_stats_forTable[]}) {    
    return (
        <>
            <Grid sm={6} md={4} xl={3}>
                <BattingStatsTable player = {stats}/>
            </Grid>

            <Grid sm={12} md={8} xl={9}>
                <BattingStatsBarChart player = {stats}/>
            </Grid>
        </>
    );
}