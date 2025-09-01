/*
* Loading skeleton used for player stat/model components.
* 
* author: Braden Mosley
* lastEdit: 04-15-2024
*/

import Skeleton from '@mui/material/Skeleton';

export default function StatsTableSkeleton() {
    return (
        <>
            <Skeleton variant = 'rounded' width = '100%' height = '350px' animation = 'wave' />
        </>
    )
}