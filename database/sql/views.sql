-- Holds the pitch data for the 2024 season
drop view if exists pitch_sums_view_2024;
create or replace view pitch_sums_view_2024 as
select "Pitcher" , "PitcherTeam",
         COUNT(*) as total_pitches,
         COUNT(*) filter (where tp."AutoPitchType" = 'Curveball') as curveball_count,
         COUNT(*) filter (where tp."AutoPitchType" = 'Four-Seam') as fourseam_count,
            COUNT(*) filter (where tp."AutoPitchType" = 'Sinker') as sinker_count,
            COUNT(*) filter (where tp."AutoPitchType" = 'Slider') as slider_count,
            COUNT(*) filter (where tp."TaggedPitchType" = 'Fastball' and "AutoPitchType" != 'Four-Seam') as twoseam_count,
            COUNT(*) filter (where tp."AutoPitchType" = 'Changeup') as changeup_count,
            COUNT(*) filter (where tp."AutoPitchType" = 'Cutter') as cutter_count,
            COUNT(*) filter (where tp."AutoPitchType" = 'Splitter') as splitter_count,
            COUNT(*) filter (where tp."AutoPitchType" = 'Other' or tp."AutoPitchType" = 'NaN') as other_count
from trackman_pitcher tp, trackman_metadata tm, seasons s
where tm."PitchUID" = tp."PitchUID" and s."SeasonTitle" = '2024' and tm."UTCDate" >= s."StartDate" and tm."UTCDate" <= s."EndDate"
group by ("Pitcher", "PitcherTeam");

-- Values AU Baseball uses for strike zone
-- min_plate_side = -0.86
-- max_plate_side = 0.86
-- max_plate_height = 3.55
-- min_plate_height = 1.77

