/*
* Table to show a team's roster.
* Created based on MUI examples.
* 
* author: Braden Mosley
* lastEdit: 04-03-2024
*/

'use client'

import Link from '@/app/utils/Link'
import { DataGrid, GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import { Theme } from '@/app/utils/theme';

const playerURL : string = '/the-eye/player/';

const columns: GridColDef[] = [
    {
        field: 'PlayerName',
        headerName: 'Name',
        width: 200,
        renderCell: (params: GridRenderCellParams) => {
            const name = params.row.PlayerName.split(/(?=[A-Z])/);
            
            return (
                <Link 
                    href = {playerURL.concat(params.row.TeamName + '/' + params.row.PlayerName + '/stats')}
                    name = {name[1] + ' ' + name[0]}
                    fontWeight = {500}
                    underline = 'always'
                />
            );
        }
    },
];

export default function RosterTable({players}: {players: {PlayerName: String, TeamName: String}[]}) {
    return (
        <DataGrid
            rows = {players}
            getRowId = {(row) => row.PlayerName}
            columns = {columns}
            autoHeight = {true}
            hideFooter = {true}
            sx={{
                '& .MuiDataGrid-container--top [role=row]': {backgroundColor: Theme.palette.secondary.main},
                '& .MuiDataGrid-columnHeaderTitle': {fontWeight: 700},
            }}
        />
    );
}
