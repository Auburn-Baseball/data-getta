-- Create a function that calculates the pitch_sums_data for a given time period.
-- The function takes in the pitcher name, pitcher team, start date, and end date as arguments.
drop function if exists get_pitch_count;
create or replace function get_pitch_count(pitcher_name text, pitcher_team text, start_date date, end_date date)
returns table("Pitcher" varchar, "PitcherTeam" varchar, "total_pitches" bigint, "curveball_count" bigint, "fourseam_count" bigint, "sinker_count" bigint, "slider_count" bigint, "twoseam_count" bigint, "changeup_count" bigint, "cutter_count" bigint, "splitter_count" bigint, "other_count" bigint)
as $$
begin
    return query
    select tp."Pitcher" , tp."PitcherTeam",
         COUNT(*) as total_pitches,
         COUNT(*) filter (where tp."AutoPitchType" = 'Curveball') as curveball_count,
         COUNT(*) filter (where tp."AutoPitchType" = 'Four-Seam') as fourseam_count,
            COUNT(*) filter (where tp."AutoPitchType" = 'Sinker') as sinker_count,
            COUNT(*) filter (where tp."AutoPitchType" = 'Slider') as slider_count,
            COUNT(*) filter (where tp."TaggedPitchType" = 'Fastball' and tp."AutoPitchType" != 'Four-Seam') as twoseam_count,
            COUNT(*) filter (where tp."AutoPitchType" = 'Changeup') as changeup_count,
            COUNT(*) filter (where tp."AutoPitchType" = 'Cutter') as cutter_count,
            COUNT(*) filter (where tp."AutoPitchType" = 'Splitter') as splitter_count,
            COUNT(*) filter (where tp."AutoPitchType" = 'Other' or tp."AutoPitchType" = 'NaN') as other_count
from trackman_metadata tm, trackman_pitcher tp
where tp."Pitcher" = pitcher_name and tp."PitcherTeam" = pitcher_team and tp."PitchUID" = tm."PitchUID" and tm."UTCDate" >= start_date and tm."UTCDate" <= end_date
group by (tp."Pitcher", tp."PitcherTeam");
end;
$$ language plpgsql;

