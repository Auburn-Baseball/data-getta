"""
Author: Joshua Reed
Created: 15 October 2025
Updated: 19 October 2025

Advanced Pitching Stats Utility Module
- Loads environment variables and initializes Supabase client
- Defines strike zone constants and helper functions
- Extracts, calculates, and combines advanced pitching stats from CSV files
- Uploads combined stats to Supabase
- Computes and updates scaled percentile ranks for players
"""

import bisect
import json
from typing import Dict, Optional, Tuple, cast

import numpy as np
import pandas as pd
import xgboost as xgb
from supabase import Client, create_client

from .common import (
    SUPABASE_KEY,
    SUPABASE_URL,
    NumpyEncoder,
    check_practice,
    check_supabase_vars,
    is_in_strike_zone,
    project_root,
)
from .file_date import CSVFilenameParser

check_supabase_vars()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)  # type: ignore[arg-type]

# Strike zone constants
MIN_PLATE_SIDE = -0.86
MAX_PLATE_SIDE = 0.86
MAX_PLATE_HEIGHT = 3.55
MIN_PLATE_HEIGHT = 1.77


# Load xBA grid for fast lookups
XBA_GRID_PATH = project_root / "scripts" / "utils" / "models" / "xBA_grid.csv"


def load_xba_grid(path):
    if path.exists():
        xba_grid = pd.read_csv(path)
    else:
        xba_grid = pd.DataFrame(columns=["ev_bin", "la_bin", "dir_bin", "xBA"])

    if not xba_grid.empty:
        xba_dict = {
            (int(ev), int(la), int(dr)): float(xba)
            for ev, la, dr, xba in zip(
                xba_grid["ev_bin"],
                xba_grid["la_bin"],
                xba_grid["dir_bin"],
                xba_grid["xBA"],
            )
        }
        ev_bins = list(xba_grid["ev_bin"].unique())
        la_bins = list(xba_grid["la_bin"].unique())
        dir_bins = list(xba_grid["dir_bin"].unique())
        global_xba_mean = xba_grid["xBA"].mean()
    else:
        xba_dict = {}
        ev_bins = la_bins = dir_bins = []
        global_xba_mean = 0.25

    return xba_grid, xba_dict, ev_bins, la_bins, dir_bins, global_xba_mean


# Module-level call
xba_grid, xba_dict, ev_bins, la_bins, dir_bins, global_xba_mean = load_xba_grid(XBA_GRID_PATH)


def closest_value(sorted_list, value):
    """Return the closest value in a sorted list using binary search."""
    i = bisect.bisect_left(sorted_list, value)
    if i == 0:
        return sorted_list[0]
    if i == len(sorted_list):
        return sorted_list[-1]
    before, after = sorted_list[i - 1], sorted_list[i]
    return after if abs(after - value) < abs(before - value) else before


def lookup_xBA(ev, la, dir_angle):
    """Fast xBA lookup using exact matches or nearest neighbor averaging."""
    if not xba_dict:
        return global_xba_mean

    key = (ev, la, dir_angle)
    if key in xba_dict:
        return xba_dict[key]

    # --- Approximation path ---
    ev_c = closest_value(ev_bins, ev)
    la_c = closest_value(la_bins, la)
    dir_c = closest_value(dir_bins, dir_angle)

    # Check 3D neighborhood (±1 EV/LA, ±5 Dir)
    neighbors = [
        xba_dict[k]
        for k in [
            (ev_c + e_off, la_c + l_off, dir_c + d_off)
            for e_off in (-1, 0, 1)
            for l_off in (-1, 0, 1)
            for d_off in (-5, 0, 5)
        ]
        if k in xba_dict
    ]

    if neighbors:
        return sum(neighbors) / len(neighbors)
    return global_xba_mean


# --- Load pre-trained xSLG model ---
XSLG_MODEL_PATH = project_root / "scripts" / "utils" / "models" / "xslg_model.json"
xslg_model = None


def load_xslg_model(path):
    local_xslg_model = None

    if path.exists():
        try:
            local_xslg_model = xgb.XGBRegressor()
            local_xslg_model.load_model(str(path))
            # print("xSLG model loaded successfully.")
        except Exception as e:
            print(f"Failed to load xSLG model: {e}")
    else:
        print("xSLG model not found — skipping xSLG predictions.")

    return local_xslg_model


