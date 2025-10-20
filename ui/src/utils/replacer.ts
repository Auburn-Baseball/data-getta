export const batter_replacer = (key: string, value: unknown) => {
  if (typeof value === 'bigint') {
    return Number(value.toString());
  }

  if (typeof value === 'string') {
    if (key === 'Batter' || key === 'BatterTeam') {
      return value;
    }
    const numeric = Number(value);
    return Number.isFinite(numeric) ? Number(numeric.toFixed(3)) : value;
  }

  return value;
};

export const pitcher_replacer = (key: string, value: unknown) => {
  if (typeof value === 'bigint') {
    return Number(value.toString());
  }

  if (typeof value === 'string') {
    if (key === 'Pitcher' || key === 'PitcherTeam') {
      return value;
    }
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric : value;
  }

  return value;
};

export const pitcherRunValue_replacer = (key: string, value: unknown) => {
  if (typeof value === 'string' && key === 'Score') {
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric : value;
  }

  return value;
};

export const batterRunValue_replacer = (key: string, value: unknown) => {
  if (typeof value === 'string' && (key === 'NumPitches' || key === 'Score')) {
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric : value;
  }

  return value;
};
