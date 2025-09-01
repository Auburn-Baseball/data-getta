SELECT
  "Pitcher",
  "PitcherTeam",
  "PitcherThrows",
  CASE
    WHEN (
      (("TaggedPitchType") :: text = 'Fastball' :: text)
      AND (("AutoPitchType") :: text <> 'Four-Seam' :: text)
    ) THEN 'Sinker' :: character varying
    WHEN (("AutoPitchType") :: text = 'Four-Seam' :: text) THEN 'Fastball' :: character varying
    ELSE "AutoPitchType"
  END AS "PitchType",
  avg("RelSpeed") AS avg_rel_speed,
  avg("InducedVert") AS avg_induced_vert,
  avg("HorzBreak") AS avg_horz_break,
  avg("RelHeight") AS avg_rel_height,
  avg("RelSide") AS avg_rel_side,
  avg("Extension") AS avg_extension,
  avg("SpinRate") AS avg_spin_rate,
  avg("SpinAxis") AS avg_spin_axis,
  avg("VertApprAngle") AS avg_vert_appr_angle,
  avg("HorzApprAngle") AS avg_horz_appr_angle
FROM
  trackman_pitcher
WHERE
  (
    (("PitcherThrows") :: text <> 'Undefined' :: text)
    AND (("AutoPitchType") :: text <> '' :: text)
    AND (("AutoPitchType") :: text <> 'NaN' :: text)
    AND ("RelSpeed" <> 'NaN' :: numeric)
    AND ("InducedVert" <> 'NaN' :: numeric)
    AND ("HorzBreak" <> 'NaN' :: numeric)
    AND ("RelHeight" <> 'NaN' :: numeric)
    AND ("RelSide" <> 'NaN' :: numeric)
    AND ("Extension" <> 'NaN' :: numeric)
    AND ("SpinRate" <> 'NaN' :: numeric)
    AND ("SpinAxis" <> 'NaN' :: numeric)
    AND ("VertApprAngle" <> 'NaN' :: numeric)
    AND ("HorzApprAngle" <> 'NaN' :: numeric)
  )
GROUP BY
  "Pitcher",
  "PitcherTeam",
  "PitcherThrows",
  CASE
    WHEN (
      (("TaggedPitchType") :: text = 'Fastball' :: text)
      AND (("AutoPitchType") :: text <> 'Four-Seam' :: text)
    ) THEN 'Sinker' :: character varying
    WHEN (("AutoPitchType") :: text = 'Four-Seam' :: text) THEN 'Fastball' :: character varying
    ELSE "AutoPitchType"
  END;