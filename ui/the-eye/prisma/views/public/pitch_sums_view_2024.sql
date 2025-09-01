SELECT
  tp."Pitcher",
  tp."PitcherTeam",
  count(*) AS total_pitches,
  count(*) FILTER (
    WHERE
      ((tp."AutoPitchType") :: text = 'Curveball' :: text)
  ) AS curveball_count,
  count(*) FILTER (
    WHERE
      ((tp."AutoPitchType") :: text = 'Four-Seam' :: text)
  ) AS fourseam_count,
  count(*) FILTER (
    WHERE
      ((tp."AutoPitchType") :: text = 'Sinker' :: text)
  ) AS sinker_count,
  count(*) FILTER (
    WHERE
      ((tp."AutoPitchType") :: text = 'Slider' :: text)
  ) AS slider_count,
  count(*) FILTER (
    WHERE
      (
        ((tp."TaggedPitchType") :: text = 'Fastball' :: text)
        AND ((tp."AutoPitchType") :: text <> 'Four-Seam' :: text)
      )
  ) AS twoseam_count,
  count(*) FILTER (
    WHERE
      ((tp."AutoPitchType") :: text = 'Changeup' :: text)
  ) AS changeup_count,
  count(*) FILTER (
    WHERE
      ((tp."AutoPitchType") :: text = 'Cutter' :: text)
  ) AS cutter_count,
  count(*) FILTER (
    WHERE
      ((tp."AutoPitchType") :: text = 'Splitter' :: text)
  ) AS splitter_count,
  count(*) FILTER (
    WHERE
      (
        ((tp."AutoPitchType") :: text = 'Other' :: text)
        OR ((tp."AutoPitchType") :: text = 'NaN' :: text)
      )
  ) AS other_count
FROM
  trackman_pitcher tp,
  trackman_metadata tm,
  seasons s
WHERE
  (
    (tm."PitchUID" = tp."PitchUID")
    AND ((s."SeasonTitle") :: text = '2024' :: text)
    AND (tm."UTCDate" >= s."StartDate")
    AND (tm."UTCDate" <= s."EndDate")
  )
GROUP BY
  tp."Pitcher",
  tp."PitcherTeam";