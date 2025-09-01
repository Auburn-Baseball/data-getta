/*
* Table to show a player's pitching stats.
* Created based on MUI examples.
* 
* author: Braden Mosley
* lastEdit: 04-03-2024
*/

'use client'

import Link from '@/app/utils/Link'
import { DataGrid, GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import { pitcher_stats_forTable } from '../../../utils/types';
import { Theme } from '@/app/utils/theme';
import Box from '@mui/material/Box';

const playerURL : string = '/the-eye/player/';

const columns: GridColDef[] = [
    {
        field: 'Pitcher',
        headerName: 'Name',
        width: 200,
        renderCell: (params: GridRenderCellParams) => {
            const name = params.row.Pitcher.split(/(?=[A-Z])/);

            return (
                <Link 
                    href = {playerURL.concat(params.row.PitcherTeam + '/' + params.row.Pitcher + '/stats')}
                    name = {name[1] + ' ' + name[0]}
                    fontWeight = {500}
                    underline = 'always'
                />
            )
        }
    },
    {
        field: 'games',
        headerName: 'G',
        description: 'Games',
        width: 80,
    },
    {
        field: 'games_started',
        headerName: 'GS',
        description: 'Games Started',
        width: 80,
    },
    {
        field: 'pitches',
        headerName: 'P',
        description: 'Pitches',
        width: 80,
    },
    {
        field: 'total_innings_pitched',
        headerName: 'IP',
        description: 'Total Innings Pitched',
        width: 80,
    },
    {
        field: 'total_batters_faced',
        headerName: 'BF',
        description: 'Total Batters Faced',
        width: 80,
    },
    {
        field: 'total_strikeouts_pitcher',
        headerName: 'K',
        description: 'Total Strikeouts',
        width: 80,
    },
    {
        field: 'total_walks_pitcher',
        headerName: 'BB',
        description: 'Total Walks',
        width: 80,
    },
    {
        field: 'total_out_of_zone_pitches',
        headerName: 'OoZ',
        description: 'Total Out of Zone Pitches',
        width: 80,
    },
    {
        field: 'misses_in_zone',
        headerName: 'MiZ',
        description: 'Misses in Zone',
        width: 80,
    },
    {
        field: 'swings_in_zone',
        headerName: 'SiZ',
        description: 'Swings in Zone',
        width: 80,
    },
    {
        field: 'total_num_chases',
        headerName: 'Chases',
        description: 'Total Number of Chases',
        width: 80,
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

export default function PitcherTable({players}: {players: pitcher_stats_forTable[]}) {
    return (
        <Box sx={{ height: 350 }}>
            <DataGrid
                rows = {players}
                getRowId = {(row) => row.Pitcher}
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
