/*
* Layout used for team pages.
* Queries and displays the team's name and conference.
* 
* author: Braden Mosley
* lastEdit: 04-03-2024
*/

import Box from "@mui/material/Box";
import TeamInfo from '../components/TeamInfo';
import TableTabs from "../components/TableTabs";
import { prisma } from '@/app/utils/db';

export default async function Layout({ children, params }: { children: React.ReactNode, params: { teamName: string } }) {
    const decodedTeamName = decodeURIComponent(params.teamName);
    const team = await prisma.teams.findUnique({
        where: {
            TeamName: decodedTeamName,
        },
    });

    const currentURL = '/the-eye/team/';
    
    return (
        <Box>            
            <Box
                sx={{
                    backgroundColor: '#f5f5f5',
                    paddingLeft: {xs: 4, sm: 8},
                    paddingY: 2,
                    marginTop: '4px',
                }}
            >    
                <TableTabs team = {decodedTeamName}/>
            </Box>

            <Box sx={{paddingX: {xs: 4, sm: 8}, paddingY: 4}}>
                <TeamInfo 
                    name = {team?.DisplayName as string}
                    conference = {team?.Conference as string}
                />
                { children }
            </Box>
            
        </Box>
    );
}