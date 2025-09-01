/*
* Creates a gauge diagram for each pitch type based on the score.
* Used for batters.
* 
* author: Braden Mosley
* lastEdit: 04-24-2024
*/

'use client'

import Stack from '@mui/material/Stack';
import Box from '@mui/material/Box';
import { Gauge, gaugeClasses } from '@mui/x-charts/Gauge';
import Typography from '@mui/material/Typography';
import { batter_run_values } from '@/app/utils/types';

const settings = {
    width: 160,
    height: 120,
    startAngle: -90,
    endAngle: 90,
    innerRadius: "70%",
    outerRadius: "100%",
    cornerRadius: '20%'
};

export default function BatterScoreGauge({values}: {values: batter_run_values[]}) {
    return (
        <Box
            sx={{
                border: '2px solid #e0e0e0',
                borderRadius: '24px',
                paddingX: 2,
                paddingY: 1,
                marginY: 4,
            }}
        >
            <Typography variant='h6'>Batter Run Values</Typography>
            
            <Stack direction='row' useFlexGap gap={4} flexWrap='wrap'>
                { values.map((pitch, index) => (
                    <Stack direction='column' key={index}>
                        <Gauge
                            {...settings}
                            value={pitch.Score}
                            sx={(theme) => ({
                                [`& .${gaugeClasses.valueText}`]: {
                                    fontWeight: 700,
                                    fontSize: 24,
                                },
                                [`& .${gaugeClasses.valueArc}`]: {
                                fill: '#e86100',
                                },
                            })}
                        />
                        <Typography textAlign='center'>{pitch.BatterSide} Side of Plate</Typography>
                        <Typography textAlign='center'>{pitch.PitcherThrows} {pitch.PitchType}</Typography>
                    </Stack>
                ))}
            </Stack>
        </Box>
    );
}