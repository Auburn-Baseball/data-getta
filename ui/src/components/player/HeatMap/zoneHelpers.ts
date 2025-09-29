import type { OuterLabel } from './constants';
import { OUTER_ID, OUTER_LABELS } from './constants';

export type BaseZone = {
  zoneId: number;
  inZone: boolean;
  zoneRow: number;
  zoneCol: number;
  zoneCell: number;
  outerLabel: OuterLabel;
};

export type ZoneMeta = BaseZone;

const INNER_ZONE_METAS: ZoneMeta[] = (() => {
  const metas: ZoneMeta[] = [];
  for (let row = 1; row <= 3; row++) {
    for (let col = 1; col <= 3; col++) {
      const cell = (row - 1) * 3 + col;
      metas.push({
        zoneId: cell,
        inZone: true,
        zoneRow: row,
        zoneCol: col,
        zoneCell: cell,
        outerLabel: 'NA',
      } as ZoneMeta);
    }
  }
  return metas;
})();

const OUTER_ZONE_METAS: ZoneMeta[] = OUTER_LABELS.map((label) => ({
  zoneId: OUTER_ID[label],
  inZone: false,
  zoneRow: 0,
  zoneCol: 0,
  zoneCell: 0,
  outerLabel: label,
}));

const ALL_ZONE_METAS: ZoneMeta[] = [...INNER_ZONE_METAS, ...OUTER_ZONE_METAS];

export function buildZoneMap<T extends BaseZone>(
  bins: T[],
  createEmpty: (meta: ZoneMeta) => T,
): Map<number, T> {
  const map = new Map<number, T>();
  ALL_ZONE_METAS.forEach((meta) => {
    map.set(meta.zoneId, createEmpty(meta));
  });

  bins.forEach((bin) => {
    map.set(bin.zoneId, bin);
  });

  return map;
}

export function zoneValuesArray<T extends BaseZone>(zoneMap: Map<number, T>): T[] {
  return Array.from(zoneMap.values());
}
