/*
* Queries the values to create the heat map svgs.
* 
* author: Braden Mosley
* lastEdit: 04-16-2024
*/

import Grid from '@mui/material/Unstable_Grid2';
import PitchTypeHeatMap from './PitchTypeHeatMap';
import { prisma } from '@/app/utils/db';

export default async function CreateHeatMaps(
    {player, team}:
    {player: string, team: string})
{
    // Pitch Types:
    // All, Fastball, Sinker, Changeup, Slider, Curveball, Cutter, Splitter, FourSeamFastball, and TwoSeamFastball

    // Each queries returns an array of an object.
    // The keys in the object are the heat map types.

    // array[0].AllPitches is all pitches.
    // array[0].SuccessfulPitches is successful pitches.
    // array[0].PitchRatio is pitch ratio.

    const all = await prisma.heatmap_model_values.findMany({
        where: {
            Pitcher: player,
            PitcherTeam: team,
            PitchType: 'AllPitchTypes',
        },
        select: {
            AllPitches: true,
            SuccessfulPitches: true,
            PitchRatio: true,
        },
    });
    
    const fastball = await prisma.heatmap_model_values.findMany({
        where: {
            Pitcher: player,
            PitcherTeam: team,
            PitchType: 'Fastball',
        },
        select: {
            AllPitches: true,
            SuccessfulPitches: true,
            PitchRatio: true,
        },
    });

    const sinker = await prisma.heatmap_model_values.findMany({
        where: {
            Pitcher: player,
            PitcherTeam: team,
            PitchType: 'Sinker',
        },
        select: {
            AllPitches: true,
            SuccessfulPitches: true,
            PitchRatio: true,
        },
    });

    const changeup = await prisma.heatmap_model_values.findMany({
        where: {
            Pitcher: player,
            PitcherTeam: team,
            PitchType: 'Changeup',
        },
        select: {
            AllPitches: true,
            SuccessfulPitches: true,
            PitchRatio: true,
        },
    });

    const slider = await prisma.heatmap_model_values.findMany({
        where: {
            Pitcher: player,
            PitcherTeam: team,
            PitchType: 'Slider',
        },
        select: {
            AllPitches: true,
            SuccessfulPitches: true,
            PitchRatio: true,
        },
    });

    const curveball = await prisma.heatmap_model_values.findMany({
        where: {
            Pitcher: player,
            PitcherTeam: team,
            PitchType: 'Curveball',
        },
        select: {
            AllPitches: true,
            SuccessfulPitches: true,
            PitchRatio: true,
        },
    });

    const cutter = await prisma.heatmap_model_values.findMany({
        where: {
            Pitcher: player,
            PitcherTeam: team,
            PitchType: 'Cutter',
        },
        select: {
            AllPitches: true,
            SuccessfulPitches: true,
            PitchRatio: true,
        },
    });

    const splitter = await prisma.heatmap_model_values.findMany({
        where: {
            Pitcher: player,
            PitcherTeam: team,
            PitchType: 'Splitter',
        },
        select: {
            AllPitches: true,
            SuccessfulPitches: true,
            PitchRatio: true,
        },
    });

    const four_seam = await prisma.heatmap_model_values.findMany({
        where: {
            Pitcher: player,
            PitcherTeam: team,
            PitchType: 'FourSeamFastBall',
        },
        select: {
            AllPitches: true,
            SuccessfulPitches: true,
            PitchRatio: true,
        },
    });

    const two_seam = await prisma.heatmap_model_values.findMany({
        where: {
            Pitcher: player,
            PitcherTeam: team,
            PitchType: 'TwoSeamFastBall',
        },
        select: {
            AllPitches: true,
            SuccessfulPitches: true,
            PitchRatio: true,
        },
    });
    
    return (
        <Grid container spacing={2}>
            <PitchTypeHeatMap
                values={JSON.parse(JSON.stringify(all))}
                pitchType='All Pitches'
            />
            <PitchTypeHeatMap
                values={JSON.parse(JSON.stringify(fastball))}
                pitchType='Fastball'
            />
            <PitchTypeHeatMap
                values={JSON.parse(JSON.stringify(sinker))}
                pitchType='Sinker'
            />
            <PitchTypeHeatMap
                values={JSON.parse(JSON.stringify(changeup))}
                pitchType='Changeup'
            />
            <PitchTypeHeatMap
                values={JSON.parse(JSON.stringify(slider))}
                pitchType='Slider'
            />
            <PitchTypeHeatMap
                values={JSON.parse(JSON.stringify(curveball))}
                pitchType='Curveball'
            />
            <PitchTypeHeatMap
                values={JSON.parse(JSON.stringify(cutter))}
                pitchType='Cutter'
            />
            <PitchTypeHeatMap
                values={JSON.parse(JSON.stringify(splitter))}
                pitchType='Splitter'
            />
            <PitchTypeHeatMap
                values={JSON.parse(JSON.stringify(four_seam))}
                pitchType='Four Seam Fastball'
            />
            <PitchTypeHeatMap
                values={JSON.parse(JSON.stringify(two_seam))}
                pitchType='Two Seam Fastball'
            />
        </Grid>
    );
}