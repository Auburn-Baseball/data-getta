/*
* Page that shows the team's player pitcher stats.
* 
* author: Braden Mosley
* lastEdit: 04-03-2024
*/

import { Suspense } from 'react';
import TableSkeleton from '../../components/TableSkeleton';
import CreatePitcherTable from '../../components/CreatePitcherTable';

export default async function Page({ params }: { params: { teamName: string } }) {    
    const decodedTeamName = decodeURIComponent(params.teamName);

    return (
        <Suspense fallback={<TableSkeleton />}>
            <CreatePitcherTable team = {decodedTeamName}/>
        </Suspense>
    );
}