/*
* Determines whether the player is a pitcher or batter
* and creates the corresponding diagrams.
* 
* author: Braden Mosley
* lastEdit: 04-15-2024
*/

import { prisma } from '@/app/utils/db';
import { batter_stats, pitcher_stats, pitch_sums } from "@/app/utils/types";
import { batter_replacer, pitcher_replacer } from '@/app/utils/replacer';
import Grid from '@mui/material/Unstable_Grid2';
import { Typography } from '@mui/material';
import CreateBatterDiagrams from './Batting/CreateBatterDiagrams';
import CreatePitcherDiagrams from './Pitching/CreatePitcherDiagrams';

export default async function CreateStatsDiagrams(
    {player, team, startDate, endDate}:
    {player: string, team: string, startDate: string, endDate: string})
{    
    // https://www.prisma.io/docs/orm/more/upgrade-guides/upgrading-versions/upgrading-to-prisma-4#raw-query-mapping-postgresql-type-casts
    // In SQL function, get_batter_stats takes the params (text, text, date, date)
    // ::date explicitly casts the startDate and endDate strings to a SQL date type
    
    const batter = await prisma.$queryRaw<batter_stats[]>`SELECT * FROM get_batter_stats(${player}, ${team}, ${startDate}::date, ${endDate}::date)`;
    const pitcher = await prisma.$queryRaw<pitcher_stats[]>`SELECT * FROM get_pitcher_stats(${player}, ${team}, ${startDate}::date, ${endDate}::date)`;
    const pitches = await prisma.$queryRaw<pitch_sums[]>`SELECT * FROM get_pitch_count(${player}, ${team}, ${startDate}::date, ${endDate}::date)`;
    
    if (batter.length != 0 && pitcher.length != 0) {        
        return (
            <Grid container spacing={2}>
                <CreateBatterDiagrams stats = {JSON.parse(JSON.stringify(batter, batter_replacer))} />

                <CreatePitcherDiagrams
                    stats = {JSON.parse(JSON.stringify(pitcher, pitcher_replacer))}
                    sums = {JSON.parse(JSON.stringify(pitches, pitcher_replacer))}
                />
            </Grid>
        );
    } 
    
    else if (batter.length != 0) {
        return (
            <Grid container spacing={2}>
                <CreateBatterDiagrams stats = {JSON.parse(JSON.stringify(batter, batter_replacer))} />
            </Grid>
        );
    } 
    
    else if (pitcher.length != 0) {        
        return (
            <Grid container spacing={2}>
                <CreatePitcherDiagrams
                    stats = {JSON.parse(JSON.stringify(pitcher, pitcher_replacer))}
                    sums = {JSON.parse(JSON.stringify(pitches, pitcher_replacer))}
                />
            </Grid>
        );
    } 
    
    else {        
        return (
            <Typography variant='h6' color = '#d32f2f'><strong>Strikeout!</strong><br/>No stats found for this date range.</Typography>
        );
    }


}