/*
* Layout for player pages.
*
* Displays the player's name and team
* and the tabs for each model for the player.
* 
* author: Braden Mosley
* lastEdit: 04-15-2024
*/

import Box from "@mui/material/Box";
import PlayerInfo from '../../components/PlayerInfo';
import ModelTabs from "../../components/ModelTabs";
import { prisma } from '@/app/utils/db';

export default async function Layout(
    { children, params }:
    { children: React.ReactNode, params: { teamName: string, playerName: string } })
{
    const decodedTeamName = decodeURIComponent(params.teamName);
    const decodedPlayerName = decodeURIComponent(params.playerName);
    
    const player = await prisma.players.findUnique({
        where: {
            PlayerName_TeamName: {PlayerName: decodedPlayerName, TeamName: decodedTeamName},
        },
        include: {
            teams: true,
        }
    });

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
                <ModelTabs team = {decodedTeamName} player = {decodedPlayerName}/>
            </Box>

            <Box sx={{paddingX: {xs: 4, sm: 8}, paddingY: 4}}>
                <PlayerInfo 
                    name = {player?.PlayerName as string}
                    team = {player?.teams.DisplayName as string}
                />
                { children }
            </Box>
        </Box>
    );
}