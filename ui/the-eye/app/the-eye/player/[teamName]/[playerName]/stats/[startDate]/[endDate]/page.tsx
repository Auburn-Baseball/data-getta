/*
* Page to show a player's stats.
* 
* author: Braden Mosley
* lastEdit: 04-15-2024
*/

import Box from "@mui/material/Box";
import { Suspense } from 'react';
import DateSelector from "@/app/the-eye/player/components/DateSelector";
import CreateStatsDiagrams from "@/app/the-eye/player/components/CreateStatsDiagrams";
import StatsTableSkeleton from "@/app/the-eye/player/components/StatsTableSkeleton";

export default function Page (
    { params }:
    { params: { teamName: string, playerName: string, startDate: string, endDate: string } })
{
    const decodedTeamName = decodeURIComponent(params.teamName);
    const decodedPlayerName = decodeURIComponent(params.playerName);
    
    return(
        <Box sx={{paddingY: 2}}>
            <DateSelector
                start = {params.startDate}
                end = {params.endDate}
            />

            <Box sx={{paddingTop: 2}}>
                <Suspense fallback={<StatsTableSkeleton />}>
                    <CreateStatsDiagrams
                        player = {decodedPlayerName}
                        team = {decodedTeamName}
                        startDate = {params.startDate}
                        endDate = {params.endDate}
                    />
                </Suspense>
            </Box>
            
        </Box>
    );

}