-- Holds the batter stats for the 2024 season
drop view if exists batter_stats_view_2024;
create or replace view batter_stats_view_2024 as
with at_bats_subquery as (
    with hits_subquery as (
        select "Batter", "BatterTeam",
                COUNT(*) filter (where "PlayResult" = 'Single'
                                or "PlayResult" = 'Double'
                                or "PlayResult" = 'Triple'
                                or "PlayResult" = 'HomeRun'
                ) as hits,
                COUNT(*) filter (where "PlayResult" = 'Error'
                                or "PlayResult" = 'Out'
                                or "PlayResult" = 'FieldersChoice'
                                or "KorBB" = 'Strikeout'
                                or "PlayResult" = 'Single'
                                or "PlayResult" = 'Double'
                                or "PlayResult" = 'Triple'
                                or "PlayResult" = 'HomeRun'
                                ) as at_bats,
                COUNT(*) filter (where "PlateLocHeight" > 3.55
                                or "PlateLocHeight" < 1.77
                                or "PlateLocSide" > 0.86
                                or "PlateLocSide" < -0.86
                                ) as total_out_of_zone_pitches,
                COUNT(*) filter (where "PlateLocHeight" < 3.55
                                and "PlateLocHeight" > 1.77
                                and "PlateLocSide" < 0.86
                                and "PlateLocSide" > -0.86
                                ) as total_in_zone_pitches
        from trackman_metadata tm, trackman_batter tb, trackman_pitcher tp, seasons s
        where tm."PitchUID" = tb."PitchUID" and tb."PitchUID" = tp."PitchUID" and s."SeasonTitle" = '2024' and tm."UTCDate" >= s."StartDate" and tm."UTCDate" <= s."EndDate"
        group by ("Batter", "BatterTeam")
    )
    select 
        tb."Batter" as "Batter",
        tb."BatterTeam" as "BatterTeam",
       	hs."hits" as "hits",
        hs."at_bats" as "at_bats",
        COUNT(*) filter (where "PitchCall" = 'StrikeCalled'
                        or "PitchCall" = 'StrikeSwinging'
                        or "PitchCall" = 'FoulBallNotFieldable'
                        ) as strikes,
        COUNT(*) filter (where "KorBB" = 'Walk') as walks,
        COUNT(*) filter (where "KorBB" = 'Strikeout') as strikeouts,
        COUNT(*) filter (where "PlayResult" = 'HomeRun') as homeruns,
        COUNT(*) filter (where "PlayResult" = 'Double'
                        or "PlayResult" = 'Triple'
                        or "PlayResult" = 'HomeRun'
                        ) as extra_base_hits,
        COUNT(*) filter (where "KorBB" = 'Walk'
                        or "PitchCall" = 'InPlay'
                        or "PitchCall" = 'HitByPitch'
                        or "KorBB" = 'Strikeout'
                        ) as plate_appearances,
        COUNT(*) filter (where "PitchCall" = 'HitByPitch') as hit_by_pitch,
        COUNT(*) filter (where "PlayResult" = 'Sacrifice') as sacrifice,
        SUM(case
            when "PlayResult" = 'Single' then 1
            when "PlayResult" = 'Double' then 2
            when "PlayResult" = 'Triple' then 3
            when "PlayResult" = 'HomeRun' then 4
            else 0
            end) as total_bases,
        case when at_bats = 0 then null
            else (hits + COUNT(*) filter (where "KorBB" = 'Walk'
                                    or "PitchCall" = 'HitByPitch'))::decimal
            / (COUNT(*) filter (where "PlayResult" = 'Error'
                                or "PlayResult" = 'Out'
                                or "PlayResult" = 'FieldersChoice'
                                or "KorBB" = 'Strikeout'
                                ) + hits 
                                + COUNT(*) filter (where "KorBB" = 'Walk'
                                                    or "PitchCall" = 'HitByPitch')
                                + COUNT(*) filter (where "PlayResult" = 'Sacrifice' 
                                                    and "TaggedHitType" = 'FlyBall')) 
        end as on_base_percentage,
        case when at_bats = 0 then null
            else 
            SUM(case
            when "PlayResult" = 'Single' then 1
            when "PlayResult" = 'Double' then 2
            when "PlayResult" = 'Triple' then 3
            when "PlayResult" = 'HomeRun' then 4
            else 0
            end)::decimal / at_bats 
        end as slugging_percentage,
        case when total_out_of_zone_pitches = 0 then null
            else COUNT(*) filter (where "PitchCall" = 'StrikeSwinging'
                                or "PitchCall" = 'FoulBallNotFieldable'
                                or "PitchCall" = 'InPlay'
                                or "PlateLocHeight" > 3.55
                                or "PlateLocHeight" < 1.77
                                or "PlateLocSide" > 0.86
                                or "PlateLocSide" < -0.86
                                )::decimal / total_out_of_zone_pitches
        end as chase_percentage,
        case when total_in_zone_pitches = 0 then null
            else COUNT(*) filter (where "PitchCall" = 'StrikeSwinging'
                                and "PlateLocHeight" < 3.55
                                and "PlateLocHeight" > 1.77
                                and "PlateLocSide" < 0.86
                                and "PlateLocSide" > -0.86
                                )::decimal / total_in_zone_pitches
        end as in_zone_whiff_percentage,
        COUNT(distinct "GameUID") as games
    from  hits_subquery hs, trackman_batter tb, trackman_metadata tm, trackman_pitcher tp, seasons s
    where hs."Batter" = tb."Batter" and hs."BatterTeam" = tb."BatterTeam" and tb."PitchUID" = tm."PitchUID" and tm."PitchUID" = tp."PitchUID" and s."SeasonTitle" = '2024' and tm."UTCDate" >= s."StartDate" and tm."UTCDate" <= s."EndDate"
    group by (tb."Batter", tb."BatterTeam", hs."hits", hs."at_bats", hs."total_out_of_zone_pitches", hs."total_in_zone_pitches")
)
select 
        *,
        case
            when at_bats = 0 then null
            else hits::decimal / at_bats
        end as batting_average,
        on_base_percentage + slugging_percentage as onbase_plus_slugging,
        slugging_percentage - case
            when at_bats = 0 then null
            else hits::decimal / at_bats
        end as isolated_power,
        case
            when plate_appearances = 0 then null
            else strikeouts::decimal / plate_appearances
        end as k_percentage,
        case
            when plate_appearances = 0 then null
            else walks::decimal / plate_appearances
        end as base_on_ball_percentage
