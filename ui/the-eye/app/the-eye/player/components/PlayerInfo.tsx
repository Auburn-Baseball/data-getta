/*
* Displays the player's name and team.
* 
* author: Braden Mosley
* lastEdit: 04-15-2024
*/

import Box from "@mui/material/Box";
import Typography from '@mui/material/Typography';

export default function PlayerInfo(
    { name, team }:
    { name: string, team: string }) {
        
        console.log(name);
        const playerName = name.split(/(?=[A-Z])/);
        

        return (
            <Box>
                <Typography variant='h4' fontWeight={700}>{playerName[1] + ' ' + playerName[0]}</Typography>
                <Typography variant='h6' fontWeight={600}>{team}</Typography>
            </Box>
            
        );
    }