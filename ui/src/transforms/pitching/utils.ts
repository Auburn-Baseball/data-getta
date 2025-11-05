export const inningsToOuts = (innings: number | string | null | undefined): number => {
  if (innings === null || innings === undefined) {
    return 0;
  }

  const numeric =
    typeof innings === 'string'
      ? Number.parseFloat(innings)
      : typeof innings === 'number'
        ? innings
        : Number(innings);

  if (!Number.isFinite(numeric)) {
    return 0;
  }

  const wholeInnings = Math.trunc(numeric);
  const fractional = Number((numeric - wholeInnings).toFixed(2));

  if (fractional === 0) {
    return wholeInnings * 3;
  }

  const tenth = Math.round(fractional * 10);
  if (tenth === 1) {
    return wholeInnings * 3 + 1;
  }
  if (tenth === 2) {
    return wholeInnings * 3 + 2;
  }

  return wholeInnings * 3 + Math.round((numeric - wholeInnings) * 3);
};

export const outsToInnings = (outs: number): number => {
  if (!Number.isFinite(outs) || outs <= 0) {
    return 0;
  }
  const whole = Math.floor(outs / 3);
  const remainder = outs % 3;
  const decimal = remainder === 0 ? 0 : remainder === 1 ? 0.1 : 0.2;
  return Number((whole + decimal).toFixed(1));
};
