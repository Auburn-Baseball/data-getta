/*
* Link component to be used as the main form of navigation in this app.
* Combines the Next.js and MUI Link components together for a combined link with performance and styling.
* 
* author: Braden Mosley
* lastEdit: 04-03-2024
*/

import NextLink from 'next/link';
import MUI_Link from '@mui/material/Link';

export default function Link(
    {href, name, fontWeight, underline}: 
    {href: string, name: string, fontWeight: number, underline: "none" | "hover" | "always" | undefined}
) {
    return (
        <NextLink href = {href} passHref legacyBehavior>
            <MUI_Link
                color = 'inherit'
                fontWeight = {fontWeight}
                underline = {underline}
            >
                {name}
            </MUI_Link>
        </NextLink>
    )
}