/*
* Creates the heat map svgs for the given pitch type.
* 
* author: Braden Mosley
* lastEdit: 04-16-2024
*/

import Grid from '@mui/material/Unstable_Grid2';
import HeatMap from './HeatMap';
import Typography from "@mui/material/Typography";
import Divider from '@mui/material/Divider';

// Return type from prisma queries in CreateHeatMaps.tsx
type heatmap = {
    AllPitches: number[];
    SuccessfulPitches: number[];
    PitchRatio: number[];
}

export default function PitchTypeShiftModel({values, pitchType}: {values: heatmap[], pitchType: string}) {   
    // If the pitcher does not have this pitch type, return nothing
    if (values.length == 0) {
        return <></>
    }
    
    return (
        <>
            <Grid xs={12}>
                <Typography align='center' variant="h6" fontWeight='700'>{pitchType}</Typography>
            </Grid>
            
            <Grid xs={4}>
                <HeatMap percentages={values[0].AllPitches} />
            </Grid>

            <Grid xs={4}>
                <HeatMap percentages={values[0].SuccessfulPitches} />
            </Grid>

            <Grid xs={4}>
                <HeatMap percentages={values[0].PitchRatio} />
            </Grid>

            <Grid xs={12}>
                <Divider sx={{ marginY: 2 }}/>
            </Grid>
        </>
    );
}