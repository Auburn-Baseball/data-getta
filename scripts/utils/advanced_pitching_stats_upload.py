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

import json
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from supabase import Client, create_client

from .common import SUPABASE_KEY, SUPABASE_URL, NumpyEncoder
from .file_date import CSVFilenameParser
import xgboost as xgb
import bisect

# Initialize Supabase client
if SUPABASE_URL is None or SUPABASE_KEY is None:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Strike zone constants
MIN_PLATE_SIDE = -0.86
MAX_PLATE_SIDE = 0.86
MAX_PLATE_HEIGHT = 3.55
MIN_PLATE_HEIGHT = 1.77


# Load xBA grid for fast lookups
XBA_GRID_PATH = project_root / "scripts" / "utils" / "models" / "xBA_grid.csv"
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
XSLG_MODEL_PATH = (
    project_root / "scripts" / "utils" / "models" / "xslg_model.json"
)
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
XWOBAM_MODEL_PATH = (
    project_root / "scripts" / "utils" / "models" / "xwoba_model.json"
)
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


def get_advanced_pitching_stats_from_buffer(
    buffer, filename: str
) -> Dict[Tuple[str, str, int], Dict]:
    """Extract advanced pitching stats from CSV in memory"""
    try:
        cols_needed = [
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
        df = pd.read_csv(buffer, usecols=cols_needed)

        is_practice = False
        if "League" in df.columns:
            league_values = df["League"].dropna().astype(str).str.strip().str.upper()
            is_practice = (league_values == "TEAM").any()

        # Verify required columns exist
        required_columns = ["Pitcher", "PitcherTeam"]
        if not all(col in df.columns for col in required_columns):
            print(f"Warning: Missing required columns in {filename}")
            return {}

        # Extract year and game date from filename
        file_date_parser = CSVFilenameParser()
        date_components = file_date_parser.get_date_components(filename)
        if not date_components:
            raise ValueError(f"Unable to extract date from filename: {filename}")
        year = date_components[0]

        game_date_obj = file_date_parser.get_date_object(filename)
        if game_date_obj is None:
            raise ValueError(f"Unable to parse game date from filename: {filename}")
        game_date_str = str(game_date_obj)

        pitchers_dict = {}

        # Group by pitcher and team
        grouped = df.groupby(["Pitcher", "PitcherTeam"])

        for (pitcher_name, pitcher_team), group in grouped:
            if pd.isna(pitcher_name) or pd.isna(pitcher_team):
                continue

            pitcher_name = str(pitcher_name).strip()
            if is_practice:
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
                    height = (
                        float(row["PlateLocHeight"]) if pd.notna(row["PlateLocHeight"]) else None
                    )
                    side = float(row["PlateLocSide"]) if pd.notna(row["PlateLocSide"]) else None

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
                valid_xslg = batted_ball_rows[
                    ["ExitSpeed", "Angle", "Direction", "BatterSide"]
                ].copy()
                valid_xslg["BatterSide"] = valid_xslg["BatterSide"].map(
                    {"Left": 0, "Right": 1}
                )
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

            barrel_per = (barrel_balls / batted_balls) if batted_balls > 0 else None

            # --- Compute xBA per batter ---
            if not batted_ball_rows.empty:
                avg_xba_batted_balls = batted_ball_rows["xBA"].mean()
                batter_xba = (
                    (avg_xba_batted_balls * batted_balls) / at_bats
                    if at_bats > 0
                    else 0
                )
                batter_xba = max(batter_xba, 0)  # Clip minimum
            else:
                batter_xba = 0

            # --- Compute xSLG per batter ---
            if not batted_ball_rows.empty:
                avg_xslg_batted_balls = batted_ball_rows["xSLG"].mean()
                batter_xslg = (
                    (avg_xslg_batted_balls * batted_balls) / at_bats
                    if at_bats > 0
                    else 0
                )
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
                    valid_bb["BatterSide"] = valid_bb["BatterSide"].map(
                        {"Left": 0, "Right": 1}
                    )
                    preds = xwoba_model.predict(valid_bb)
                    sum_xwOBA_bb = np.sum(preds)
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
                "avg_exit_velo": (round(avg_exit_velo, 1) if avg_exit_velo is not None else None),
                "k_per": round(k_percentage, 3) if k_percentage is not None else None,
                "bb_per": (round(bb_percentage, 3) if bb_percentage is not None else None),
                "la_sweet_spot_per": (
                    round(la_sweet_spot_per, 3) if la_sweet_spot_per is not None else None
                ),
                "hard_hit_per": (round(hard_hit_per, 3) if hard_hit_per is not None else None),
                "in_zone_pitches": in_zone_pitches,
                "whiff_per": round(whiff_per, 3) if whiff_per is not None else None,
                "out_of_zone_pitches": out_of_zone_pitches,
                "chase_per": round(chase_per, 3) if chase_per is not None else None,
                "fastballs": fastballs,
                "avg_fastball_velo": (
                    round(avg_fastball_velo, 1) if avg_fastball_velo is not None else None
                ),
                "ground_balls": ground_balls,
                "gb_per": round(gb_per, 3) if gb_per is not None else None,
                "xba_per": round(batter_xba, 3) if batter_xba is not None else None,
                "xslg_per": round(batter_xslg, 3) if batter_xslg is not None else None,
                "at_bats": at_bats,
                "xwoba_per": (
                    round(batter_xwoba, 3) if batter_xwoba is not None else None
                ),
                "barrel_per": round(barrel_per, 3) if barrel_per is not None else None,
            }

            pitchers_dict[key] = pitcher_stats

        return pitchers_dict

    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return {}