from at_bats_subquery;

-- Values AU Baseball uses for strike zone
-- min_plate_side = -0.86
-- max_plate_side = 0.86
-- max_plate_height = 3.55
-- min_plate_height = 1.77

-- Holds the pitcher stats for the 2024 season
drop view if exists pitcher_stats_view_2024;
create or replace view pitcher_stats_view_2024 as
with pitcher_stats_subquery as (
    with pitcher_stats_subquery_two as (
        select tp2."Pitcher" as "Pitcher", tp2."PitcherTeam" as "PitcherTeam",
        COUNT(*) filter (where "PlateLocHeight" > 3.55
                                or "PlateLocHeight" < 1.77
                                or "PlateLocSide" > 0.86
                                or "PlateLocSide" < -0.86
                                ) as total_out_of_zone_pitches,
        COUNT(*) filter (where "PlateLocHeight" < 3.55
                                and "PlateLocHeight" > 1.77
                                and "PlateLocSide" < 0.86
                                and "PlateLocSide" > -0.86
                                ) as total_in_zone_pitches
        from trackman_batter tb2, trackman_metadata tm2, trackman_pitcher tp2, seasons s2
        where tb2."PitchUID" = tm2."PitchUID" and tm2."PitchUID" = tp2."PitchUID" and s2."SeasonTitle" = '2024' and tm2."UTCDate" >= s2."StartDate" and tm2."UTCDate" <= s2."EndDate"
        group by (tp2."Pitcher", tp2."PitcherTeam")
    )
    select pss."Pitcher" as "Pitcher", pss."PitcherTeam" as "PitcherTeam",
        COUNT(*) filter (where "KorBB" = 'Strikeout') as total_strikeouts_pitcher,
        COUNT(*) filter (where "KorBB" = 'Walk') as total_walks_pitcher,
        COUNT(*) filter (where "PlateLocHeight" > 3.55
                            or "PlateLocHeight" < 1.77
                            or "PlateLocSide" > 0.86
                            or "PlateLocSide" < -0.86
                            ) as total_out_of_zone_pitches,
        COUNT(*) filter (where "PitchCall" = 'StrikeSwinging'
                        and "PlateLocHeight" < 3.55
                        and "PlateLocHeight" > 1.77
                        and "PlateLocSide" < 0.86
                        and "PlateLocSide" > -0.86
                        ) as misses_in_zone,
        COUNT(*) filter (where "PitchCall" = 'StrikeSwinging'  
                        or "PitchCall" = 'FoulBallNotFieldable'
                        or "PitchCall" = 'InPlay'
                        and "PlateLocHeight" < 3.55
                        and "PlateLocHeight" > 1.77
                        and "PlateLocSide" < 0.86
                        and "PlateLocSide" > -0.86
                        ) as swings_in_zone,
        COUNT(*) filter (where "PitchCall" = 'StrikeSwinging'  
                        or "PitchCall" = 'FoulBallNotFieldable'
                        and "PlateLocHeight" > 3.55
                        and "PlateLocHeight" < 1.77
                        and "PlateLocSide" > 0.86
                        and "PlateLocSide" < -0.86
                        ) as total_num_chases,
        COUNT(*) as pitches,
        COUNT(distinct "GameUID") as games,
        COUNT(*) filter (where "Inning" = 1
                        and "Outs" = 0
                        and "Balls" = 0
                        and "Strikes" = 0
                        and "PAofInning" = 1
                        ) as games_started,
        ROUND(((COUNT(*) filter (where "KorBB" = 'StrikeOut') + 
        SUM("OutsOnPlay"::integer)) / 3) +
        (((COUNT(*) filter (where "KorBB" = 'StrikeOut') + 
        SUM("OutsOnPlay"::integer)) % 3)::decimal / 10), 1) as total_innings_pitched,
        COUNT(distinct ("PAofInning", "Inning", "Batter", "GameUID")) as total_batters_faced,
        case when total_in_zone_pitches = 0 then null
            else COUNT(*) filter (where "PitchCall" = 'StrikeSwinging'
                                and "PlateLocHeight" < 3.55
                                and "PlateLocHeight" > 1.77
                                and "PlateLocSide" < 0.86
                                and "PlateLocSide" > -0.86
                                )::decimal / total_in_zone_pitches
        end as in_zone_whiff_percentage,
        case when total_out_of_zone_pitches = 0 then null
            else COUNT(*) filter (where "PitchCall" = 'StrikeSwinging'
                                or "PitchCall" = 'FoulBallNotFieldable'
                                or "PitchCall" = 'InPlay'
                                or "PlateLocHeight" > 3.55
                                or "PlateLocHeight" < 1.77
                                or "PlateLocSide" > 0.86
                                or "PlateLocSide" < -0.86
                                )::decimal / total_out_of_zone_pitches
        end as chase_percentage
    from pitcher_stats_subquery_two pss, trackman_metadata tm, trackman_pitcher tp, trackman_batter tb, seasons s
    where pss."Pitcher" = tp."Pitcher" and pss."PitcherTeam" = tp."PitcherTeam" and tm."PitchUID" = tp."PitchUID" and tm."PitchUID" = tb."PitchUID" and s."SeasonTitle" = '2024' and tm."UTCDate" >= s."StartDate" and tm."UTCDate" <= s."EndDate"
    group by (pss."Pitcher", pss."PitcherTeam", pss."total_out_of_zone_pitches", pss."total_in_zone_pitches")
)
select 
    *,
    case
        when total_batters_faced = 0 then null
        else total_strikeouts_pitcher::decimal / total_batters_faced
    end as k_percentage,
    case
        when total_batters_faced = 0 then null
        else total_walks_pitcher::decimal / total_batters_faced
    end as base_on_ball_percentage
