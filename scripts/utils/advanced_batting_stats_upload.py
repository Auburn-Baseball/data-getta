"""
Author: Joshua Reed
Created: 08 October 2025
Updated: 14 October 2025

Advanced Batting Stats Utility Module
- Loads environment variables and initializes Supabase client
- Defines strike zone constants and helper functions
- Extracts, calculates, and combines advanced batting stats from CSV files
- Uploads combined stats to Supabase
- Computes and updates scaled percentile ranks for players
"""

import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client
import json
import numpy as np
from typing import Dict, Tuple, List, Set
from pathlib import Path
from .file_date import CSVFilenameParser
import xgboost as xgb
import bisect

# Load environment variables
project_root = Path(__file__).parent.parent.parent
env = os.getenv("ENV", "development")
load_dotenv(project_root / f".env.{env}")

# Supabase configuration
SUPABASE_URL = os.getenv("VITE_SUPABASE_PROJECT_URL")
SUPABASE_KEY = os.getenv("VITE_SUPABASE_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "SUPABASE_PROJECT_URL and SUPABASE_API_KEY must be set in .env file"
    )

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Strike zone constants
MIN_PLATE_SIDE = -0.86
MAX_PLATE_SIDE = 0.86
MAX_PLATE_HEIGHT = 3.55
MIN_PLATE_HEIGHT = 1.77


# Load xBA grid for fast lookups
XBA_GRID_PATH = project_root / "scripts" / "utils" / "saved_models" / "xBA_grid.csv"
# --- Load xBA grid ---
if XBA_GRID_PATH.exists():
    xba_grid = pd.read_csv(XBA_GRID_PATH)
else:
    print("Warning: xBA grid not found, xBA stats will be skipped")
    xba_grid = pd.DataFrame(columns=["ev_bin", "la_bin", "dir_bin", "xBA"])

# --- Prepare lookup structures ---
if not xba_grid.empty:
    # Dictionary for instant exact lookups
    xba_dict = {
        (int(ev), int(la), int(dr)): float(xba)
        for ev, la, dr, xba in zip(
            xba_grid["ev_bin"], xba_grid["la_bin"], xba_grid["dir_bin"], xba_grid["xBA"]
        )
    }

    # Precompute unique sorted lists (already sorted, so no sort() call)
    ev_bins = list(xba_grid["ev_bin"].unique())
    la_bins = list(xba_grid["la_bin"].unique())
    dir_bins = list(xba_grid["dir_bin"].unique())

    global_xba_mean = xba_grid["xBA"].mean()
else:
    xba_dict = {}
    ev_bins = la_bins = dir_bins = []
    global_xba_mean = 0.25

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
        return None

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
XSLG_MODEL_PATH = project_root / "scripts" / "utils" / "saved_models" / "xslg_model.json"
xslg_model = None
if XSLG_MODEL_PATH.exists():
    try:
        xslg_model = xgb.XGBRegressor()
        xslg_model.load_model(str(XSLG_MODEL_PATH))
        # print("xSLG model loaded successfully.")
    except Exception as e:
        print(f"Failed to load xSLG model: {e}")
else:
    print("xSLG model not found — skipping xSLG predictions.")


# --- Load pre-trained xwOBA model ---
XWOBAM_MODEL_PATH = project_root / "scripts" / "utils" / "saved_models" / "xwoba_model.json"
xwoba_model = None
if XWOBAM_MODEL_PATH.exists():
    try:
        xwoba_model = xgb.XGBRegressor()
        xwoba_model.load_model(str(XWOBAM_MODEL_PATH))
        # print("xwOBA model loaded successfully.")
    except Exception as e:
        print(f"Failed to load xwOBA model: {e}")
else:
    print("xwOBA model not found — skipping xwOBA predictions.")


# Custom JSON encoder for numpy and pandas types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        return super(NumpyEncoder, self).default(obj)


