/*
* Queries the values to create the defensive shift svgs.
* 
* author: Braden Mosley
* lastEdit: 04-11-2024
*/

import Grid from '@mui/material/Unstable_Grid2';
import PitchTypeShiftModel from './PitchTypeShiftModel';
import { prisma } from '@/app/utils/db';

export default async function CreateShiftingModels(
    {player, team}:
    {player: string, team: string})
{
    // Pitch Types:
    // Fastball, Sinker, Changeup, Slider, Curveball, Cutter, and Splitter

    // Each queries returns an array of objects.
    // The objects are the ModelValues.

    // array[0] is the left batter side.
    // array[1] is the right batter side.

    const fastball = await prisma.defensive_shift_model_values.findMany({
        where: {
            Pitcher: player,
            PitcherTeam: team,
            PitchType: 'Fastball',
        },
        select: {
            ModelValues: true,
        },
        orderBy: {
            BatterSide: 'asc',
        },
    });

    const sinker = await prisma.defensive_shift_model_values.findMany({
        where: {
            Pitcher: player,
            PitcherTeam: team,
            PitchType: 'Sinker',
        },
        select: {
            ModelValues: true,
        },
        orderBy: {
            BatterSide: 'asc',
        },
    });

    const changeup = await prisma.defensive_shift_model_values.findMany({
        where: {
            Pitcher: player,
            PitcherTeam: team,
            PitchType: 'Changeup',
        },
        select: {
            ModelValues: true,
        },
        orderBy: {
            BatterSide: 'asc',
        },
    });

    const slider = await prisma.defensive_shift_model_values.findMany({
        where: {
            Pitcher: player,
            PitcherTeam: team,
            PitchType: 'Slider',
        },
        select: {
            ModelValues: true,
        },
        orderBy: {
            BatterSide: 'asc',
        },
    });

    const curveball = await prisma.defensive_shift_model_values.findMany({
        where: {
            Pitcher: player,
            PitcherTeam: team,
            PitchType: 'Curveball',
        },
        select: {
            ModelValues: true,
        },
        orderBy: {
            BatterSide: 'asc',
        },
    });

    const cutter = await prisma.defensive_shift_model_values.findMany({
        where: {
            Pitcher: player,
            PitcherTeam: team,
            PitchType: 'Cutter',
        },
        select: {
            ModelValues: true,
        },
        orderBy: {
            BatterSide: 'asc',
        },
    });

    const splitter = await prisma.defensive_shift_model_values.findMany({
        where: {
            Pitcher: player,
            PitcherTeam: team,
            PitchType: 'Splitter',
        },
        select: {
            ModelValues: true,
        },
        orderBy: {
            BatterSide: 'asc',
        },
    });
    
    return (
        <Grid container spacing={2}>
            <PitchTypeShiftModel
                values={JSON.parse(JSON.stringify(fastball))}
                pitchType='Fastball'
            />
            <PitchTypeShiftModel
                values={JSON.parse(JSON.stringify(sinker))}
                pitchType='Sinker'
            />
            <PitchTypeShiftModel
                values={JSON.parse(JSON.stringify(changeup))}
                pitchType='Changeup'
            />
            <PitchTypeShiftModel
                values={JSON.parse(JSON.stringify(slider))}
                pitchType='Slider'
            />
            <PitchTypeShiftModel
                values={JSON.parse(JSON.stringify(curveball))}
                pitchType='Curveball'
            />
            <PitchTypeShiftModel
                values={JSON.parse(JSON.stringify(cutter))}
                pitchType='Cutter'
            />
            <PitchTypeShiftModel
                values={JSON.parse(JSON.stringify(splitter))}
                pitchType='Splitter'
            />
        </Grid>
    );
}