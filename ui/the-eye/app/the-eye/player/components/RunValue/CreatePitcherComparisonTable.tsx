/*
* Queries the pitchers for the given team to pass to the comparison table.
* 
* author: Braden Mosley
* lastEdit: 04-24-2024
*/

import { prisma } from '@/app/utils/db';
import Box from '@mui/material/Box';
import PitcherComparisonTable from './PitcherComparisonTable';
import CreateTeamSelect from './CreateTeamSelect';
import { batter_run_values } from '@/app/utils/types';
import { pitcherRunValue_replacer } from '@/app/utils/replacer';

export default async function CreatePitcherComparisonTable({team, batter}: {team: string, batter: batter_run_values[]}) {
    const pitchers = await prisma.pitcher_run_values.findMany({
        where: {
            PitcherTeam: team,
        },
        orderBy: {
            PitchType: 'asc',
        },
    })
    
    return (
        <Box>
            <CreateTeamSelect team = {team} />

            <PitcherComparisonTable
                players = {JSON.parse(JSON.stringify(pitchers, pitcherRunValue_replacer))}
                batter = {batter}
            />
        </Box>
        
    );
}