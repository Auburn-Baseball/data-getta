/*
* Landing page for the app when visiting https://datagetta.app
* 
* author: Braden Mosley
* lastEdit: 04-03-2024
*/

'use client'

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Image from 'next/image';
import NextLink from 'next/link';
import Animation from '../public/lineAnimation.gif'
import LoginIcon from '@mui/icons-material/Login';

export default function LandingPage() {
    return (
        <Box sx={{position: 'absolute', width: '100vw', height: '100vh', overflow: 'hidden'}}>
            <Image 
                src = {Animation}
                alt = 'Animation'
                fill = {true}
                objectFit = 'cover'
            />

            <Box
                sx={{
                    display: 'flex',
                    paddingX: 4, paddingY: 2,
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                }}
            >
                <Typography
                    variant = 'h3'
                    sx = {{
                        position: 'relative',
                        color: '#e86100',
                        fontWeight: '700',
                        textWrap: 'nowrap',
                    }}
                >
                    DATA GETTA
                </Typography>

                <Box>
                    <NextLink href = '/the-eye/' passHref legacyBehavior>
                        <Button
                            variant = 'contained'
                            size = 'large'
                            endIcon = {<LoginIcon />}
                            sx = {{backgroundColor: '#e86100', '&:hover': {backgroundColor: '#cc4e0b'}}}
                        >
                            Login
                        </Button>
                    </NextLink>
                </Box>
            </Box>
        </Box>
    );
}