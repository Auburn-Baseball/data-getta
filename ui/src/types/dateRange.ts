export type DateRange = {
  startDate: string;
  endDate: string;
};

export type SeasonDateRange = DateRange & {
  year: number;
};
