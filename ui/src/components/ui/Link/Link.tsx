import * as React from 'react';

import MuiLink from '@mui/material/Link';
import type { LinkProps as MuiLinkProps } from '@mui/material/Link';

import { Link as RouterLink } from 'react-router';
import type { LinkProps as RRLinkProps } from 'react-router';

type Props = {
  href: string;
  name: string;
  fontWeight?: number;
  underline?: 'none' | 'hover' | 'always';
  prefetch?: RRLinkProps['prefetch'];
  replace?: RRLinkProps['replace'];
  state?: RRLinkProps['state'];
} & Omit<MuiLinkProps, 'href' | 'underline' | 'component' | 'color'>;

export const Link = React.forwardRef<HTMLAnchorElement, Props>(function Link(
  { href, name, fontWeight, underline = 'hover', prefetch, replace, state, sx, ...mui },
  ref,
) {
  return (
    <MuiLink
      ref={ref}
      component={RouterLink}
      to={href}
      prefetch={prefetch}
      replace={replace}
      state={state}
      underline={underline}
      color="inherit"
      sx={{ fontWeight, ...sx }}
      {...mui}
    >
      {name}
    </MuiLink>
  );
});

export default Link;
