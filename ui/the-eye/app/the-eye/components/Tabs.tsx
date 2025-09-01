/*
* Tabs used in the side bars.
* Created based on MUI examples.
* 
* author: Braden Mosley
* lastEdit: 04-03-2024
*/

import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import GroupsIcon from '@mui/icons-material/Groups';
import { common } from "@mui/material/colors";
import { Theme } from '@/app/utils/theme';

import Image from 'next/image';
import logo from './assets/au_logo_onecolor_white.svg'

export default function Tabs() {
    return (
        <List>

            <ListItem disablePadding sx={{paddingBottom: 2}}>
                <ListItemButton
                    sx={{
                        gap: 2,
                        justifyContent: 'center',
                        ':hover': {bgcolor: Theme.palette.primary.light,}
                    }}
                    href="/the-eye/team/AUB_TIG/roster"
                >
                    <ListItemIcon sx={{minWidth: 'auto'}}>
                        <Image
                            src = {logo}
                            width = {24}
                            height = {24}
                            alt = "auburn logo"
                        />
                    </ListItemIcon>
                    <ListItemText sx={{'& .MuiTypography-root':{fontWeight: 'bold'}, flexGrow: 0}}>Auburn</ListItemText>
                </ListItemButton>
            </ListItem>

            <ListItem disablePadding sx={{paddingBottom: 2}}>
                <ListItemButton
                    sx={{
                        gap: 2,
                        justifyContent: 'center',
                        ':hover': {bgcolor: Theme.palette.primary.light,}
                    }}
                    href="/the-eye"
                    >
                    <ListItemIcon sx={{minWidth: 'auto'}}>
                        <GroupsIcon sx = {{ color: common.white }}/>
                    </ListItemIcon>
                    <ListItemText sx={{'& .MuiTypography-root':{fontWeight: 'bold'}, flexGrow: 0}}>Teams</ListItemText>
                </ListItemButton>
            </ListItem>

        </List>
    );
}