/*
* Queries the pitcher_stats_view and the pitch_sums_view for the given team.
* Passes these result to their corresponding tables.
* 
* author: Braden Mosley
* lastEdit: 04-03-2024
*/

import { prisma } from '@/app/utils/db';
import { pitcher_replacer } from '@/app/utils/replacer';
import { pitcher_stats, pitch_sums } from '@/app/utils/types';
import PitcherTable from './PitcherTable';
import PitchSumsTable from './PitchSumsTable';
import Box from '@mui/material/Box';

export default async function CreatePitcherTable({ team }: { team: string }) {    
    const pitchers = await prisma.$queryRaw<pitcher_stats[]>`SELECT * FROM pitcher_stats_view_2024 WHERE "PitcherTeam" = ${team}`;
    const pitches = await prisma.$queryRaw<pitch_sums[]>`SELECT * FROM pitch_sums_view_2024 WHERE "PitcherTeam" = ${team}`;

    return (
        <Box>
            <PitcherTable players={JSON.parse(JSON.stringify(pitchers, pitcher_replacer))}/>
            <PitchSumsTable players={JSON.parse(JSON.stringify(pitches, pitcher_replacer))}/>
        </Box>
    );
}