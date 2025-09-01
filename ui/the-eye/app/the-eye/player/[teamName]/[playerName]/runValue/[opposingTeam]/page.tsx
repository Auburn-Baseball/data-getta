/*
* Page for the run value model.
* 
* author: Braden Mosley
* lastEdit: 04-25-2024
*/

import { Suspense } from "react";
import StatsTableSkeleton from "@/app/the-eye/player/components/StatsTableSkeleton";
import CreateRunValueModels from "@/app/the-eye/player/components/RunValue/CreateRunValueModels";

export default function Page(
    { params }:
    { params: { teamName: string, playerName: string, opposingTeam: string } })
{

    const decodedTeamName = decodeURIComponent(params.teamName);
    const decodedPlayerName = decodeURIComponent(params.playerName);
    const decodedOpposingTeam = decodeURIComponent(params.opposingTeam);

    return (
        <Suspense fallback={<StatsTableSkeleton />}>
            <CreateRunValueModels
                team = {decodedTeamName}
                player = {decodedPlayerName}
                opposingTeam = {decodedOpposingTeam}
            />
        </Suspense>
    );


}