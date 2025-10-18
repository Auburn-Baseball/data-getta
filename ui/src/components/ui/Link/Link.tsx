import * as React from 'react';

import MuiLink from '@mui/material/Link';
import type { LinkProps as MuiLinkProps } from '@mui/material/Link';

import { Link as RouterLink, useLocation } from 'react-router';
import type { LinkProps as RRLinkProps } from 'react-router';

type Props = {
  href: string;
  name: string;
  fontWeight?: number;
  underline?: 'none' | 'hover' | 'always';
  prefetch?: RRLinkProps['prefetch'];
  replace?: RRLinkProps['replace'];
  state?: RRLinkProps['state'];
  preserveSearch?: boolean;
} & Omit<MuiLinkProps, 'href' | 'underline' | 'component' | 'color'>;

export const Link = React.forwardRef<HTMLAnchorElement, Props>(function Link(
  {
    href,
    name,
    fontWeight,
    underline = 'hover',
    prefetch,
    replace,
    state,
    preserveSearch = true,
    sx,
    ...mui
  },
  ref,
) {
  const location = useLocation();

  const to = React.useMemo(() => {
    if (!preserveSearch) {
      return href;
    }

    const currentSearch = location.search;
    if (!currentSearch) {
      return href;
    }

    const [pathPart, hashPart] = href.split('#');
    const [pathname, hrefSearch] = pathPart.split('?');

    const merged = new URLSearchParams(currentSearch);

    if (hrefSearch) {
      const explicit = new URLSearchParams(hrefSearch);
      explicit.forEach((value, key) => {
        merged.set(key, value);
      });
    }

    const searchString = merged.toString();
    const base = `${pathname}${searchString ? `?${searchString}` : ''}`;
    return hashPart ? `${base}#${hashPart}` : base;
  }, [href, location.search, preserveSearch]);

  return (
    <MuiLink
      ref={ref}
      component={RouterLink}
      to={to}
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
