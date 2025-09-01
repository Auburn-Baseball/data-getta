WITH pitcher_stats_subquery AS (
  WITH pitcher_stats_subquery_two AS (
    SELECT
      tp2."Pitcher",
      tp2."PitcherTeam",
      count(*) FILTER (
        WHERE
          (
            (tp2."PlateLocHeight" > 3.55)
            OR (tp2."PlateLocHeight" < 1.77)
            OR (tp2."PlateLocSide" > 0.86)
            OR (tp2."PlateLocSide" < '-0.86' :: numeric)
          )
      ) AS total_out_of_zone_pitches,
      count(*) FILTER (
        WHERE
          (
            (tp2."PlateLocHeight" < 3.55)
            AND (tp2."PlateLocHeight" > 1.77)
            AND (tp2."PlateLocSide" < 0.86)
            AND (tp2."PlateLocSide" > '-0.86' :: numeric)
          )
      ) AS total_in_zone_pitches
    FROM
      trackman_batter tb2,
      trackman_metadata tm2,
      trackman_pitcher tp2,
      seasons s2
    WHERE
      (
        (tb2."PitchUID" = tm2."PitchUID")
        AND (tm2."PitchUID" = tp2."PitchUID")
        AND ((s2."SeasonTitle") :: text = '2024' :: text)
        AND (tm2."UTCDate" >= s2."StartDate")
        AND (tm2."UTCDate" <= s2."EndDate")
      )
    GROUP BY
      tp2."Pitcher",
      tp2."PitcherTeam"
  )
  SELECT
    pss."Pitcher",
    pss."PitcherTeam",
    count(*) FILTER (
      WHERE
        ((tm."KorBB") :: text = 'Strikeout' :: text)
    ) AS total_strikeouts_pitcher,
    count(*) FILTER (
      WHERE
        ((tm."KorBB") :: text = 'Walk' :: text)
    ) AS total_walks_pitcher,
    count(*) FILTER (
      WHERE
        (
          (tp."PlateLocHeight" > 3.55)
          OR (tp."PlateLocHeight" < 1.77)
          OR (tp."PlateLocSide" > 0.86)
          OR (tp."PlateLocSide" < '-0.86' :: numeric)
        )
    ) AS total_out_of_zone_pitches,
    count(*) FILTER (
      WHERE
        (
          ((tm."PitchCall") :: text = 'StrikeSwinging' :: text)
          AND (tp."PlateLocHeight" < 3.55)
          AND (tp."PlateLocHeight" > 1.77)
          AND (tp."PlateLocSide" < 0.86)
          AND (tp."PlateLocSide" > '-0.86' :: numeric)
        )
    ) AS misses_in_zone,
    count(*) FILTER (
      WHERE
        (
          ((tm."PitchCall") :: text = 'StrikeSwinging' :: text)
          OR (
            (tm."PitchCall") :: text = 'FoulBallNotFieldable' :: text
          )
          OR (
            ((tm."PitchCall") :: text = 'InPlay' :: text)
            AND (tp."PlateLocHeight" < 3.55)
            AND (tp."PlateLocHeight" > 1.77)
            AND (tp."PlateLocSide" < 0.86)
            AND (tp."PlateLocSide" > '-0.86' :: numeric)
          )
        )
    ) AS swings_in_zone,
    count(*) FILTER (
      WHERE
        (
          ((tm."PitchCall") :: text = 'StrikeSwinging' :: text)
          OR (
            (
              (tm."PitchCall") :: text = 'FoulBallNotFieldable' :: text
            )
            AND (tp."PlateLocHeight" > 3.55)
            AND (tp."PlateLocHeight" < 1.77)
            AND (tp."PlateLocSide" > 0.86)
            AND (tp."PlateLocSide" < '-0.86' :: numeric)
          )
        )
    ) AS total_num_chases,
    count(*) AS pitches,
    count(DISTINCT tm."GameUID") AS games,
    count(*) FILTER (
      WHERE
        (
          (tm."Inning" = 1)
          AND (tm."Outs" = 0)
          AND (tm."Balls" = 0)
          AND (tm."Strikes" = 0)
          AND (tp."PAofInning" = 1)
        )
    ) AS games_started,
    round(
      (
        (
          (
            (
              count(*) FILTER (
                WHERE
                  ((tm."KorBB") :: text = 'StrikeOut' :: text)
              ) + sum((tm."OutsOnPlay") :: integer)
            ) / 3
          )
        ) :: numeric + (
          (
            (
              (
                count(*) FILTER (
                  WHERE
                    ((tm."KorBB") :: text = 'StrikeOut' :: text)
                ) + sum((tm."OutsOnPlay") :: integer)
              ) % (3) :: bigint
            )
          ) :: numeric / (10) :: numeric
        )
      ),
      1
    ) AS total_innings_pitched,
    count(
      DISTINCT ROW(
        tp."PAofInning",
        tm."Inning",
        tb."Batter",
        tm."GameUID"
      )
    ) AS total_batters_faced,
    CASE
      WHEN (pss.total_in_zone_pitches = 0) THEN NULL :: numeric
      ELSE (
        (
          count(*) FILTER (
            WHERE
              (
                ((tm."PitchCall") :: text = 'StrikeSwinging' :: text)
                AND (tp."PlateLocHeight" < 3.55)
                AND (tp."PlateLocHeight" > 1.77)
                AND (tp."PlateLocSide" < 0.86)
                AND (tp."PlateLocSide" > '-0.86' :: numeric)
              )
          )
        ) :: numeric / (pss.total_in_zone_pitches) :: numeric
      )
    END AS in_zone_whiff_percentage,
    CASE
      WHEN (pss.total_out_of_zone_pitches = 0) THEN NULL :: numeric
      ELSE (
        (
          count(*) FILTER (
            WHERE
              (
                ((tm."PitchCall") :: text = 'StrikeSwinging' :: text)
                OR (
                  (tm."PitchCall") :: text = 'FoulBallNotFieldable' :: text
                )
                OR ((tm."PitchCall") :: text = 'InPlay' :: text)
                OR (tp."PlateLocHeight" > 3.55)
                OR (tp."PlateLocHeight" < 1.77)
                OR (tp."PlateLocSide" > 0.86)
                OR (tp."PlateLocSide" < '-0.86' :: numeric)
              )
          )
        ) :: numeric / (pss.total_out_of_zone_pitches) :: numeric
      )
    END AS chase_percentage
  FROM
    pitcher_stats_subquery_two pss,
    trackman_metadata tm,
    trackman_pitcher tp,
    trackman_batter tb,
    seasons s
  WHERE
    (
      ((pss."Pitcher") :: text = (tp."Pitcher") :: text)
      AND (
        (pss."PitcherTeam") :: text = (tp."PitcherTeam") :: text
      )
      AND (tm."PitchUID" = tp."PitchUID")
      AND (tm."PitchUID" = tb."PitchUID")
      AND ((s."SeasonTitle") :: text = '2024' :: text)
      AND (tm."UTCDate" >= s."StartDate")
      AND (tm."UTCDate" <= s."EndDate")
    )
  GROUP BY
    pss."Pitcher",
    pss."PitcherTeam",
    pss.total_out_of_zone_pitches,
    pss.total_in_zone_pitches
)
SELECT
  "Pitcher",
  "PitcherTeam",
  total_strikeouts_pitcher,
  total_walks_pitcher,
  total_out_of_zone_pitches,
  misses_in_zone,
  swings_in_zone,
  total_num_chases,
  pitches,
  games,
  games_started,
  total_innings_pitched,
  total_batters_faced,
  in_zone_whiff_percentage,
  chase_percentage,
  CASE
    WHEN (total_batters_faced = 0) THEN NULL :: numeric
    ELSE (
      (total_strikeouts_pitcher) :: numeric / (total_batters_faced) :: numeric
    )
  END AS k_percentage,
  CASE
    WHEN (total_batters_faced = 0) THEN NULL :: numeric
    ELSE (
      (total_walks_pitcher) :: numeric / (total_batters_faced) :: numeric
    )
  END AS base_on_ball_percentage
FROM
  pitcher_stats_subquery;