def combine_advanced_pitching_stats(existing_stats: Dict, new_stats: Dict) -> Dict:
    """Merge existing and new pitching stats, updating rates and percentages safely"""

    if not existing_stats:
        return new_stats

    existing_dates = set(existing_stats.get("processed_dates") or [])
    new_dates = set(new_stats.get("processed_dates") or [])

    if new_dates and new_dates.issubset(existing_dates):
        return existing_stats

    # Helper to safely get numeric values
    def safe_get(d, key):
        return d.get(key) if d.get(key) is not None else 0

    # Combine counts
    combined_plate_app = safe_get(existing_stats, "plate_app") + safe_get(
        new_stats, "plate_app"
    )
    combined_batted_balls = safe_get(existing_stats, "batted_balls") + safe_get(
        new_stats, "batted_balls"
    )
    combined_ground_balls = safe_get(existing_stats, "ground_balls") + safe_get(
        new_stats, "ground_balls"
    )
    combined_in_zone_pitches = safe_get(existing_stats, "in_zone_pitches") + safe_get(
        new_stats, "in_zone_pitches"
    )
    combined_out_of_zone_pitches = safe_get(
        existing_stats, "out_of_zone_pitches"
    ) + safe_get(new_stats, "out_of_zone_pitches")
    combined_fastballs = safe_get(existing_stats, "fastballs") + safe_get(
        new_stats, "fastballs"
    )
    combined_at_bats = safe_get(existing_stats, "at_bats") + safe_get(
        new_stats, "at_bats"
    )

    # Weighted averages helper
    def weighted_avg(stat_key, weight_key, total_weight, round_digits=3):
        total = safe_get(existing_stats, stat_key) * safe_get(
            existing_stats, weight_key
        ) + safe_get(new_stats, stat_key) * safe_get(new_stats, weight_key)
        if total_weight > 0:
            return round(max(total / total_weight, 0), round_digits)
        return None

    combined_avg_exit_velo = weighted_avg(
        "avg_exit_velo", "batted_balls", combined_batted_balls, 1
    )
    combined_k_per = weighted_avg("k_per", "plate_app", combined_plate_app, 3)
    combined_bb_per = weighted_avg("bb_per", "plate_app", combined_plate_app, 3)
    combined_gb_per = weighted_avg("gb_per", "batted_balls", combined_batted_balls, 3)
    combined_sweet_spot_per = weighted_avg(
        "la_sweet_spot_per", "batted_balls", combined_batted_balls, 3
    )
    combined_hard_hit_per = weighted_avg(
        "hard_hit_per", "batted_balls", combined_batted_balls, 3
    )
    combined_whiff_per = weighted_avg(
        "whiff_per", "in_zone_pitches", combined_in_zone_pitches, 3
    )
    combined_chase_per = weighted_avg(
        "chase_per", "out_of_zone_pitches", combined_out_of_zone_pitches, 3
    )
    combined_avg_fastball_velo = weighted_avg(
        "avg_fastball_velo", "fastballs", combined_fastballs, 1
    )
    combined_xba_per = weighted_avg("xba_per", "at_bats", combined_at_bats)
    combined_xslg_per = weighted_avg("xslg_per", "at_bats", combined_at_bats)
    combined_xwoba_per = weighted_avg("xwoba_per", "plate_app", combined_plate_app)
    combined_barrel_per = weighted_avg(
        "barrel_per", "batted_balls", combined_batted_balls
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


def upload_advanced_pitching_to_supabase(
    pitchers_dict: Dict[Tuple[str, str, int], Dict],
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
        while True:
            result = (
                supabase.table("AdvancedPitchingStats")
                .select("*")
                .range(offset, offset + batch_size - 1)
                .execute()
            )
            data = result.data
            if not data:
                break
            for record in data:
                stat_key = (record["Pitcher"], record["PitcherTeam"], record["Year"])
                existing_stats[stat_key] = record
            offset += batch_size

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
                temp["avg_exit_velo"], ascending=False
            )
            temp["k_per_rank"] = rank_and_scale_to_1_100(temp["k_per"], ascending=True)
            temp["bb_per_rank"] = rank_and_scale_to_1_100(temp["bb_per"], ascending=False)
            temp["la_sweet_spot_per_rank"] = rank_and_scale_to_1_100(
                temp["la_sweet_spot_per"], ascending=False
            )
            temp["hard_hit_per_rank"] = rank_and_scale_to_1_100(
                temp["hard_hit_per"], ascending=False
            )
            temp["whiff_per_rank"] = rank_and_scale_to_1_100(temp["whiff_per"], ascending=True)
            temp["chase_per_rank"] = rank_and_scale_to_1_100(temp["chase_per"], ascending=True)
            temp["avg_fastball_rank"] = rank_and_scale_to_1_100(
                temp["avg_fastball_velo"], ascending=True
            )
            temp["gb_per_rank"] = rank_and_scale_to_1_100(
                temp["gb_per"], ascending=True
            )
            temp["xba_per_rank"] = rank_and_scale_to_1_100(
                temp["xba_per"], ascending=False
            )
            temp["xslg_per_rank"] = rank_and_scale_to_1_100(
                temp["xslg_per"], ascending=False
            )
            temp["xwoba_per_rank"] = rank_and_scale_to_1_100(
                temp["xwoba_per"], ascending=False
            )
            temp["barrel_per_rank"] = rank_and_scale_to_1_100(
                temp["barrel_per"], ascending=True
            )
            ranked_dfs.append(temp)

        ranked_df = pd.concat(ranked_dfs, ignore_index=True)
        print("Computed scaled percentile ranks by year.")

        # Prepare data for upload
        update_cols = [
            "Pitcher",
            "PitcherTeam",
            "Year",
            "avg_exit_velo_rank",
            "k_per_rank",
            "bb_per_rank",
            "la_sweet_spot_per_rank",
            "hard_hit_per_rank",
            "whiff_per_rank",
            "chase_per_rank",
            "avg_fastball_rank",
            "gb_per_rank",
            "xba_per_rank",
            "xslg_per_rank",
            "xwoba_per_rank",
            "barrel_per_rank",
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
