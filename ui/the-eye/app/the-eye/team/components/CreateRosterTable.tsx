/*
* Queries all of the players for the given team and sorts in alphabetical order.
* Passes this result to the Roster Table.
* 
* author: Braden Mosley
* lastEdit: 04-03-2024
*/

import { prisma } from '@/app/utils/db';
import RosterTable from './RosterTable';

export default async function CreateRosterTable({ team }: { team: string }) {    
    
    const players = await prisma.players.findMany({
        where: {
            TeamName: team,
        },
        orderBy: {
            PlayerName: 'asc',
        },
    });

    return (
        <RosterTable players = {players}/>
    );
}