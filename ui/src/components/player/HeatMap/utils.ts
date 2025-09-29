import { PITCH_TYPES, type PitchKey } from './constants';

export const HEATMAP_ZONE_DESCRIPTION =
  'Inner 3x3 cells capture the strike zone while the outer panels collect pitches thrown away from it.';

export const ensureRows = <T>(rows: T[] | null | undefined): T[] => rows ?? [];

export const toNumeric = (value: unknown): number => {
  const numeric = Number(value ?? 0);
  return Number.isFinite(numeric) ? numeric : 0;
};

export const selectedPitchLabel = (key: PitchKey | null): string => {
  if (!key) return 'All pitches';
  return PITCH_TYPES.find((def) => def.key === key)?.label ?? key;
};