-- This function calculates the batter stats for a given time period.
-- The function takes in the batter name, batter team, start date, and end date as arguments.
-- NOTE: This as multiple subqueries because some stats are dependent on other stats.
drop function if exists get_batter_stats;
create or replace function get_batter_stats(batter_name text, batter_team text, start_date date, end_date date)
returns table("Batter" varchar, "BatterTeam" varchar, "hits" bigint, "at_bats" bigint, "strikes" bigint, "walks" bigint, "strikeouts" bigint, "homeruns" bigint, "extra_base_hits" bigint, "plate_appearances" bigint, "hit_by_pitch" bigint, "sacrifice" bigint, "total_bases" bigint, "on_base_percentage" decimal, "slugging_percentage" decimal, "chase_percentage" decimal, "in_zone_whiff_percentage" decimal, "games" bigint, "batting_average" decimal, "onbase_plus_slugging" decimal, "isolated_power" decimal, "k_percentage" decimal, "base_on_ball_percentage" decimal)
as $$
begin 
    return query
    with at_bats_subquery as (
        with hits_subquery as (
            select tb."Batter", tb."BatterTeam",
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
            from trackman_metadata tm, trackman_batter tb, trackman_pitcher tp
            where tm."PitchUID" = tb."PitchUID" and tb."PitchUID" = tp."PitchUID" and tm."UTCDate" >= start_date and tm."UTCDate" <= end_date and tb."Batter" = batter_name and tb."BatterTeam" = batter_team
            group by (tb."Batter", tb."BatterTeam")
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
            case when hs."at_bats" = 0 then null
                else (hs."hits" + COUNT(*) filter (where "KorBB" = 'Walk'
                                        or "PitchCall" = 'HitByPitch'))::decimal
                / (COUNT(*) filter (where "PlayResult" = 'Error'
                                    or "PlayResult" = 'Out'
                                    or "PlayResult" = 'FieldersChoice'
                                    or "KorBB" = 'Strikeout'
                                    ) + hs."hits" 
                                    + COUNT(*) filter (where "KorBB" = 'Walk'
                                                        or "PitchCall" = 'HitByPitch')
                                    + COUNT(*) filter (where "PlayResult" = 'Sacrifice' 
                                                        and "TaggedHitType" = 'FlyBall')) 
            end as on_base_percentage,
            case when hs."at_bats" = 0 then null
                else 
                SUM(case
                when "PlayResult" = 'Single' then 1
                when "PlayResult" = 'Double' then 2
                when "PlayResult" = 'Triple' then 3
                when "PlayResult" = 'HomeRun' then 4
                else 0
                end)::decimal / hs."at_bats" 
            end as slugging_percentage,
            case when hs."total_out_of_zone_pitches" = 0 then null
                else COUNT(*) filter (where "PitchCall" = 'StrikeSwinging'
                                    or "PitchCall" = 'FoulBallNotFieldable'
                                    or "PitchCall" = 'InPlay'
                                    or "PlateLocHeight" > 3.55
                                    or "PlateLocHeight" < 1.77
                                    or "PlateLocSide" > 0.86
                                    or "PlateLocSide" < -0.86
                                    )::decimal / hs."total_out_of_zone_pitches"
            end as chase_percentage,
            case when hs."total_in_zone_pitches" = 0 then null
                else COUNT(*) filter (where "PitchCall" = 'StrikeSwinging'
                                    and "PlateLocHeight" < 3.55
                                    and "PlateLocHeight" > 1.77
                                    and "PlateLocSide" < 0.86
                                    and "PlateLocSide" > -0.86
                                    )::decimal / hs."total_in_zone_pitches"
            end as in_zone_whiff_percentage,
            COUNT(distinct "GameUID") as games
        from  hits_subquery hs, trackman_batter tb, trackman_metadata tm, trackman_pitcher tp
        where hs."Batter" = tb."Batter" and hs."BatterTeam" = tb."BatterTeam" and tb."PitchUID" = tm."PitchUID" and tm."PitchUID" = tp."PitchUID" and tm."UTCDate" >= start_date and tm."UTCDate" <= end_date and tb."Batter" = batter_name and tb."BatterTeam" = batter_team
        group by (tb."Batter", tb."BatterTeam", hs."hits", hs."at_bats", hs."total_out_of_zone_pitches", hs."total_in_zone_pitches")
    )
    select 
            *,
            case
                when abs."at_bats" = 0 then null
                else abs."hits"::decimal / abs."at_bats"
            end as batting_average,
            abs."on_base_percentage" + abs."slugging_percentage" as onbase_plus_slugging,
            abs."slugging_percentage" - case
                when abs."at_bats" = 0 then null
                else abs."hits"::decimal / abs."at_bats"
            end as isolated_power,
            case
                when abs."plate_appearances" = 0 then null
                else abs."strikeouts"::decimal / abs."plate_appearances"
            end as k_percentage,
            case
                when abs."plate_appearances" = 0 then null
                else abs."walks"::decimal / abs."plate_appearances"
            end as base_on_ball_percentage
    from at_bats_subquery abs;
end;
$$ language plpgsql;

-- This function calculates the pitcher stats for a given time period.
-- The function takes in the pitcher name, pitcher team, start date, and end date as arguments.
drop function if exists get_pitcher_stats;
create or replace function get_pitcher_stats(pitcher_name text, pitcher_team text, start_date date, end_date date)
returns table("Pitcher" varchar, "PitcherTeam" varchar, "total_strikeouts_pitcher" bigint, "total_walks_pitcher" bigint, "total_out_of_zone_pitches" bigint, "misses_in_zone" bigint, "swings_in_zone" bigint, "total_num_chases" bigint, "pitches" bigint, "games" bigint, "games_started" bigint, "total_innings_pitched" decimal, "total_batters_faced" bigint, "in_zone_whiff_percentage" decimal, "chase_percentage" decimal, "k_percentage" decimal, "base_on_ball_percentage" decimal)
as $$
    begin
    return query
    with pitcher_stats_subquery as (
    with pitcher_stats_subquery_two as (
        select tp."Pitcher" as "Pitcher", tp."PitcherTeam" as "PitcherTeam",
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
        from trackman_batter tb, trackman_metadata tm, trackman_pitcher tp
        where tb."PitchUID" = tm."PitchUID" and tm."PitchUID" = tp."PitchUID" and tm."UTCDate" >= start_date and tm."UTCDate" <= end_date and tp."Pitcher" = pitcher_name and tp."PitcherTeam" = pitcher_team
        group by (tp."Pitcher", tp."PitcherTeam")
    )
    select tp."Pitcher" as "Pitcher", tp."PitcherTeam" as "PitcherTeam",
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
        case when pss."total_in_zone_pitches" = 0 then null
            else COUNT(*) filter (where "PitchCall" = 'StrikeSwinging'
                                and "PlateLocHeight" < 3.55
                                and "PlateLocHeight" > 1.77
                                and "PlateLocSide" < 0.86
                                and "PlateLocSide" > -0.86
                                )::decimal / pss."total_in_zone_pitches"
        end as in_zone_whiff_percentage,
        case when pss."total_out_of_zone_pitches" = 0 then null
            else COUNT(*) filter (where "PitchCall" = 'StrikeSwinging'
                                or "PitchCall" = 'FoulBallNotFieldable'
                                or "PitchCall" = 'InPlay'
                                or "PlateLocHeight" > 3.55
                                or "PlateLocHeight" < 1.77
                                or "PlateLocSide" > 0.86
                                or "PlateLocSide" < -0.86
                                )::decimal / pss."total_out_of_zone_pitches"
        end as chase_percentage
    from pitcher_stats_subquery_two pss, trackman_metadata tm, trackman_pitcher tp, trackman_batter tb
    where pss."Pitcher" = tp."Pitcher" and pss."PitcherTeam" = tp."PitcherTeam" and tm."PitchUID" = tp."PitchUID" and tm."PitchUID" = tb."PitchUID" and tm."UTCDate" >= start_date and tm."UTCDate" <= end_date and tp."Pitcher" = pitcher_name and tp."PitcherTeam" = pitcher_team
    group by (tp."Pitcher", tp."PitcherTeam", pss."total_out_of_zone_pitches", pss."total_in_zone_pitches")
)
select 
    *,
    case
        when ps."total_batters_faced" = 0 then null
        else ps."total_strikeouts_pitcher"::decimal / ps."total_batters_faced"
    end as k_percentage,
    case
        when ps."total_batters_faced" = 0 then null
        else ps."total_walks_pitcher"::decimal / ps."total_batters_faced"
    end as base_on_ball_percentage
from pitcher_stats_subquery ps;
    end;
$$ language plpgsql;

