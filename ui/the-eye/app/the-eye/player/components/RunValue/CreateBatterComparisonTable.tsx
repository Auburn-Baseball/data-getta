/*
* Queries the batters for the given team to pass to the comparison table.
* 
* author: Braden Mosley
* lastEdit: 04-24-2024
*/

import { prisma } from '@/app/utils/db';
import Box from '@mui/material/Box';
import BatterComparisonTable from './BatterComparisonTable';
import CreateTeamSelect from './CreateTeamSelect';
import { pitcher_run_values } from '@/app/utils/types';
import { batterRunValue_replacer } from '@/app/utils/replacer';

export default async function CreateBatterComparisonTable({team, pitcher}: {team: string, pitcher: pitcher_run_values[]}) {
    const batters = await prisma.batter_run_values.findMany({
        where: {
            BatterTeam: team,
        },
        orderBy: {
            PitchType: 'asc',
        },
    })
    
    return (
        <Box>
            <CreateTeamSelect team = {team} />

            <BatterComparisonTable
                players = {JSON.parse(JSON.stringify(batters, batterRunValue_replacer))}
                pitcher = {pitcher}
            />
        </Box>
        
    );
}