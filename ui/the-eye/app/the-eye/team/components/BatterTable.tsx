/*
* Table to show a player's batting stats.
* Created based on MUI examples.
* 
* author: Braden Mosley
* lastEdit: 04-22-2024
*/

'use client'

import Link from '@/app/utils/Link'
import { DataGrid, GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import { batter_stats_forTable } from '../../../utils/types';
import { Theme } from '@/app/utils/theme';
import Box from '@mui/material/Box';

const playerURL : string = '/the-eye/player/';

const columns: GridColDef[] = [
    {
        field: 'Batter',
        headerName: 'Name',
        width: 200,
        renderCell: (params: GridRenderCellParams) => {
            const name = params.row.Batter.split(/(?=[A-Z])/);

            return (
                <Link 
                    href = {playerURL.concat(params.row.BatterTeam + '/' + params.row.Batter + '/stats')}
                    name = {name[1] + ' ' + name[0]}
                    fontWeight = {500}
                    underline = 'always'
                />
            )
        }
    },
    {
        field: 'games',
        headerName: 'Games',
        description: 'Games',
        width: 80,
    },
    {
        field: 'plate_appearances',
        headerName: 'PA',
        description: 'Plate Appearances',
        width: 80,
    },
    {
        field: 'at_bats',
        headerName: 'AB',
        description: 'At Bats',
        width: 80,
    },
    {
        field: 'batting_average',
        headerName: 'AVG',
        description: 'Batting Average',
        width: 80,
    },
    {
        field: 'hits',
        headerName: 'H',
        description: 'Hits',
        width: 80,
    },
    {
        field: 'strikes',
        headerName: 'Strikes',
        description: 'Strikes',
        width: 80,
    },
    {
        field: 'walks',
        headerName: 'BB',
        description: 'Walks',
        width: 80,
    },
    {
        field: 'strikeouts',
        headerName: 'K',
        description: 'Strikeouts',
        width: 80,
    },
    {
        field: 'homeruns',
        headerName: 'HR',
        description: 'Homeruns',
        width: 80,
    },
    {
        field: 'extra_base_hits',
        headerName: 'XBH',
        description: 'Extra Base Hits',
        width: 80,
    },
    {
        field: 'sacrifice',
        headerName: 'S',
        description: 'Sacrifice',
        width: 80,
    },
    {
        field: 'hit_by_pitch',
        headerName: 'HBP',
        description: 'Hit by Pitch',
        width: 80,
    },
    {
        field: 'total_bases',
        headerName: 'TB',
        description: 'Total Bases',
        width: 80,
    },
    {
        field: 'on_base_percentage',
        headerName: 'OBP',
        description: 'On Base Percentage',
        width: 80,
    },
    {
        field: 'slugging_percentage',
        headerName: 'SLUG',
        description: 'Slugging Percentage',
        width: 80,
    },
    {
        field: 'onbase_plus_slugging',
        headerName: 'OPS',
        description: 'On Base Plus Slugging',
        width: 80,
    },
    {
        field: 'chase_percentage',
        headerName: 'CHASE',
        description: 'Chase Percentage',
        width: 80,
        valueGetter: (value) => {
            if (!value) {
                return value;
            } else {
                return Number((value * 100).toFixed(0))
            }
        },
    },
    {
        field: 'in_zone_whiff_percentage',
        headerName: 'IZW',
        description: 'In Zone Whiff Percentage',
        width: 80,
        valueGetter: (value) => {
            if (!value) {
                return value;
            } else {
                return Number((value * 100).toFixed(0))
            }
        },
    },
    {
        field: 'isolated_power',
        headerName: 'ISO',
        description: 'Isolated Power',
        width: 80,
    },
    {
        field: 'k_percentage',
        headerName: 'K%',
        description: 'K Percentage',
        width: 80,
        valueGetter: (value) => {
            if (!value) {
                return value;
            } else {
                return Number((value * 100).toFixed(0))
            }
        },
    },
    {
        field: 'base_on_ball_percentage',
        headerName: 'BoB',
        description: 'Base on Ball Percentage',
        width: 80,
        valueGetter: (value) => {
            if (!value) {
                return value;
            } else {
                return Number((value * 100).toFixed(0))
            }
        },
    },
];

export default function BatterTable({players}: {players: batter_stats_forTable[]}) {
    return (
        <Box sx={{ height: 350 }}>
            <DataGrid
                rows = {players}
                getRowId = {(row) => row.Batter}
                columns = {columns}
                hideFooter = {true}
                sx={{
                    '& .MuiDataGrid-container--top [role=row]': {backgroundColor: Theme.palette.secondary.main},
                    '& .MuiDataGrid-columnHeaderTitle': {fontWeight: 700},
                }}
            />
        </Box>
    );
}
