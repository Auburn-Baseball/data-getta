WITH at_bats_subquery AS (
  WITH hits_subquery AS (
    SELECT
      tb_1."Batter",
      tb_1."BatterTeam",
      count(*) FILTER (
        WHERE
          (
            ((tm_1."PlayResult") :: text = 'Single' :: text)
            OR ((tm_1."PlayResult") :: text = 'Double' :: text)
            OR ((tm_1."PlayResult") :: text = 'Triple' :: text)
            OR ((tm_1."PlayResult") :: text = 'HomeRun' :: text)
          )
      ) AS hits,
      count(*) FILTER (
        WHERE
          (
            ((tm_1."PlayResult") :: text = 'Error' :: text)
            OR ((tm_1."PlayResult") :: text = 'Out' :: text)
            OR (
              (tm_1."PlayResult") :: text = 'FieldersChoice' :: text
            )
            OR ((tm_1."KorBB") :: text = 'Strikeout' :: text)
            OR ((tm_1."PlayResult") :: text = 'Single' :: text)
            OR ((tm_1."PlayResult") :: text = 'Double' :: text)
            OR ((tm_1."PlayResult") :: text = 'Triple' :: text)
            OR ((tm_1."PlayResult") :: text = 'HomeRun' :: text)
          )
      ) AS at_bats,
      count(*) FILTER (
        WHERE
          (
            (tp_1."PlateLocHeight" > 3.55)
            OR (tp_1."PlateLocHeight" < 1.77)
            OR (tp_1."PlateLocSide" > 0.86)
            OR (tp_1."PlateLocSide" < '-0.86' :: numeric)
          )
      ) AS total_out_of_zone_pitches,
      count(*) FILTER (
        WHERE
          (
            (tp_1."PlateLocHeight" < 3.55)
            AND (tp_1."PlateLocHeight" > 1.77)
            AND (tp_1."PlateLocSide" < 0.86)
            AND (tp_1."PlateLocSide" > '-0.86' :: numeric)
          )
      ) AS total_in_zone_pitches
    FROM
      trackman_metadata tm_1,
      trackman_batter tb_1,
      trackman_pitcher tp_1,
      seasons s_1
    WHERE
      (
        (tm_1."PitchUID" = tb_1."PitchUID")
        AND (tb_1."PitchUID" = tp_1."PitchUID")
        AND ((s_1."SeasonTitle") :: text = '2024' :: text)
        AND (tm_1."UTCDate" >= s_1."StartDate")
        AND (tm_1."UTCDate" <= s_1."EndDate")
      )
    GROUP BY
      tb_1."Batter",
      tb_1."BatterTeam"
  )
  SELECT
    tb."Batter",
    tb."BatterTeam",
    hs.hits,
    hs.at_bats,
    count(*) FILTER (
      WHERE
        (
          ((tm."PitchCall") :: text = 'StrikeCalled' :: text)
          OR ((tm."PitchCall") :: text = 'StrikeSwinging' :: text)
          OR (
            (tm."PitchCall") :: text = 'FoulBallNotFieldable' :: text
          )
        )
    ) AS strikes,
    count(*) FILTER (
      WHERE
        ((tm."KorBB") :: text = 'Walk' :: text)
    ) AS walks,
    count(*) FILTER (
      WHERE
        ((tm."KorBB") :: text = 'Strikeout' :: text)
    ) AS strikeouts,
    count(*) FILTER (
      WHERE
        ((tm."PlayResult") :: text = 'HomeRun' :: text)
    ) AS homeruns,
    count(*) FILTER (
      WHERE
        (
          ((tm."PlayResult") :: text = 'Double' :: text)
          OR ((tm."PlayResult") :: text = 'Triple' :: text)
          OR ((tm."PlayResult") :: text = 'HomeRun' :: text)
        )
    ) AS extra_base_hits,
    count(*) FILTER (
      WHERE
        (
          ((tm."KorBB") :: text = 'Walk' :: text)
          OR ((tm."PitchCall") :: text = 'InPlay' :: text)
          OR ((tm."PitchCall") :: text = 'HitByPitch' :: text)
          OR ((tm."KorBB") :: text = 'Strikeout' :: text)
        )
    ) AS plate_appearances,
    count(*) FILTER (
      WHERE
        ((tm."PitchCall") :: text = 'HitByPitch' :: text)
    ) AS hit_by_pitch,
    count(*) FILTER (
      WHERE
        ((tm."PlayResult") :: text = 'Sacrifice' :: text)
    ) AS sacrifice,
    sum(
      CASE
        WHEN ((tm."PlayResult") :: text = 'Single' :: text) THEN 1
        WHEN ((tm."PlayResult") :: text = 'Double' :: text) THEN 2
        WHEN ((tm."PlayResult") :: text = 'Triple' :: text) THEN 3
        WHEN ((tm."PlayResult") :: text = 'HomeRun' :: text) THEN 4
        ELSE 0
      END
    ) AS total_bases,
    CASE
      WHEN (hs.at_bats = 0) THEN NULL :: numeric
      ELSE (
        (
          (
            hs.hits + count(*) FILTER (
              WHERE
                (
                  ((tm."KorBB") :: text = 'Walk' :: text)
                  OR ((tm."PitchCall") :: text = 'HitByPitch' :: text)
                )
            )
          )
        ) :: numeric / (
          (
            (
              (
                count(*) FILTER (
                  WHERE
                    (
                      ((tm."PlayResult") :: text = 'Error' :: text)
                      OR ((tm."PlayResult") :: text = 'Out' :: text)
                      OR ((tm."PlayResult") :: text = 'FieldersChoice' :: text)
                      OR ((tm."KorBB") :: text = 'Strikeout' :: text)
                    )
                ) + hs.hits
              ) + count(*) FILTER (
                WHERE
                  (
                    ((tm."KorBB") :: text = 'Walk' :: text)
                    OR ((tm."PitchCall") :: text = 'HitByPitch' :: text)
                  )
              )
            ) + count(*) FILTER (
              WHERE
                (
                  ((tm."PlayResult") :: text = 'Sacrifice' :: text)
                  AND ((tm."TaggedHitType") :: text = 'FlyBall' :: text)
                )
            )
          )
        ) :: numeric
      )
    END AS on_base_percentage,
    CASE
      WHEN (hs.at_bats = 0) THEN NULL :: numeric
      ELSE (
        (
          sum(
            CASE
              WHEN ((tm."PlayResult") :: text = 'Single' :: text) THEN 1
              WHEN ((tm."PlayResult") :: text = 'Double' :: text) THEN 2
              WHEN ((tm."PlayResult") :: text = 'Triple' :: text) THEN 3
              WHEN ((tm."PlayResult") :: text = 'HomeRun' :: text) THEN 4
              ELSE 0
            END
          )
        ) :: numeric / (hs.at_bats) :: numeric
      )
    END AS slugging_percentage,
    CASE
      WHEN (hs.total_out_of_zone_pitches = 0) THEN NULL :: numeric
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
        ) :: numeric / (hs.total_out_of_zone_pitches) :: numeric
      )
    END AS chase_percentage,
    CASE
      WHEN (hs.total_in_zone_pitches = 0) THEN NULL :: numeric
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
        ) :: numeric / (hs.total_in_zone_pitches) :: numeric
      )
    END AS in_zone_whiff_percentage,
    count(DISTINCT tm."GameUID") AS games
  FROM
    hits_subquery hs,
    trackman_batter tb,
    trackman_metadata tm,
    trackman_pitcher tp,
    seasons s
  WHERE
    (
      ((hs."Batter") :: text = (tb."Batter") :: text)
      AND (
        (hs."BatterTeam") :: text = (tb."BatterTeam") :: text
      )
      AND (tb."PitchUID" = tm."PitchUID")
      AND (tm."PitchUID" = tp."PitchUID")
      AND ((s."SeasonTitle") :: text = '2024' :: text)
      AND (tm."UTCDate" >= s."StartDate")
      AND (tm."UTCDate" <= s."EndDate")
    )
  GROUP BY
    tb."Batter",
    tb."BatterTeam",
    hs.hits,
    hs.at_bats,
    hs.total_out_of_zone_pitches,
    hs.total_in_zone_pitches
)
SELECT
  "Batter",
  "BatterTeam",
  hits,
  at_bats,
  strikes,
  walks,
  strikeouts,
  homeruns,
  extra_base_hits,
  plate_appearances,
  hit_by_pitch,
  sacrifice,
  total_bases,
  on_base_percentage,
  slugging_percentage,
  chase_percentage,
  in_zone_whiff_percentage,
  games,
  CASE
    WHEN (at_bats = 0) THEN NULL :: numeric
    ELSE ((hits) :: numeric / (at_bats) :: numeric)
  END AS batting_average,
  (on_base_percentage + slugging_percentage) AS onbase_plus_slugging,
  (
    slugging_percentage - CASE
      WHEN (at_bats = 0) THEN NULL :: numeric
      ELSE ((hits) :: numeric / (at_bats) :: numeric)
    END
  ) AS isolated_power,
  CASE
    WHEN (plate_appearances = 0) THEN NULL :: numeric
    ELSE (
      (strikeouts) :: numeric / (plate_appearances) :: numeric
    )
  END AS k_percentage,
  CASE
    WHEN (plate_appearances = 0) THEN NULL :: numeric
    ELSE ((walks) :: numeric / (plate_appearances) :: numeric)
  END AS base_on_ball_percentage
FROM
  at_bats_subquery;