from pitcher_stats_subquery;

-- View for defensive shifting modeling team
drop view if exists pitcher_pitch_type_avg_view;
create or replace view pitcher_pitch_type_avg_view as
select "Pitcher", "PitcherTeam",
        "PitcherThrows",
        case
            when "TaggedPitchType" = 'Fastball' and "AutoPitchType" != 'Four-Seam' then 'Sinker'
            when "AutoPitchType" = 'Four-Seam' then 'Fastball'
            else "AutoPitchType"
        end as "PitchType",
        AVG("RelSpeed") as avg_rel_speed,
        AVG("InducedVert") as avg_induced_vert,
        AVG("HorzBreak") as avg_horz_break,
        AVG("RelHeight") as avg_rel_height,
        AVG("RelSide")  as avg_rel_side,
        AVG("Extension") as avg_extension,
        AVG("SpinRate") as avg_spin_rate,
        AVG("SpinAxis") as avg_spin_axis,
        AVG("VertApprAngle") as avg_vert_appr_angle,
        AVG("HorzApprAngle") as avg_horz_appr_angle
from trackman_pitcher
where "PitcherThrows" != 'Undefined' and "AutoPitchType" != '' and "AutoPitchType" != 'NaN' and "RelSpeed" != 'NaN' 
and "InducedVert" != 'NaN' and "HorzBreak" != 'NaN' and "RelHeight" != 'NaN' and "RelSide" != 'NaN' and "Extension" != 'NaN'
and "SpinRate" != 'NaN' and "SpinAxis" != 'NaN' and "VertApprAngle" != 'NaN' and "HorzApprAngle" != 'NaN'
group by ("Pitcher", "PitcherTeam", "PitcherThrows", "PitchType");
    