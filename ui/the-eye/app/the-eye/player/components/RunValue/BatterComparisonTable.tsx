/*
* Table to compare a pitcher's run values to a team's batters.
* 
* author: Braden Mosley
* lastEdit: 04-24-2024
*/

'use client'

import { DataGrid, GridColDef, GridCellParams } from '@mui/x-data-grid';
import { Theme } from '@/app/utils/theme';
import Box from '@mui/material/Box';
import { batter_run_values, pitcher_run_values } from '@/app/utils/types';
import clsx from 'clsx';
import Typography from '@mui/material/Typography';
import Stack from '@mui/material/Stack';

const columns: GridColDef[] = [
    {
        field: 'Batter',
        headerName: 'Name',
        width: 200,
        valueGetter: (value: string) => {
            const name = value.split(/(?=[A-Z])/);
            return (name[1] + ' ' + name[0]);
        },
    },
    {
        field: 'BatterSide',
        headerName: 'Batter Side',
        width: 140,
    },
    {
        field: 'PitcherThrows',
        headerName: 'Pitcher Throws',
        width: 140,
    },
    {
        field: 'PitchType',
        headerName: 'Pitch Type',
        width: 200,
    },
    {
        field: 'NumPitches',
        headerName: 'Total Pitches',
        width: 140,
    },
    {
        field: 'Score',
        headerName: 'Score',
        width: 140,
        cellClassName: (params: GridCellParams<any, number>) => {
            if (params.value == null) {
                return '';
            }
        
            return clsx('super-app', {
                negative: params.value < 0,
                positive: params.value > 0,
            });
        },
    },
];

export default function BatterComparisonTable({players, pitcher}: {players: batter_run_values[], pitcher: pitcher_run_values[]}) {    
    let comparison : batter_run_values[] = [];
    players.map((batterPitch) => {
        for (const pitcherPitch of pitcher) {
            if (batterPitch.PitchType === pitcherPitch.PitchType && batterPitch.PitcherThrows === pitcherPitch.Handedness) {
                if (pitcherPitch.Score !== null && batterPitch.Score !== null) {
                    let result = {...batterPitch};
                    result.Score = (Number((pitcherPitch.Score - batterPitch.Score).toFixed(2)));
                    comparison.push(result);
                }
            }
        }
    })
    
    return (
        <Box
            sx={{
                paddingY: 4,
                '& .super-app.negative': {
                    backgroundColor: Theme.palette.error.main,
                    color: '#FFF',
                    fontWeight: '700',
                },
                '& .super-app.positive': {
                    backgroundColor: Theme.palette.success.main,
                    color: '#FFF',
                    fontWeight: '700',
                },
            }}
        >
            <Stack direction = 'row' useFlexGap gap={1}>
                <Typography fontWeight={700} color={Theme.palette.success.main}>+ Advantage Pitcher</Typography>
                <Typography fontWeight={700}>|</Typography>
                <Typography fontWeight={700} color={Theme.palette.error.main}>- Advantage Batter</Typography>
            </Stack>
            
            <DataGrid
                rows = {comparison}
                getRowId = {(row) => row.Batter + row.PitchType + row.PitcherThrows + row.BatterSide}
                columns = {columns}
                hideFooter = {true}
                sx={{
                    '& .MuiDataGrid-container--top [role=row]': {backgroundColor: Theme.palette.grey[300]},
                    '& .MuiDataGrid-columnHeaderTitle': {fontWeight: 700},
                }}
                autoHeight
            />
        </Box>
    );
}
