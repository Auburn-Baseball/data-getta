export const batter_replacer = (key: any, value: any) => {
  if (typeof value === 'bigint') {
    return Number(value.toString());
  } else if (typeof value === 'string') {
    if (key === 'Batter' || key === 'BatterTeam') {
      return value;
    } else {
      return Number(Number(value).toFixed(3));
    }
  } else {
    return value;
  }
};

export const pitcher_replacer = (key: any, value: any) => {
  if (typeof value === 'bigint') {
    return Number(value.toString());
  } else if (typeof value === 'string') {
    if (key === 'Pitcher' || key === 'PitcherTeam') {
      return value;
    } else {
      return Number(value);
    }
  } else {
    return value;
  }
};

export const pitcherRunValue_replacer = (key: any, value: any) => {
  if (typeof value === 'string') {
    if (key === 'Score') {
      return Number(value);
    } else {
      return value;
    }
  } else {
    return value;
  }
};

export const batterRunValue_replacer = (key: any, value: any) => {
  if (typeof value === 'string') {
    if (key === 'NumPitches' || key === 'Score') {
      return Number(value);
    } else {
      return value;
    }
  } else {
    return value;
  }
};
