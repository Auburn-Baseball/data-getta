/*
* The home page for the app.
* Displays each of the conferences and the teams in each conference.
* 
* author: Braden Mosley
* lastEdit: 04-03-2024
*/

import Grid from '@mui/material/Unstable_Grid2';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import ConferenceTable from './components/ConferenceTable';
import { prisma } from '@/app/utils/db';

export default async function ConferencePage() {
    // Queries all conferences and their relating teams.
    const conferences = await prisma.conferences.findMany({
        include: {
            teams: {
                select: {
                    TeamName: true,
                    DisplayName: true,
                },
                orderBy: {
                    DisplayName: 'asc',
                },
            },
        },
    });

    return (
        <Box
            sx={{
                paddingX: 8, paddingY: 4
            }}
        >
            <Typography variant='h4' fontWeight={700} sx={{paddingBottom: 4}}>Conferences</Typography>

            <Grid container spacing={2}>
                {/* Creates all the conference tables from the conferences' query above */}
                {conferences.map((conf, index) => 
                    <Grid sm={12} md={6} xl={4} key={index} sx={{width: '100%'}}>
                        <ConferenceTable
                            name = {conf.ConferenceName}
                            teams = {conf.teams}
                        />
                    </Grid>
                )}
            </Grid>
        </Box>
    );
}