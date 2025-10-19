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
import re
import json
import numpy as np
from typing import Dict, Tuple, List, Set
from pathlib import Path
from .file_date import CSVFilenameParser

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
        df = pd.read_csv(buffer)

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
                (group["PitchCall"] == "InPlay")
                & (group["ExitSpeed"].notna())
                & (group["Angle"]).notna()
            ].shape[0]

            # LA Sweet Spot percentage
            sweet_spot_balls = group[
                (group["PitchCall"] == "InPlay")
                & (group["ExitSpeed"].notna())
                & (group["Angle"].notna())
                & (group["Angle"] >= 8)
                & (group["Angle"] <= 32)
            ].shape[0]
            la_sweet_spot_per = (
                (sweet_spot_balls / batted_balls) if batted_balls > 0 else None
            )

            # Hard hit percentage
            hard_hit_balls = group[
                (group["PitchCall"] == "InPlay")
                & (group["ExitSpeed"].notna())
                & (group["ExitSpeed"] >= 95)
                & (group["Angle"].notna())
            ].shape[0]
            hard_hit_per = (hard_hit_balls / batted_balls) if batted_balls > 0 else None

            # Total and average exit velocity
            total_exit_velo = group[
                (group["PitchCall"] == "InPlay")
                & (group["ExitSpeed"].notna())
                & (group["Angle"].notna())
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
                "infield_right_per": (
                    round(infield_right_per, 3)
                    if infield_right_per is not None
                    else None
                ),
                "processed_dates": [game_date_str],
            }

            batters_dict[key] = batter_stats

        return batters_dict

    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return {}


