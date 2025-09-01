/*
* Creates the defensive shift svgs for the given pitch type.
* 
* author: Braden Mosley
* lastEdit: 04-15-2024
*/

import Grid from '@mui/material/Unstable_Grid2';
import ShiftingModel from './ShiftingModel';
import Typography from "@mui/material/Typography";
import Divider from '@mui/material/Divider';

export default function PitchTypeShiftModel({values, pitchType}: {values: {ModelValues: number[]}[], pitchType: string}) {   
    
    // If the pitcher does not have this pitch type, return nothing
    if (values.length == 0) {
        return <></>
    }

    // values[0] is the left batter side.
    // values[1] is the right batter side.
    
    return (
        <>
            <Grid xs={4}>
                <ShiftingModel percentages={values[0].ModelValues} />
            </Grid>

            <Grid xs={4}>
                <Typography align='center' variant="h6" fontWeight='700'>{pitchType}</Typography>
            </Grid>

            <Grid xs={4}>
                <ShiftingModel percentages={values[1].ModelValues} />
            </Grid>

            <Grid xs={12}>
                <Divider sx={{ marginY: 2 }}/>
            </Grid>
        </>
    );
}