def is_in_strike_zone(plate_loc_height, plate_loc_side):
    """Return True if pitch is within strike zone bounds"""
    try:
        height = float(plate_loc_height)
        side = float(plate_loc_side)
        return (
            MIN_PLATE_HEIGHT <= height <= MAX_PLATE_HEIGHT
            and MIN_PLATE_SIDE <= side <= MAX_PLATE_SIDE
        )
    except (ValueError, TypeError):
        return False


def get_advanced_batting_stats_from_buffer(
    buffer, filename: str
) -> Dict[Tuple[str, str, int], Dict]:
    """Extract advanced batting stats from CSV in memory"""
    try:
        cols_needed = [
            'Batter', 
            'BatterTeam', 
            'KorBB', 
            'PitchCall', 
            'PlayResult',
            'ExitSpeed',
            'Angle',
            'Direction',
            'BatterSide',
            'PlateLocHeight',
            'PlateLocSide',
            'Bearing',
            'Distance'
        ]
        df = pd.read_csv(buffer, usecols=cols_needed)

        # Verify required columns exist
        required_columns = ["Batter", "BatterTeam"]
        if not all(col in df.columns for col in required_columns):
            print(f"Warning: Missing required columns in {filename}")
            return {}

        # Extract year from filename
        file_date_parser = CSVFilenameParser()
        date_components = file_date_parser.get_date_components(filename)
        if not date_components:
            raise ValueError(f"Unable to extract date from filename: {filename}")
        year = date_components[0]

        game_date_obj = file_date_parser.get_date_object(filename)
        if game_date_obj is None:
            raise ValueError(f"Unable to parse game date from filename: {filename}")
        game_date_str = str(game_date_obj)

        batters_dict = {}

        # Group by batter and team
        grouped = df.groupby(["Batter", "BatterTeam"])

        for (batter_name, batter_team), group in grouped:
            if pd.isna(batter_name) or pd.isna(batter_team):
                continue

            batter_name = str(batter_name).strip()
            batter_team = str(batter_team).strip()

            if not batter_name or not batter_team:
                continue

            key = (batter_name, batter_team, year)

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
                (group["PitchCall"] == "InPlay") &
                (group["ExitSpeed"].notna()) &
                (group['Angle']).notna() &
                (group["Direction"].notna()) &
                (group["BatterSide"].notna())
            ].shape[0]

            # Calculate at-bats
            at_bats = len(
                group[
                    group["KorBB"].isin(["Strikeout"])
                ]
            ) + batted_balls

            # LA Sweet Spot percentage
            sweet_spot_balls = group[
                (group["PitchCall"] == "InPlay") &
                (group["ExitSpeed"].notna()) &
                (group["Angle"].notna()) &
                (group["Direction"].notna()) &
                (group["BatterSide"].notna()) &
                (group["Angle"] >= 8) & (group["Angle"] <= 32)
            ].shape[0]
            la_sweet_spot_per = (
                (sweet_spot_balls / batted_balls) if batted_balls > 0 else None
            )

            # Hard hit percentage
            hard_hit_balls = group[
                (group["PitchCall"] == "InPlay") &
                (group["ExitSpeed"].notna()) &
                (group["ExitSpeed"] >= 95) &
                (group["Angle"].notna()) &
                (group["Direction"].notna()) &
                (group["BatterSide"].notna())
            ].shape[0]
            hard_hit_per = (hard_hit_balls / batted_balls) if batted_balls > 0 else None

            # Total and average exit velocity
            total_exit_velo = group[
                (group["PitchCall"] == "InPlay") &
                (group["ExitSpeed"].notna()) &
                (group["Angle"].notna()) &
                (group["Direction"].notna()) &
                (group["BatterSide"].notna())
            ]["ExitSpeed"].sum()
            avg_exit_velo = total_exit_velo / batted_balls if batted_balls > 0 else None

            # Walks and strikeouts
            walks = len(group[group["KorBB"] == "Walk"])
            strikeouts = len(group[group["KorBB"] == "Strikeout"])

            # K% and BB%
            k_percentage = (
                strikeouts / plate_appearances if plate_appearances > 0 else None
            )
            bb_percentage = walks / plate_appearances if plate_appearances > 0 else None

            # Initialize zone stats counters
            in_zone_pitches = 0
            out_of_zone_pitches = 0
            in_zone_whiffs = 0
            out_of_zone_swings = 0

            # Compute zone stats
            for _, row in group.iterrows():
                try:
                    height = (
                        float(row["PlateLocHeight"])
                        if pd.notna(row["PlateLocHeight"])
                        else None
                    )
                    side = (
                        float(row["PlateLocSide"])
                        if pd.notna(row["PlateLocSide"])
                        else None
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

            # Initialize infield slice counters
            infield_left_slice = 0
            infield_lc_slice = 0
            infield_center_slice = 0
            infield_rc_slice = 0
            infield_right_slice = 0

            # Compute infield slices
            for _, row in group.iterrows():
                try:
                    if row.get("PitchCall") != "InPlay":
                        continue
                    distance = (
                        float(row["Distance"]) if pd.notna(row["Distance"]) else None
                    )
                    bearing = (
                        float(row["Bearing"]) if pd.notna(row["Bearing"]) else None
                    )

                    if distance is not None and distance <= 200 and bearing is not None:
                        if -45 <= bearing < -27:
                            infield_left_slice += 1
                        elif -27 <= bearing < -9:
                            infield_lc_slice += 1
                        elif -9 <= bearing < 9:
                            infield_center_slice += 1
                        elif 9 <= bearing < 27:
                            infield_rc_slice += 1
                        elif 27 <= bearing <= 45:
                            infield_right_slice += 1
                except (ValueError, TypeError):
                    continue

            total_infield_batted_balls = (
                infield_left_slice
                + infield_lc_slice
                + infield_center_slice
                + infield_rc_slice
                + infield_right_slice
            )

            # Compute slice percentages
            infield_left_per = (
                infield_left_slice / total_infield_batted_balls
                if total_infield_batted_balls > 0
                else None
            )
            infield_lc_per = (
                infield_lc_slice / total_infield_batted_balls
                if total_infield_batted_balls > 0
                else None
            )
            infield_center_per = (
                infield_center_slice / total_infield_batted_balls
                if total_infield_batted_balls > 0
                else None
            )
            infield_rc_per = (
                infield_rc_slice / total_infield_batted_balls
                if total_infield_batted_balls > 0
                else None
            )
            infield_right_per = (
                infield_right_slice / total_infield_batted_balls
                if total_infield_batted_balls > 0
                else None
            )

            # Whiff and chase percentages
            whiff_per = (
                in_zone_whiffs / in_zone_pitches if in_zone_pitches > 0 else None
            )
            chase_per = (
                out_of_zone_swings / out_of_zone_pitches
                if out_of_zone_pitches > 0
                else None
            )

            # --- Prepare batted_ball_rows ---
            batted_ball_rows = group[
                (group["PitchCall"] == "InPlay") &
                (group["ExitSpeed"].notna()) &
                (group["Angle"].notna()) &
                (group["Direction"].notna()) &
                (group["BatterSide"].notna())
            ].copy()

            # --- Compute xBA for all batted balls ---
            dir_angle = batted_ball_rows["Direction"].astype(float)
            dir_angle[batted_ball_rows["BatterSide"] == "Left"] *= -1  # mirror lefties
            ev_bin = batted_ball_rows["ExitSpeed"].round().astype(int)
            la_bin = batted_ball_rows["Angle"].round().astype(int)
            dir_bin = (dir_angle // 5 * 5).astype(int)

            # Use your neighbor-averaging function
            batted_ball_rows["xBA"] = [
                lookup_xBA(ev, la, dr) for ev, la, dr in zip(ev_bin, la_bin, dir_bin)
            ]

            # --- Predict xSLG for all batted balls ---
            if xslg_model is not None and not batted_ball_rows.empty:
                valid_xslg = batted_ball_rows[["ExitSpeed", "Angle", "Direction", "BatterSide"]].copy()
                valid_xslg["BatterSide"] = valid_xslg["BatterSide"].map({"Left": 0, "Right": 1})
                preds_xslg = xslg_model.predict(valid_xslg)
                batted_ball_rows["xSLG"] = preds_xslg
            else:
                batted_ball_rows["xSLG"] = 0

            # --- Drop any rows where xBA or xSLG is None just to be safe ---
            batted_ball_rows = batted_ball_rows.dropna(subset=["xBA", "xSLG"])

            # --- Barrel % calculation (skip rows with None) ---
            barrel_balls = batted_ball_rows[
                (batted_ball_rows["xBA"].notna()) &
                (batted_ball_rows["xSLG"].notna()) &
                (batted_ball_rows["xBA"] >= 0.5) &
                (batted_ball_rows["xSLG"] >= 1.5)
            ].shape[0]

            barrel_per = (barrel_balls / batted_balls) if batted_balls > 0 else None


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
                "Undefined": 0.0
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
                    valid_bb = batted_ball_rows[["ExitSpeed","Angle","Direction","BatterSide"]].copy()
                    valid_bb["BatterSide"] = valid_bb["BatterSide"].map({"Left":0,"Right":1})
                    preds = xwoba_model.predict(valid_bb)
                    sum_xwOBA_bb = np.sum(preds)
                else:
                    sum_xwOBA_bb = 0

                # Contributions from non-batted-ball events
                total_contrib = sum_xwOBA_bb \
                    + walks * woba_map["Walk"] \
                    + hbps * woba_map["HitByPitch"] \
                    + sacrifices * woba_map["Sacrifice"] \
                    + fielders_choice * woba_map["FieldersChoice"] \
                    + outs * woba_map["Out"]

                # Compute xwOBA
                batter_xwoba = total_contrib / pa
                batter_xwoba = max(batter_xwoba, 0)  # Clip minimum

            except Exception as e:
                print(f"Error computing xwOBA for {batter_name}: {e}")
                batter_xwoba = 0


            # Store computed stats for batter
            batter_stats = {
                "Batter": batter_name,
                "BatterTeam": batter_team,
                "Year": year,
                "plate_app": plate_appearances,
                "batted_balls": batted_balls,
                "avg_exit_velo": (
                    round(avg_exit_velo, 1) if avg_exit_velo is not None else None
                ),
                "k_per": round(k_percentage, 3) if k_percentage is not None else None,
                "bb_per": (
                    round(bb_percentage, 3) if bb_percentage is not None else None
                ),
                "la_sweet_spot_per": (
                    round(la_sweet_spot_per, 3)
                    if la_sweet_spot_per is not None
                    else None
                ),
                "hard_hit_per": (
                    round(hard_hit_per, 3) if hard_hit_per is not None else None
                ),
                "in_zone_pitches": in_zone_pitches,
                "whiff_per": round(whiff_per, 3) if whiff_per is not None else None,
                "out_of_zone_pitches": out_of_zone_pitches,
                "chase_per": round(chase_per, 3) if chase_per is not None else None,
                "infield_left_slice": infield_left_slice,
                "infield_left_per": (
                    round(infield_left_per, 3) if infield_left_per is not None else None
                ),
                "infield_lc_slice": infield_lc_slice,
                "infield_lc_per": (
                    round(infield_lc_per, 3) if infield_lc_per is not None else None
                ),
                "infield_center_slice": infield_center_slice,
                "infield_center_per": (
                    round(infield_center_per, 3)
                    if infield_center_per is not None
                    else None
                ),
                "infield_rc_slice": infield_rc_slice,
                "infield_rc_per": (
                    round(infield_rc_per, 3) if infield_rc_per is not None else None
                ),
                "infield_right_slice": infield_right_slice,
                "infield_right_per": round(infield_right_per, 3) if infield_right_per is not None else None,
                "xba_per": round(batter_xba, 3) if batter_xba is not None else None,
                "xslg_per": round(batter_xslg, 3) if batter_xslg is not None else None,
                "at_bats": at_bats,
                "xwoba_per": round(batter_xwoba, 3) if batter_xwoba is not None else None,
                "barrel_per": round(barrel_per, 3) if barrel_per is not None else None,
            }

            batters_dict[key] = batter_stats

        return batters_dict

    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return {}


def combine_advanced_batting_stats(existing_stats: Dict, new_stats: Dict) -> Dict:
    """Merge existing and new batting stats with explicit layout and rounded percentages"""

    if not existing_stats:
        return new_stats

    # Helper to safely get numeric values
    def safe_get(d, key):
        return d.get(key) if d.get(key) is not None else 0

    # Combine counts
    combined_plate_app = safe_get(existing_stats, "plate_app") + safe_get(new_stats, "plate_app")
    combined_batted_balls = safe_get(existing_stats, "batted_balls") + safe_get(new_stats, "batted_balls")
    combined_at_bats = safe_get(existing_stats, "at_bats") + safe_get(new_stats, "at_bats")
    combined_in_zone_pitches = safe_get(existing_stats, "in_zone_pitches") + safe_get(new_stats, "in_zone_pitches")
    combined_out_of_zone_pitches = safe_get(existing_stats, "out_of_zone_pitches") + safe_get(new_stats, "out_of_zone_pitches")

    # Weighted averages helper
    def weighted_avg(stat_key, weight_key, total_weight, round_digits=3):
        total = safe_get(existing_stats, stat_key) * safe_get(existing_stats, weight_key) + \
                safe_get(new_stats, stat_key) * safe_get(new_stats, weight_key)
        if total_weight > 0:
            return round(max(total / total_weight, 0), round_digits)
        return None

    # Compute weighted stats
    combined_avg_exit_velo = weighted_avg("avg_exit_velo", "batted_balls", combined_batted_balls, 1)
    combined_k_per = weighted_avg("k_per", "plate_app", combined_plate_app)
    combined_bb_per = weighted_avg("bb_per", "plate_app", combined_plate_app)
    combined_sweet_spot_per = weighted_avg("la_sweet_spot_per", "batted_balls", combined_batted_balls)
    combined_hard_hit_per = weighted_avg("hard_hit_per", "batted_balls", combined_batted_balls)
    combined_whiff_per = weighted_avg("whiff_per", "in_zone_pitches", combined_in_zone_pitches)
    combined_chase_per = weighted_avg("chase_per", "out_of_zone_pitches", combined_out_of_zone_pitches)
    combined_xba_per = weighted_avg("xba_per", "at_bats", combined_at_bats)
    combined_xslg_per = weighted_avg("xslg_per", "at_bats", combined_at_bats)
    combined_xwoba_per = weighted_avg("xwoba_per", "plate_app", combined_plate_app)
    combined_barrel_per = weighted_avg("barrel_per", "batted_balls", combined_batted_balls)

    # Combine infield slices
    slices = ["infield_left_slice", "infield_lc_slice", "infield_center_slice", "infield_rc_slice", "infield_right_slice"]
    combined_slices = {s: safe_get(existing_stats, s) + safe_get(new_stats, s) for s in slices}
    total_infield = sum(combined_slices.values())
    combined_slice_per = {s.replace("_slice", "_per"): round(v / total_infield, 3) if total_infield > 0 else None
                          for s, v in combined_slices.items()}

    # Explicit return layout
    return {
        "Batter": new_stats["Batter"],
        "BatterTeam": new_stats["BatterTeam"],
        "Year": new_stats["Year"],
        "plate_app": combined_plate_app,
        "batted_balls": combined_batted_balls,
        "at_bats": combined_at_bats,
        "avg_exit_velo": combined_avg_exit_velo,
        "k_per": combined_k_per,
        "bb_per": combined_bb_per,
        "la_sweet_spot_per": combined_sweet_spot_per,
        "hard_hit_per": combined_hard_hit_per,
        "in_zone_pitches": combined_in_zone_pitches,
        "whiff_per": combined_whiff_per,
        "out_of_zone_pitches": combined_out_of_zone_pitches,
        "chase_per": combined_chase_per,
        "infield_left_slice": combined_slices["infield_left_slice"],
        "infield_left_per": combined_slice_per["infield_left_per"],
        "infield_lc_slice": combined_slices["infield_lc_slice"],
        "infield_lc_per": combined_slice_per["infield_lc_per"],
        "infield_center_slice": combined_slices["infield_center_slice"],
        "infield_center_per": combined_slice_per["infield_center_per"],
        "infield_rc_slice": combined_slices["infield_rc_slice"],
        "infield_rc_per": combined_slice_per["infield_rc_per"],
        "infield_right_slice": combined_slices["infield_right_slice"],
        "infield_right_per": combined_slice_per["infield_right_per"],
        "xba_per": combined_xba_per,
        "xslg_per": combined_xslg_per,
        "xwoba_per": combined_xwoba_per,
        "barrel_per": combined_barrel_per
    }


def upload_advanced_batting_to_supabase(batters_dict: Dict[Tuple[str, str, int], Dict]):
    """Upload batting stats to Supabase and compute scaled percentile ranks"""
    if not batters_dict:
        print("No advanced batting stats to upload")
        return

    try:
        # Fetch existing records in batches
        existing_stats = {}
        offset = 0
        batch_size = 1000
        while True:
            result = (
                supabase.table("AdvancedBattingStats")
                .select("*")
                .range(offset, offset + batch_size - 1)
                .execute()
            )
            data = result.data
            if not data:
                break
            for record in data:
                key = (record["Batter"], record["BatterTeam"], record["Year"])
                existing_stats[key] = record
            offset += batch_size

        # Combine new stats with existing stats
        combined_stats = {}
        updated_count = 0
        new_count = 0
        for key, new_stat in batters_dict.items():
            if key in existing_stats:
                combined = combine_advanced_batting_stats(existing_stats[key], new_stat)
                if combined is existing_stats[key]:
                    # Date already processed; skip to avoid duplicate uploads
                    continue
                updated_count += 1
            else:
                combined = new_stat
                new_count += 1
            combined_stats[key] = combined

        # Convert combined stats to JSON-serializable list
        batter_data = []
        for batter_dict in combined_stats.values():
            clean_dict = {k: v for k, v in batter_dict.items() if k != "unique_games"}
            json_str = json.dumps(clean_dict, cls=NumpyEncoder)
            clean_batter = json.loads(json_str)
            batter_data.append(clean_batter)

        print(
            f"Preparing to upload {updated_count} existing records and {new_count} new players..."
        )

        # Upload data in batches
        upload_batch_size = 1000
        total_inserted = 0
        for i in range(0, len(batter_data), upload_batch_size):
            batch = batter_data[i : i + upload_batch_size]
            try:
                supabase.table("AdvancedBattingStats").upsert(
                    batch, on_conflict="Batter,BatterTeam,Year"
                ).execute()
                total_inserted += len(batch)
                print(
                    f"Uploaded batch {i//upload_batch_size + 1}: {len(batch)} records"
                )
            except Exception as batch_error:
                print(
                    f"Error uploading batch {i//upload_batch_size + 1}: {batch_error}"
                )
                if batch:
                    print(f"Sample record: {batch[0]}")
                continue

        print(f"Uploaded {total_inserted} combined batter records")

        # Fetch all records to compute scaled percentile ranks
        print("\nFetching all batter records for ranking...")
        all_records = []
        offset = 0
        while True:
            result = supabase.table("AdvancedBattingStats").select(
                "Batter,BatterTeam,Year,avg_exit_velo,k_per,"
                + "bb_per,la_sweet_spot_per,hard_hit_per,whiff_per,"
                + "chase_per,xba_per,xslg_per,xwoba_per,barrel_per"
            ).range(offset, offset + batch_size - 1).execute()
            data = result.data
            if not data:
                break
            all_records.extend(data)
            offset += batch_size
            print(f"Fetched {len(data)} records (total: {len(all_records)})")

        if not all_records:
            print("No records found for ranking.")
            return

        df = pd.DataFrame(all_records).dropna(subset=["Year"])

        # Helper: rank series and scale to 1-100
        def rank_and_scale_to_1_100(series, ascending=False):
            series = series.copy()
            mask = series.notna()
            if mask.sum() == 0:
                return pd.Series([None] * len(series), index=series.index)
            ranks = series[mask].rank(method="min", ascending=ascending)
            min_rank, max_rank = ranks.min(), ranks.max()
            scaled = (
                pd.Series([100.0] * mask.sum(), index=series[mask].index)
                if min_rank == max_rank
                else np.floor(1 + (ranks - min_rank) / (max_rank - min_rank) * 99)
            )
            result = pd.Series([None] * len(series), index=series.index)
            result[mask] = scaled
            return result

        # Compute rankings by year
        ranked_dfs = []
        for year, group in df.groupby("Year"):
            temp = group.copy()
            temp["avg_exit_velo_rank"] = rank_and_scale_to_1_100(
                temp["avg_exit_velo"], ascending=True
            )
            temp["k_per_rank"] = rank_and_scale_to_1_100(temp["k_per"], ascending=False)
            temp["bb_per_rank"] = rank_and_scale_to_1_100(temp["bb_per"], ascending=True)
            temp["la_sweet_spot_per_rank"] = rank_and_scale_to_1_100(temp["la_sweet_spot_per"], ascending=True)
            temp["hard_hit_per_rank"] = rank_and_scale_to_1_100(temp["hard_hit_per"], ascending=True)
            temp["whiff_per_rank"] = rank_and_scale_to_1_100(temp["whiff_per"], ascending=False)
            temp["chase_per_rank"] = rank_and_scale_to_1_100(temp["chase_per"], ascending=False)
            temp["xba_per_rank"] = rank_and_scale_to_1_100(temp["xba_per"], ascending=True)
            temp["xslg_per_rank"] = rank_and_scale_to_1_100(temp["xslg_per"], ascending=True)
            temp["xwoba_per_rank"] = rank_and_scale_to_1_100(temp["xwoba_per"], ascending=True)
            temp["barrel_per_rank"] = rank_and_scale_to_1_100(temp["barrel_per"], ascending=True)
            ranked_dfs.append(temp)

        ranked_df = pd.concat(ranked_dfs, ignore_index=True)
        print("Computed scaled percentile ranks by year.")

        # Prepare data for upload
        update_cols = [
            "Batter","BatterTeam","Year",
            "avg_exit_velo_rank","k_per_rank","bb_per_rank",
            "la_sweet_spot_per_rank","hard_hit_per_rank",
            "whiff_per_rank","chase_per_rank","xba_per_rank",
            "xslg_per_rank","xwoba_per_rank","barrel_per_rank"
        ]
        update_data = ranked_df[update_cols].to_dict(orient="records")
        for record in update_data:
            for key, value in record.items():
                if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
                    record[key] = None

        # Upload rank updates in batches
        print("\nUploading scaled percentile ranks...")
        total_updated = 0
        for i in range(0, len(update_data), upload_batch_size):
            batch = update_data[i : i + upload_batch_size]
            try:
                supabase.table("AdvancedBattingStats").upsert(
                    batch, on_conflict="Batter,BatterTeam,Year"
                ).execute()
                total_updated += len(batch)
                print(f"Updated batch {i//upload_batch_size + 1}: {len(batch)} records")
            except Exception as update_err:
                print(f"Error updating batch {i//upload_batch_size + 1}: {update_err}")
                if batch:
                    print(f"Sample record: {batch[0]}")
                continue

        print(
            f"Successfully updated ranks for {total_updated} records across all years."
        )

    except Exception as e:
        print(f"Supabase error: {e}")


if __name__ == "__main__":
    # Module entry point; designed for import
    print("Advanced Batting Stats utility module loaded")