def combine_advanced_batting_stats(existing_stats: Dict, new_stats: Dict) -> Dict:
    """Merge existing and new batting stats, updating rates and percentages"""
    if not existing_stats:
        return new_stats

    existing_dates = set(existing_stats.get("processed_dates") or [])
    new_dates = set(new_stats.get("processed_dates") or [])

    if new_dates and new_dates.issubset(existing_dates):
        return existing_stats

    # Combine plate appearances and batted balls
    combined_plate_app = existing_stats.get("plate_app", 0) + new_stats.get(
        "plate_app", 0
    )
    combined_batted_balls = existing_stats.get("batted_balls", 0) + new_stats.get(
        "batted_balls", 0
    )

    # Compute combined average exit velocity
    existing_total_exit_velo = (existing_stats.get("avg_exit_velo", 0) or 0) * (
        existing_stats.get("batted_balls", 0) or 0
    )
    new_total_exit_velo = (new_stats.get("avg_exit_velo", 0) or 0) * (
        new_stats.get("batted_balls", 0) or 0
    )
    combined_avg_exit_velo = None
    if combined_batted_balls > 0:
        total_exit_velo = existing_total_exit_velo + new_total_exit_velo
        combined_avg_exit_velo = total_exit_velo / combined_batted_balls

    # Combine K% and BB%
    existing_strikeouts = (existing_stats.get("k_per", 0) or 0) * (
        existing_stats.get("plate_app", 0) or 0
    )
    new_strikeouts = (new_stats.get("k_per", 0) or 0) * (
        new_stats.get("plate_app", 0) or 0
    )
    combined_k_per = (
        (existing_strikeouts + new_strikeouts) / combined_plate_app
        if combined_plate_app > 0
        else None
    )

    existing_walks = (existing_stats.get("bb_per", 0) or 0) * (
        existing_stats.get("plate_app", 0) or 0
    )
    new_walks = (new_stats.get("bb_per", 0) or 0) * (new_stats.get("plate_app", 0) or 0)
    combined_bb_per = (
        (existing_walks + new_walks) / combined_plate_app
        if combined_plate_app > 0
        else None
    )

    # Combine LA Sweet Spot and Hard Hit percentages
    existing_sweet_spot = (existing_stats.get("la_sweet_spot_per", 0) or 0) * (
        existing_stats.get("batted_balls", 0) or 0
    )
    new_sweet_spot = (new_stats.get("la_sweet_spot_per", 0) or 0) * (
        new_stats.get("batted_balls", 0) or 0
    )
    combined_sweet_spot_per = (
        (existing_sweet_spot + new_sweet_spot) / combined_batted_balls
        if combined_batted_balls > 0
        else None
    )

    existing_hard_hit = (existing_stats.get("hard_hit_per", 0) or 0) * (
        existing_stats.get("batted_balls", 0) or 0
    )
    new_hard_hit = (new_stats.get("hard_hit_per", 0) or 0) * (
        new_stats.get("batted_balls", 0) or 0
    )
    combined_hard_hit_per = (
        (existing_hard_hit + new_hard_hit) / combined_batted_balls
        if combined_batted_balls > 0
        else None
    )

    # Combine in-zone stats
    combined_in_zone_pitches = existing_stats.get("in_zone_pitches", 0) + new_stats.get(
        "in_zone_pitches", 0
    )
    existing_in_zone_whiffs = (existing_stats.get("whiff_per", 0) or 0) * (
        existing_stats.get("in_zone_pitches", 0) or 0
    )
    new_in_zone_whiffs = (new_stats.get("whiff_per", 0) or 0) * (
        new_stats.get("in_zone_pitches", 0) or 0
    )
    combined_whiff_per = (
        (existing_in_zone_whiffs + new_in_zone_whiffs) / combined_in_zone_pitches
        if combined_in_zone_pitches > 0
        else None
    )

    # Combine out-of-zone stats
    combined_out_of_zone_pitches = existing_stats.get(
        "out_of_zone_pitches", 0
    ) + new_stats.get("out_of_zone_pitches", 0)
    existing_out_of_zone_swings = (existing_stats.get("chase_per", 0) or 0) * (
        existing_stats.get("out_of_zone_pitches", 0) or 0
    )
    new_out_of_zone_swings = (new_stats.get("chase_per", 0) or 0) * (
        new_stats.get("out_of_zone_pitches", 0) or 0
    )
    combined_chase_per = (
        (existing_out_of_zone_swings + new_out_of_zone_swings)
        / combined_out_of_zone_pitches
        if combined_out_of_zone_pitches > 0
        else None
    )

    # Combine infield slices
    combined_infield_left_slice = existing_stats.get(
        "infield_left_slice", 0
    ) + new_stats.get("infield_left_slice", 0)
    combined_infield_lc_slice = existing_stats.get(
        "infield_lc_slice", 0
    ) + new_stats.get("infield_lc_slice", 0)
    combined_infield_center_slice = existing_stats.get(
        "infield_center_slice", 0
    ) + new_stats.get("infield_center_slice", 0)
    combined_infield_rc_slice = existing_stats.get(
        "infield_rc_slice", 0
    ) + new_stats.get("infield_rc_slice", 0)
    combined_infield_right_slice = existing_stats.get(
        "infield_right_slice", 0
    ) + new_stats.get("infield_right_slice", 0)

    # Compute combined infield slice percentages
    total_infield_batted_balls = (
        combined_infield_left_slice
        + combined_infield_lc_slice
        + combined_infield_center_slice
        + combined_infield_rc_slice
        + combined_infield_right_slice
    )
    combined_infield_left_per = (
        combined_infield_left_slice / total_infield_batted_balls
        if total_infield_batted_balls > 0
        else None
    )
    combined_infield_lc_per = (
        combined_infield_lc_slice / total_infield_batted_balls
        if total_infield_batted_balls > 0
        else None
    )
    combined_infield_center_per = (
        combined_infield_center_slice / total_infield_batted_balls
        if total_infield_batted_balls > 0
        else None
    )
    combined_infield_rc_per = (
        combined_infield_rc_slice / total_infield_batted_balls
        if total_infield_batted_balls > 0
        else None
    )
    combined_infield_right_per = (
        combined_infield_right_slice / total_infield_batted_balls
        if total_infield_batted_balls > 0
        else None
    )

    combined_dates = sorted(existing_dates.union(new_dates))

    return {
        "Batter": new_stats["Batter"],
        "BatterTeam": new_stats["BatterTeam"],
        "Year": new_stats["Year"],
        "plate_app": combined_plate_app,
        "batted_balls": combined_batted_balls,
        "avg_exit_velo": (
            round(combined_avg_exit_velo, 1)
            if combined_avg_exit_velo is not None
            else None
        ),
        "k_per": round(combined_k_per, 3) if combined_k_per is not None else None,
        "bb_per": round(combined_bb_per, 3) if combined_bb_per is not None else None,
        "la_sweet_spot_per": (
            round(combined_sweet_spot_per, 3)
            if combined_sweet_spot_per is not None
            else None
        ),
        "hard_hit_per": (
            round(combined_hard_hit_per, 3)
            if combined_hard_hit_per is not None
            else None
        ),
        "in_zone_pitches": combined_in_zone_pitches,
        "whiff_per": (
            round(combined_whiff_per, 3) if combined_whiff_per is not None else None
        ),
        "out_of_zone_pitches": combined_out_of_zone_pitches,
        "chase_per": (
            round(combined_chase_per, 3) if combined_chase_per is not None else None
        ),
        "infield_left_slice": combined_infield_left_slice,
        "infield_left_per": (
            round(combined_infield_left_per, 3)
            if combined_infield_left_per is not None
            else None
        ),
        "infield_lc_slice": combined_infield_lc_slice,
        "infield_lc_per": (
            round(combined_infield_lc_per, 3)
            if combined_infield_lc_per is not None
            else None
        ),
        "infield_center_slice": combined_infield_center_slice,
        "infield_center_per": (
            round(combined_infield_center_per, 3)
            if combined_infield_center_per is not None
            else None
        ),
        "infield_rc_slice": combined_infield_rc_slice,
        "infield_rc_per": (
            round(combined_infield_rc_per, 3)
            if combined_infield_rc_per is not None
            else None
        ),
        "infield_right_slice": combined_infield_right_slice,
        "infield_right_per": (
            round(combined_infield_right_per, 3)
            if combined_infield_right_per is not None
            else None
        ),
        "processed_dates": combined_dates,
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
            result = (
                supabase.table("AdvancedBattingStats")
                .select(
                    "Batter,BatterTeam,Year,avg_exit_velo,k_per,bb_per,la_sweet_spot_per,hard_hit_per,whiff_per,chase_per"
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
                temp["avg_exit_velo"], ascending=True
            )
            temp["k_per_rank"] = rank_and_scale_to_1_100(temp["k_per"], ascending=False)
            temp["bb_per_rank"] = rank_and_scale_to_1_100(
                temp["bb_per"], ascending=True
            )
            temp["la_sweet_spot_per_rank"] = rank_and_scale_to_1_100(
                temp["la_sweet_spot_per"], ascending=True
            )
            temp["hard_hit_per_rank"] = rank_and_scale_to_1_100(
                temp["hard_hit_per"], ascending=True
            )
            temp["whiff_per_rank"] = rank_and_scale_to_1_100(
                temp["whiff_per"], ascending=False
            )
            temp["chase_per_rank"] = rank_and_scale_to_1_100(
                temp["chase_per"], ascending=False
            )
            ranked_dfs.append(temp)

        ranked_df = pd.concat(ranked_dfs, ignore_index=True)
        print("Computed scaled percentile ranks by year.")

        # Prepare data for upload
        update_cols = [
            "Batter",
            "BatterTeam",
            "Year",
            "avg_exit_velo_rank",
            "k_per_rank",
            "bb_per_rank",
            "la_sweet_spot_per_rank",
            "hard_hit_per_rank",
            "whiff_per_rank",
            "chase_per_rank",
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