xslg_model = load_xslg_model(XSLG_MODEL_PATH)


# --- Load pre-trained xwOBA model ---
XWOBA_MODEL_PATH = project_root / "scripts" / "utils" / "models" / "xwoba_model.json"
xwoba_model = None


def load_xwoba_model(path):
    local_xwoba_model = None

    if path.exists():
        try:
            local_xwoba_model = xgb.XGBRegressor()
            local_xwoba_model.load_model(str(path))
            # print("xwOBA model loaded successfully.")
        except Exception as e:
            print(f"Failed to load xwOBA model: {e}")
    else:
        print("xwOBA model not found — skipping xwOBA predictions.")

    return local_xwoba_model


xwoba_model = load_xwoba_model(XWOBA_MODEL_PATH)


def get_advanced_pitching_stats_from_buffer(
    buffer, filename: str
) -> Dict[Tuple[str, str, int], Dict]:
    """Extract advanced pitching stats from CSV in memory"""
    try:
        # Read CSV selecting only available desired columns
        # (null-safe, optional League for practice detection)
        desired_cols = [
            "Pitcher",
            "PitcherTeam",
            "KorBB",
            "PitchCall",
            "PlayResult",
            "ExitSpeed",
            "Angle",
            "Direction",
            "BatterSide",
            "TaggedHitType",
            "TaggedPitchType",
            "RelSpeed",
            "PlateLocHeight",
            "PlateLocSide",
            "League",
        ]
        header_df = pd.read_csv(buffer, nrows=0)
        available = [c for c in desired_cols if c in header_df.columns]
        buffer.seek(0)
        df = pd.read_csv(buffer, usecols=available)

        # Determines if this is practice data by checking the League column
        is_practice = check_practice(df)

        # Extract year from filename
        file_date_parser = CSVFilenameParser()
        date_components = file_date_parser.get_date_components(filename)
        if not date_components:
            raise ValueError(f"Unable to extract date from filename: {filename}")
        year = date_components[0]

        pitchers_dict = {}

        # Group by pitcher and team
        grouped = df.groupby(["Pitcher", "PitcherTeam"])

        for (pitcher_name, pitcher_team), group in grouped:
            pitcher_name = str(pitcher_name).strip()
            if is_practice and pitcher_team == "AUB_TIG":
                pitcher_team = "AUB_PRC"
            else:
                pitcher_team = str(pitcher_team).strip()

            key = (pitcher_name, pitcher_team, year)

            # Calculate plate appearances
            plate_appearances = len(
                group[
                    group["KorBB"].isin(["Walk", "Strikeout"])
                    | group["PitchCall"].isin(["InPlay", "HitByPitch"])
                    | group["PlayResult"].isin(["Error", "FieldersChoice", "Sacrifice"])
                ]
            )

            # Calculate batted balls with complete stats
            batted_balls = group[
                (group["PitchCall"] == "InPlay")
                & (group["ExitSpeed"].notna())
                & (group["Angle"]).notna()
                & (group["Direction"].notna())
                & (group["BatterSide"].notna())
            ].shape[0]

            # Calculate at-bats
            at_bats = len(group[group["KorBB"].isin(["Strikeout"])]) + batted_balls

            # Calculate ground balls
            ground_balls = group[
                (group["PitchCall"] == "InPlay")
                & (group["TaggedHitType"] == "GroundBall")
                & (group["ExitSpeed"].notna())
                & (group["Angle"]).notna()
                & (group["Direction"].notna())
                & (group["BatterSide"].notna())
            ].shape[0]

            # Calculate fastballs thrown with release speed tracked
            fastballs = group[
                (group["TaggedPitchType"] == "Fastball") & (group["RelSpeed"].notna())
            ].shape[0]

            # LA Sweet Spot percentage
            sweet_spot_balls = group[
                (group["PitchCall"] == "InPlay")
                & (group["ExitSpeed"].notna())
                & (group["Angle"].notna())
                & (group["Direction"].notna())
                & (group["BatterSide"].notna())
                & (group["Angle"] >= 8)
                & (group["Angle"] <= 32)
            ].shape[0]
            la_sweet_spot_per = (sweet_spot_balls / batted_balls) if batted_balls > 0 else None

            # Hard hit percentage
            hard_hit_balls = group[
                (group["PitchCall"] == "InPlay")
                & (group["ExitSpeed"].notna())
                & (group["ExitSpeed"] >= 95)
                & (group["Angle"].notna())
                & (group["Direction"].notna())
                & (group["BatterSide"].notna())
            ].shape[0]
            hard_hit_per = (hard_hit_balls / batted_balls) if batted_balls > 0 else None

            # Total and average exit velocity
            total_exit_velo = group[
                (group["PitchCall"] == "InPlay")
                & (group["ExitSpeed"].notna())
                & (group["Angle"].notna())
                & (group["Direction"].notna())
                & (group["BatterSide"].notna())
            ]["ExitSpeed"].sum()
            avg_exit_velo = total_exit_velo / batted_balls if batted_balls > 0 else None

            # Total and average release velocity of fastballs
            total_fastball_velo = group[
                (group["TaggedPitchType"] == "Fastball") & (group["RelSpeed"].notna())
            ]["RelSpeed"].sum()
            avg_fastball_velo = total_fastball_velo / fastballs if fastballs > 0 else None

            # Walks and strikeouts
            walks = len(group[group["KorBB"] == "Walk"])
            strikeouts = len(group[group["KorBB"] == "Strikeout"])

            # K% and BB%
            k_percentage = strikeouts / plate_appearances if plate_appearances > 0 else None
            bb_percentage = walks / plate_appearances if plate_appearances > 0 else None

            # GB %
            gb_per = ground_balls / batted_balls if batted_balls > 0 else None

            # Initialize zone stats counters
            in_zone_pitches = 0
            out_of_zone_pitches = 0
            in_zone_whiffs = 0
            out_of_zone_swings = 0

            # Compute zone stats
            for _, row in group.iterrows():
                try:
                    height: float = (
                        float(row["PlateLocHeight"]) if pd.notna(row["PlateLocHeight"]) else None
                    )
                    side: float = (
                        float(row["PlateLocSide"]) if pd.notna(row["PlateLocSide"]) else None
                    )

                    if height is not None and side is not None:
                        if is_in_strike_zone(height, side):
                            in_zone_pitches += 1
                            if row["PitchCall"] == "StrikeSwinging":
                                in_zone_whiffs += 1
                        else:
                            out_of_zone_pitches += 1
                            if row["PitchCall"] in [
                                "StrikeSwinging",
                                "FoulBallNotFieldable",
                                "InPlay",
                            ]:
                                out_of_zone_swings += 1
                except (ValueError, TypeError):
                    continue

            # Whiff and chase percentages
            whiff_per = in_zone_whiffs / in_zone_pitches if in_zone_pitches > 0 else None
            chase_per = (
                out_of_zone_swings / out_of_zone_pitches if out_of_zone_pitches > 0 else None
            )

            # --- Prepare batted_ball_rows ---
            batted_ball_rows = group[
                (group["PitchCall"] == "InPlay")
                & (group["ExitSpeed"].notna())
                & (group["Angle"].notna())
                & (group["Direction"].notna())
                & (group["BatterSide"].notna())
            ].copy()

            # --- Compute xBA for all batted balls ---
            dir_angle = batted_ball_rows["Direction"].astype(float) * np.where(
                batted_ball_rows["BatterSide"] == "Left", -1, 1
            )
            ev_bin = batted_ball_rows["ExitSpeed"].round().astype(int)
            la_bin = batted_ball_rows["Angle"].round().astype(int)
            dir_bin = (dir_angle // 5 * 5).astype(int)

            # Use your neighbor-averaging function
            batted_ball_rows["xBA"] = [
                lookup_xBA(ev, la, dr) for ev, la, dr in zip(ev_bin, la_bin, dir_bin)
            ]

            # --- Predict xSLG for all batted balls ---
            if xslg_model is not None and not batted_ball_rows.empty:
                valid_xslg = batted_ball_rows[
                    ["ExitSpeed", "Angle", "Direction", "BatterSide"]
                ].copy()
                valid_xslg["BatterSide"] = valid_xslg["BatterSide"].map({"Left": 0, "Right": 1})
                preds_xslg = xslg_model.predict(valid_xslg)
                batted_ball_rows["xSLG"] = preds_xslg
            else:
                batted_ball_rows["xSLG"] = 0

            # --- Drop any rows where xBA or xSLG is None just to be safe ---
            batted_ball_rows = batted_ball_rows.dropna(subset=["xBA", "xSLG"])

            # --- Barrel % calculation (skip rows with None) ---
            barrel_balls = batted_ball_rows[
                (batted_ball_rows["xBA"].notna())
                & (batted_ball_rows["xSLG"].notna())
                & (batted_ball_rows["xBA"] >= 0.5)
                & (batted_ball_rows["xSLG"] >= 1.5)
            ].shape[0]

            barrel_per = (barrel_balls / batted_balls) if batted_balls > 0 else 0

            # --- Compute xBA per batter ---
            if not batted_ball_rows.empty:
                avg_xba_batted_balls = batted_ball_rows["xBA"].mean()
                batter_xba = (avg_xba_batted_balls * batted_balls) / at_bats if at_bats > 0 else 0
                batter_xba = max(batter_xba, 0)  # Clip minimum
            else:
                batter_xba = 0

            # --- Compute xSLG per batter ---
            if not batted_ball_rows.empty:
                avg_xslg_batted_balls = batted_ball_rows["xSLG"].mean()
                batter_xslg = (avg_xslg_batted_balls * batted_balls) / at_bats if at_bats > 0 else 0
                batter_xslg = max(batter_xslg, 0)  # Clip minimum
            else:
                batter_xslg = 0

            # --- Predict xwOBA using pre-trained model ---
            woba_map = {
                "Single": 0.89,
                "Double": 1.27,
                "Triple": 1.62,
                "HomeRun": 2.10,
                "Walk": 0.72,
                "HitByPitch": 0.73,
                "Sacrifice": 0.0,
                "FieldersChoice": 0.0,
                "Out": 0.0,
                "Error": 0.0,
                "Undefined": 0.0,
            }

            # Non-batted-ball events
            walks = len(group[group["KorBB"] == "Walk"])
            hbps = len(group[group["KorBB"] == "HitByPitch"])
            sacrifices = len(group[group["PlayResult"] == "Sacrifice"])
            fielders_choice = len(group[group["PlayResult"] == "FieldersChoice"])
            outs = len(group[group["PlayResult"] == "Out"])

            # --- Full xwOBA including walks/HBP/etc ---
            try:
                # Plate appearances safety
                pa = plate_appearances if plate_appearances > 0 else 1

                # Model contributions from batted balls
                if not batted_ball_rows.empty and xwoba_model is not None:
                    valid_bb = batted_ball_rows[
                        ["ExitSpeed", "Angle", "Direction", "BatterSide"]
                    ].copy()
                    valid_bb["BatterSide"] = valid_bb["BatterSide"].map({"Left": 0, "Right": 1})
                    preds = xwoba_model.predict(valid_bb)
                    sum_xwOBA_bb = float(np.sum(preds))
                else:
                    sum_xwOBA_bb = 0

                # Contributions from non-batted-ball events
                total_contrib = (
                    sum_xwOBA_bb
                    + walks * woba_map["Walk"]
                    + hbps * woba_map["HitByPitch"]
                    + sacrifices * woba_map["Sacrifice"]
                    + fielders_choice * woba_map["FieldersChoice"]
                    + outs * woba_map["Out"]
                )

                # Compute xwOBA
                batter_xwoba = total_contrib / pa
                batter_xwoba = max(batter_xwoba, 0)  # Clip minimum

            except Exception as e:
                print(f"Error computing xwOBA for {pitcher_name}: {e}")
                batter_xwoba = 0

            # Store computed stats for pitcher
            pitcher_stats = {
                "Pitcher": pitcher_name,
                "PitcherTeam": pitcher_team,
                "Year": year,
                "plate_app": plate_appearances,
                "batted_balls": batted_balls,
                "avg_exit_velo": avg_exit_velo if avg_exit_velo is not None else None,
                "k_per": k_percentage if k_percentage is not None else None,
                "bb_per": bb_percentage if bb_percentage is not None else None,
                "la_sweet_spot_per": (la_sweet_spot_per if la_sweet_spot_per is not None else None),
                "hard_hit_per": hard_hit_per if hard_hit_per is not None else None,
                "in_zone_pitches": in_zone_pitches,
                "whiff_per": whiff_per if whiff_per is not None else None,
                "out_of_zone_pitches": out_of_zone_pitches,
                "chase_per": chase_per if chase_per is not None else None,
                "fastballs": fastballs,
                "avg_fastball_velo": (avg_fastball_velo if avg_fastball_velo is not None else None),
                "ground_balls": ground_balls,
                "gb_per": gb_per if gb_per is not None else None,
                "xba_per": batter_xba if batter_xba is not None else None,
                "xslg_per": batter_xslg if batter_xslg is not None else None,
                "at_bats": at_bats,
                "xwoba_per": batter_xwoba if batter_xwoba is not None else None,
                "barrel_per": barrel_per if barrel_per is not None else None,
            }

            pitchers_dict[key] = pitcher_stats

        return pitchers_dict

    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return {}


# Helper to safely get numeric values
def safe_get(d, key):
    return d.get(key) if d.get(key) is not None else 0


# Weighted averages helper (no rounding)
def weighted_avg(existing_stats, new_stats, stat_key, weight_key, total_weight):
    total = safe_get(existing_stats, stat_key) * safe_get(existing_stats, weight_key) + safe_get(
        new_stats, stat_key
    ) * safe_get(new_stats, weight_key)
    if total_weight > 0:
        return max(total / total_weight, 0)
    return None


def combine_advanced_pitching_stats(existing_stats: Dict, new_stats: Dict) -> Dict:
    """Merge existing and new pitching stats, updating rates and percentages safely"""

    if not existing_stats:
        return new_stats

    existing_dates = set(existing_stats.get("processed_dates") or [])
    new_dates = set(new_stats.get("processed_dates") or [])

    if new_dates and new_dates.issubset(existing_dates):
        return existing_stats

    # Combine counts
    combined_plate_app = safe_get(existing_stats, "plate_app") + safe_get(new_stats, "plate_app")
    combined_batted_balls = safe_get(existing_stats, "batted_balls") + safe_get(
        new_stats, "batted_balls"
    )
    combined_ground_balls = safe_get(existing_stats, "ground_balls") + safe_get(
        new_stats, "ground_balls"
    )
    combined_in_zone_pitches = safe_get(existing_stats, "in_zone_pitches") + safe_get(
        new_stats, "in_zone_pitches"
    )
    combined_out_of_zone_pitches = safe_get(existing_stats, "out_of_zone_pitches") + safe_get(
        new_stats, "out_of_zone_pitches"
    )
    combined_fastballs = safe_get(existing_stats, "fastballs") + safe_get(new_stats, "fastballs")
    combined_at_bats = safe_get(existing_stats, "at_bats") + safe_get(new_stats, "at_bats")

    combined_avg_exit_velo = weighted_avg(
        existing_stats,
        new_stats,
        "avg_exit_velo",
        "batted_balls",
        combined_batted_balls,
    )
    combined_k_per = weighted_avg(
        existing_stats, new_stats, "k_per", "plate_app", combined_plate_app
    )
    combined_bb_per = weighted_avg(
        existing_stats, new_stats, "bb_per", "plate_app", combined_plate_app
    )
    combined_gb_per = weighted_avg(
        existing_stats, new_stats, "gb_per", "batted_balls", combined_batted_balls
    )
    combined_sweet_spot_per = weighted_avg(
        existing_stats,
        new_stats,
        "la_sweet_spot_per",
        "batted_balls",
        combined_batted_balls,
    )
    combined_hard_hit_per = weighted_avg(
        existing_stats, new_stats, "hard_hit_per", "batted_balls", combined_batted_balls
    )
    combined_whiff_per = weighted_avg(
        existing_stats,
        new_stats,
        "whiff_per",
        "in_zone_pitches",
        combined_in_zone_pitches,
    )
    combined_chase_per = weighted_avg(
        existing_stats,
        new_stats,
        "chase_per",
        "out_of_zone_pitches",
        combined_out_of_zone_pitches,
    )
    combined_avg_fastball_velo = weighted_avg(
        existing_stats, new_stats, "avg_fastball_velo", "fastballs", combined_fastballs
    )
    combined_xba_per = weighted_avg(
        existing_stats, new_stats, "xba_per", "at_bats", combined_at_bats
    )
    combined_xslg_per = weighted_avg(
        existing_stats, new_stats, "xslg_per", "at_bats", combined_at_bats
    )
    combined_xwoba_per = weighted_avg(
        existing_stats, new_stats, "xwoba_per", "plate_app", combined_plate_app
    )
    combined_barrel_per = weighted_avg(
        existing_stats, new_stats, "barrel_per", "batted_balls", combined_batted_balls
    )

    return {
        "Pitcher": new_stats["Pitcher"],
        "PitcherTeam": new_stats["PitcherTeam"],
        "Year": new_stats["Year"],
        "plate_app": combined_plate_app,
        "batted_balls": combined_batted_balls,
        "avg_exit_velo": combined_avg_exit_velo,
        "k_per": combined_k_per,
        "bb_per": combined_bb_per,
        "la_sweet_spot_per": combined_sweet_spot_per,
        "hard_hit_per": combined_hard_hit_per,
        "in_zone_pitches": combined_in_zone_pitches,
        "whiff_per": combined_whiff_per,
        "out_of_zone_pitches": combined_out_of_zone_pitches,
        "chase_per": combined_chase_per,
        "fastballs": combined_fastballs,
        "avg_fastball_velo": combined_avg_fastball_velo,
        "ground_balls": combined_ground_balls,
        "gb_per": combined_gb_per,
        "at_bats": combined_at_bats,
        "xba_per": combined_xba_per,
        "xslg_per": combined_xslg_per,
        "xwoba_per": combined_xwoba_per,
        "barrel_per": combined_barrel_per,
    }


# Helper: rank series and scale to 1-100
def rank_and_scale_to_1_100(series, ascending=False):
    series = series.copy()
    mask = series.notna()
    if mask.sum() == 0:
        return pd.Series([None] * len(series), index=series.index)
    ranks = series[mask].rank(method="min", ascending=ascending)
    min_rank, max_rank = ranks.min(), ranks.max()
    if min_rank == max_rank:
        scaled = pd.Series([100.0] * mask.sum(), index=series[mask].index)
    else:
        # Scale to 1-100, with best value (min_rank) always getting 100
        # Formula: 100 - (ranks - min_rank) / (max_rank - min_rank) * 99
        scaled = 100 - (ranks - min_rank) / (max_rank - min_rank) * 99
        # Apply flooring
        scaled = np.floor(scaled)
        # Ensure minimum rank (best performer) is exactly 100
        min_mask = ranks == min_rank
        scaled.loc[min_mask] = 100.0
        # Ensure values don't go below 1 (floor any that might be 0 or negative)
        scaled = scaled.clip(lower=1.0)
    result = pd.Series([None] * len(series), index=series.index)
    result[mask] = scaled
    return result


# Helper: calculate rank for practice players against non-practice distribution
def calculate_practice_overall_rank(practice_value, non_practice_series, ascending=False):
    """
    Calculate what a practice player's overall rank would be against all non-practice players.
    This doesn't add the practice player to the ranking distribution.
    Uses the same ranking method as rank_and_scale_to_1_100.
    """
    if pd.isna(practice_value):
        return None

    non_practice_series = non_practice_series.dropna()
    if len(non_practice_series) == 0:
        return None

    # Rank all non-practice values (including the practice value for comparison)
    # Create a temporary series with practice value added
    temp_series = pd.concat([non_practice_series, pd.Series([practice_value])])
    ranks = temp_series.rank(method="min", ascending=ascending)

    # Get the rank of the practice value (last element in temp_series)
    practice_rank = ranks.iloc[-1]

    # Get min and max ranks from non-practice players only
    non_practice_ranks = ranks.iloc[:-1]
    min_rank = non_practice_ranks.min()
    max_rank = non_practice_ranks.max()

    if min_rank == max_rank:
        # All non-practice values are the same
        scaled = 100.0
    else:
        # Handle cases where practice value is outside the non-practice range
        if practice_rank < min_rank:
            """Practice value is better than all non-practice
            (rank 1 when ascending=True, or higher rank when ascending=False)"""
            scaled = 100.0
        elif practice_rank > max_rank:
            # Practice value is worse than all non-practice
            scaled = 1.0
        else:
            # Use the same scaling formula as rank_and_scale_to_1_100
            # Formula: 100 - (ranks - min_rank) / (max_rank - min_rank) * 99
            scaled = 100 - (practice_rank - min_rank) / (max_rank - min_rank) * 99
            # Apply flooring
            scaled = np.floor(scaled)
            # If practice rank equals min_rank (best), set to 100
            if practice_rank == min_rank:
                scaled = 100.0
            # Ensure values don't go below 1
            scaled = max(1.0, scaled)

    return float(scaled)


def upload_advanced_pitching_to_supabase(
    pitchers_dict: Dict[Tuple[str, str, int], Dict],
    max_fetch_loops: Optional[int] = None,
):
    """Upload pitching stats to Supabase and compute scaled percentile ranks"""
    if not pitchers_dict:
        print("No advanced pitching stats to upload")
        return

    try:
        # Fetch existing records in batches
        existing_stats = {}
        offset = 0
        batch_size = 1000
        loop_count = 0
        while True:
            result = (
                supabase.table("AdvancedPitchingStats")
                .select("*")
                .range(offset, offset + batch_size - 1)
                .execute()
            )
            # safe for mocks: get .data if exists, else treat result as list
            data = getattr(result, "data", result)
            if not data:
                break
            for record in data:
                stat_key = (record["Pitcher"], record["PitcherTeam"], record["Year"])
                existing_stats[stat_key] = record
            offset += batch_size

            # TEST-SAFETY: break after max loops
            loop_count += 1
            if max_fetch_loops is not None and loop_count >= max_fetch_loops:
                print("Max fetch loops reached, breaking loop")
                break

        # Combine new stats with existing stats
        combined_stats = {}
        updated_count = 0
        new_count = 0
        for stat_key, new_stat in pitchers_dict.items():
            if stat_key in existing_stats:
                combined = combine_advanced_pitching_stats(existing_stats[stat_key], new_stat)
                if combined is existing_stats[stat_key]:
                    continue
                updated_count += 1
            else:
                combined = new_stat
                new_count += 1
            combined_stats[stat_key] = combined

        # Convert combined stats to JSON-serializable list
        pitcher_data = []
        for pitcher_dict in combined_stats.values():
            clean_dict = {k: v for k, v in pitcher_dict.items() if k != "unique_games"}
            json_str = json.dumps(clean_dict, cls=NumpyEncoder)
            clean_pitcher = json.loads(json_str)
            pitcher_data.append(clean_pitcher)

        print(
            f"Preparing to upload {updated_count} existing records and {new_count} new players..."
        )

        # Upload data in batches
        upload_batch_size = 1000
        total_inserted = 0
        for i in range(0, len(pitcher_data), upload_batch_size):
            batch = pitcher_data[i : i + upload_batch_size]
            try:
                supabase.table("AdvancedPitchingStats").upsert(
                    batch, on_conflict="Pitcher,PitcherTeam,Year"
                ).execute()
                total_inserted += len(batch)
                print(f"Uploaded batch {i//upload_batch_size + 1}: {len(batch)} records")
            except Exception as batch_error:
                print(f"Error uploading batch {i//upload_batch_size + 1}: {batch_error}")
                if batch:
                    print(f"Sample record: {batch[0]}")
                continue

        print(f"Uploaded {total_inserted} combined pitcher records")

        # Fetch all records to compute scaled percentile ranks
        print("\nFetching all pitcher records for ranking...")
        all_records = []
        offset = 0
        loop_count = 0
        while True:
            result = (
                supabase.table("AdvancedPitchingStats")
                .select(
                    "Pitcher,PitcherTeam,Year,avg_exit_velo,k_per,bb_per,"
                    + "la_sweet_spot_per,hard_hit_per,whiff_per,chase_per,"
                    + "avg_fastball_velo,gb_per,xba_per,xslg_per,xwoba_per,"
                    + "barrel_per"
                )
                .range(offset, offset + batch_size - 1)
                .execute()
            )
            data = getattr(result, "data", result)
            if not data:
                break
            all_records.extend(data)
            offset += batch_size
            print(f"Fetched {len(data)} records (total: {len(all_records)})")

            loop_count += 1
            if max_fetch_loops is not None and loop_count >= max_fetch_loops:
                print("Max fetch loops reached for ranking fetch, breaking loop")
                break

        if not all_records:
            print("No records found for ranking.")
            return

        df = pd.DataFrame(all_records).dropna(subset=["Year"])

        # Helper mask for practice rows (computed on the fly, not stored)
        # Practice = team is AUB_PRC
        practice_mask_series = df["PitcherTeam"].eq("AUB_PRC")

        metrics = [
            ("avg_exit_velo", False),
            ("k_per", False),
            ("bb_per", True),
            ("la_sweet_spot_per", True),
            ("hard_hit_per", True),
            ("whiff_per", False),
            ("chase_per", False),
            ("avg_fastball_velo", False),
            ("gb_per", False),
            ("xba_per", True),
            ("xslg_per", True),
            ("xwoba_per", True),
            ("barrel_per", True),
        ]

        ranked_df = df.copy()

        def compute_and_assign(subset_idx, col, asc, suffix):
            subset = ranked_df.loc[subset_idx]
            ranks = rank_and_scale_to_1_100(subset[col], ascending=asc)
            rank_col_name = f"{col}_rank_{suffix}" if suffix else f"{col}_rank"
            ranked_df.loc[subset_idx, rank_col_name] = ranks

        # Overall ranks (Year only) - exclude practice data from ranking
        for year_val, group_idx in ranked_df.groupby("Year").groups.items():
            group_mask = ranked_df.index.isin(group_idx)
            # Exclude practice rows from overall rankings
            non_practice_mask = group_mask & (
                ~practice_mask_series.reindex(ranked_df.index, fill_value=False)
            )
            if not non_practice_mask.any():
                continue

            # Calculate practice mask once per year
            practice_mask = group_mask & practice_mask_series.reindex(
                ranked_df.index, fill_value=False
            )

            for col, asc in metrics:
                compute_and_assign(non_practice_mask, col, asc, "")

                # Now calculate practice players' overall ranks against non-practice distribution
                if practice_mask.any():
                    non_practice_series = ranked_df.loc[non_practice_mask, col].dropna()
                    if len(non_practice_series) > 0:
                        for practice_idx in ranked_df[practice_mask].index:
                            practice_value = ranked_df.loc[practice_idx, col]
                            if pd.notna(practice_value):
                                practice_rank = calculate_practice_overall_rank(
                                    practice_value, non_practice_series, ascending=asc
                                )
                                rank_col_name = f"{col}_rank"
                                ranked_df.loc[practice_idx, rank_col_name] = practice_rank

        # Team ranks
        for key, group_idx in ranked_df.groupby(["Year", "PitcherTeam"]).groups.items():
            year_val, team_val = cast(Tuple[int, str], key)
            group_mask = ranked_df.index.isin(group_idx)
            if str(team_val) == "AUB_PRC":
                mask = group_mask & practice_mask_series.reindex(ranked_df.index, fill_value=False)
            else:
                mask = group_mask & (
                    ~practice_mask_series.reindex(ranked_df.index, fill_value=False)
                )
            if not mask.any():
                continue
            for col, asc in metrics:
                compute_and_assign(mask, col, asc, "team")

        print("Computed scaled percentile ranks for overall and team with practice handling.")

        # Prepare data for upload
        # Build upsert payload with new rank columns
        id_cols = ["Pitcher", "PitcherTeam", "Year"]
        rank_cols = []
        for col, _asc in metrics:
            rank_cols.extend(
                [
                    f"{col}_rank",  # Overall rank
                    f"{col}_rank_team",  # Team rank
                ]
            )
        present_rank_cols = [c for c in rank_cols if c in ranked_df.columns]
        # Convert NaN to None to satisfy JSON encoding
        upload_df = ranked_df[id_cols + present_rank_cols].copy()
        upload_df = upload_df.where(pd.notna(upload_df), None)
        update_data = upload_df.to_dict(orient="records")

        # Upload rank updates in batches
        print("\nUploading scaled percentile ranks...")
        total_updated = 0
        for i in range(0, len(update_data), upload_batch_size):
            batch = update_data[i : i + upload_batch_size]
            try:
                supabase.table("AdvancedPitchingStats").upsert(
                    batch, on_conflict="Pitcher,PitcherTeam,Year"
                ).execute()
                total_updated += len(batch)
                print(f"Updated batch {i//upload_batch_size + 1}: {len(batch)} records")
            except Exception as update_err:
                print(f"Error updating batch {i//upload_batch_size + 1}: {update_err}")
                if batch:
                    print(f"Sample record: {batch[0]}")
                continue

        print(f"Successfully updated ranks for {total_updated} records across all years.")

    except Exception as e:
        print(f"Supabase error: {e}")


if __name__ == "__main__":
    # Module entry point; designed for import
    print("Advanced Pitching Stats utility module loaded")
