/*
* Queries the list for the team selection drop-down.
* 
* author: Braden Mosley
* lastEdit: 04-24-2024
*/

import { prisma } from '@/app/utils/db';
import TeamSelect from './TeamSelect';
import Typography from '@mui/material/Typography';

export default async function CreateTeamSelect({team}: {team: string}) {
    const teamList = await prisma.teams.findMany({
        where: {
            Conference: 'Southeastern Conference'
        },
        select: {
            TeamName: true,
            DisplayName: true,
        },
        orderBy: {
            DisplayName: 'asc',
        },
    });

    const currentTeam = await prisma.teams.findUnique({
        where: {
            TeamName: team,
        },
        select: {
            TeamName: true,
            DisplayName: true,
        },
    });

    if (currentTeam === null) {
        return (
            <Typography variant='h6' color = '#d32f2f'><strong>Strikeout!</strong><br/>Invalid team name.</Typography>
        );
    }
    
    return (
        <TeamSelect
            team = {currentTeam}
            allTeams = {teamList}
        />
    );
}