export const OUTER_LABELS = ['OTL', 'OTR', 'OBL', 'OBR'] as const;
export type OuterLabel = 'NA' | (typeof OUTER_LABELS)[number];

export const OUTER_ID: Record<Exclude<OuterLabel, 'NA'>, number> = {
  OTL: 10,
  OTR: 11,
  OBL: 12,
  OBR: 13,
};

export const PITCH_TYPES = [
  { key: 'FourSeam', label: 'Four-seam' },
  { key: 'Sinker', label: 'Sinker' },
  { key: 'Slider', label: 'Slider' },
  { key: 'Curveball', label: 'Curveball' },
  { key: 'Changeup', label: 'Changeup' },
  { key: 'Cutter', label: 'Cutter' },
  { key: 'Splitter', label: 'Splitter' },
  { key: 'Other', label: 'Other' },
] as const;

export type PitchKey = (typeof PITCH_TYPES)[number]['key'];
