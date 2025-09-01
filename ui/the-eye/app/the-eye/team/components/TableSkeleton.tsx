/*
* Loading skeleton used while tables are being populated.
* Used with React Suspense.
* 
* author: Braden Mosley
* lastEdit: 04-03-2024
*/

import Skeleton from '@mui/material/Skeleton';

export default function TableSkeleton() {
    return (
        <>
            <Skeleton variant = 'rounded' width = '100%' height = '350px' animation = 'wave' />
        </>
    )
}