/*
* Queries to create the run value models.
* 
* author: Braden Mosley
* lastEdit: 04-25-2024
*/

import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { prisma } from '@/app/utils/db';
import PitcherScoreGauge from "@/app/the-eye/player/components/RunValue/PitcherScoreGauge";
import BatterScoreGauge from "@/app/the-eye/player/components/RunValue/BatterScoreGauge";
import CreateBatterComparisonTable from "@/app/the-eye/player/components/RunValue/CreateBatterComparisonTable";
import CreatePitcherComparisonTable from "@/app/the-eye/player/components/RunValue/CreatePitcherComparisonTable";
import { pitcherRunValue_replacer, batterRunValue_replacer } from "@/app/utils/replacer";

export default async function CreateRunValueModels(
    { team, player, opposingTeam }:
    { team: string, player: string, opposingTeam: string })
{

    const batter = await prisma.batter_run_values.findMany({
        where: {
            Batter: player,
            BatterTeam: team,
        },
        orderBy: {
            PitchType: 'asc',
        },
    });

    const pitcher = await prisma.pitcher_run_values.findMany({
        where: {
            Pitcher: player,
            PitcherTeam: team,
        },
        orderBy: {
            PitchType: 'asc',
        },
    });

    if (pitcher.length != 0 && batter.length != 0) {        
        const pitcherResult = JSON.parse(JSON.stringify(pitcher, pitcherRunValue_replacer));
        const batterResult = JSON.parse(JSON.stringify(batter, batterRunValue_replacer));
        return (
            <Box>            
                <PitcherScoreGauge
                    values = {pitcherResult}
                />

                <CreateBatterComparisonTable
                    team = {opposingTeam}
                    pitcher = {pitcherResult}
                />

                <BatterScoreGauge
                    values = {batterResult}
                />

                <CreatePitcherComparisonTable
                    team = {opposingTeam}
                    batter = {batterResult}
                />
            </Box>
        );
    } 
    
    else if (pitcher.length != 0) {        
        const pitcherResult = JSON.parse(JSON.stringify(pitcher, pitcherRunValue_replacer));
        return (
            <Box>            
                <PitcherScoreGauge
                    values = {pitcherResult}
                />

                <CreateBatterComparisonTable
                    team = {opposingTeam}
                    pitcher = {pitcherResult}
                />
            </Box>
        );
    } 
    
    else if (batter.length != 0) {
        const batterResult = JSON.parse(JSON.stringify(batter, batterRunValue_replacer));
        return (
            <Box>            
                <BatterScoreGauge
                    values = {batterResult}
                />

                <CreatePitcherComparisonTable
                    team = {opposingTeam}
                    batter = {batterResult}
                />
            </Box>
        );
    } 
    
    else {        
        return (
            <Typography variant='h6' color = '#d32f2f'><strong>Strikeout!</strong><br/>Something went wrong.</Typography>
        );
    }

}