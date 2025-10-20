"""
Author: Joshua Reed
Created: 15 October 2025
Updated: 15 October 2025

Advanced Pitching Stats Utility Module
- Loads environment variables and initializes Supabase client
- Defines strike zone constants and helper functions
- Extracts, calculates, and combines advanced pitching stats from CSV files
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


def get_advanced_pitching_stats_from_buffer(
    buffer, filename: str
) -> Dict[Tuple[str, str, int], Dict]:
    """Extract advanced pitching stats from CSV in memory"""
    try:
        df = pd.read_csv(buffer)

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
            pitcher_team = str(pitcher_team).strip()

            if not pitcher_name or not pitcher_team:
                continue

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
            ].shape[0]

            # Calculate ground balls
            ground_balls = group[
                (group["PitchCall"] == "InPlay")
                & (group["TaggedHitType"] == "GroundBall")
                & (group["ExitSpeed"].notna())
                & (group["Angle"]).notna()
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

            # Total and average release velocity of fastballs
            total_fastball_velo = group[
                (group["TaggedPitchType"] == "Fastball") & (group["RelSpeed"].notna())
            ]["RelSpeed"].sum()
            avg_fastball_velo = (
                total_fastball_velo / fastballs if fastballs > 0 else None
            )

            # Walks and strikeouts
            walks = len(group[group["KorBB"] == "Walk"])
            strikeouts = len(group[group["KorBB"] == "Strikeout"])

            # K% and BB%
            k_percentage = (
                strikeouts / plate_appearances if plate_appearances > 0 else None
            )
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

            # Whiff and chase percentages
            whiff_per = (
                in_zone_whiffs / in_zone_pitches if in_zone_pitches > 0 else None
            )
            chase_per = (
                out_of_zone_swings / out_of_zone_pitches
                if out_of_zone_pitches > 0
                else None
            )

            # Store computed stats for pitcher
            pitcher_stats = {
                "Pitcher": pitcher_name,
                "PitcherTeam": pitcher_team,
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
                "fastballs": fastballs,
                "avg_fastball_velo": (
                    round(avg_fastball_velo, 1)
                    if avg_fastball_velo is not None
                    else None
                ),
                "ground_balls": ground_balls,
                "gb_per": round(gb_per, 3) if gb_per is not None else None,
                "processed_dates": [game_date_str],
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

    # Combine plate appearances and batted balls
    existing_plate_app = safe_get(existing_stats, "plate_app")
    new_plate_app = safe_get(new_stats, "plate_app")
    combined_plate_app = existing_plate_app + new_plate_app

    existing_batted_balls = safe_get(existing_stats, "batted_balls")
    new_batted_balls = safe_get(new_stats, "batted_balls")
    combined_batted_balls = existing_batted_balls + new_batted_balls

    # Combine ground balls
    existing_ground_balls = safe_get(existing_stats, "ground_balls")
    new_ground_balls = safe_get(new_stats, "ground_balls")
    combined_ground_balls = existing_ground_balls + new_ground_balls

    # Compute combined average exit velocity
    existing_total_exit_velo = (
        safe_get(existing_stats, "avg_exit_velo") * existing_batted_balls
    )
    new_total_exit_velo = safe_get(new_stats, "avg_exit_velo") * new_batted_balls
    combined_avg_exit_velo = (
        (existing_total_exit_velo + new_total_exit_velo) / combined_batted_balls
        if combined_batted_balls > 0
        else None
    )

    # Combine K% and BB%
    existing_strikeouts = safe_get(existing_stats, "k_per") * existing_plate_app
    new_strikeouts = safe_get(new_stats, "k_per") * new_plate_app
    combined_k_per = (
        (existing_strikeouts + new_strikeouts) / combined_plate_app
        if combined_plate_app > 0
        else None
    )

    existing_walks = safe_get(existing_stats, "bb_per") * existing_plate_app
    new_walks = safe_get(new_stats, "bb_per") * new_plate_app
    combined_bb_per = (
        (existing_walks + new_walks) / combined_plate_app
        if combined_plate_app > 0
        else None
    )

    # Combine GB %
    existing_gb_per = safe_get(existing_stats, "gb_per") * existing_batted_balls
    new_gb_per = safe_get(new_stats, "gb_per") * new_batted_balls
    combined_gb_per = (
        (existing_gb_per + new_gb_per) / combined_batted_balls
        if combined_batted_balls > 0
        else None
    )

    # Combine LA Sweet Spot and Hard Hit percentages
    existing_sweet_spot = (
        safe_get(existing_stats, "la_sweet_spot_per") * existing_batted_balls
    )
    new_sweet_spot = safe_get(new_stats, "la_sweet_spot_per") * new_batted_balls
    combined_sweet_spot_per = (
        (existing_sweet_spot + new_sweet_spot) / combined_batted_balls
        if combined_batted_balls > 0
        else None
    )

    existing_hard_hit = safe_get(existing_stats, "hard_hit_per") * existing_batted_balls
    new_hard_hit = safe_get(new_stats, "hard_hit_per") * new_batted_balls
    combined_hard_hit_per = (
        (existing_hard_hit + new_hard_hit) / combined_batted_balls
        if combined_batted_balls > 0
        else None
    )

    # Combine in-zone stats
    existing_in_zone_pitches = safe_get(existing_stats, "in_zone_pitches")
    new_in_zone_pitches = safe_get(new_stats, "in_zone_pitches")
    combined_in_zone_pitches = existing_in_zone_pitches + new_in_zone_pitches

    existing_in_zone_whiffs = (
        safe_get(existing_stats, "whiff_per") * existing_in_zone_pitches
    )
    new_in_zone_whiffs = safe_get(new_stats, "whiff_per") * new_in_zone_pitches
    combined_whiff_per = (
        (existing_in_zone_whiffs + new_in_zone_whiffs) / combined_in_zone_pitches
        if combined_in_zone_pitches > 0
        else None
    )

    # Combine out-of-zone stats
    existing_out_of_zone_pitches = safe_get(existing_stats, "out_of_zone_pitches")
    new_out_of_zone_pitches = safe_get(new_stats, "out_of_zone_pitches")
    combined_out_of_zone_pitches = (
        existing_out_of_zone_pitches + new_out_of_zone_pitches
    )

    existing_out_of_zone_swings = (
        safe_get(existing_stats, "chase_per") * existing_out_of_zone_pitches
    )
    new_out_of_zone_swings = safe_get(new_stats, "chase_per") * new_out_of_zone_pitches
    combined_chase_per = (
        (existing_out_of_zone_swings + new_out_of_zone_swings)
        / combined_out_of_zone_pitches
        if combined_out_of_zone_pitches > 0
        else None
    )

    # Combine fastball stats
    existing_fastballs = safe_get(existing_stats, "fastballs")
    new_fastballs = safe_get(new_stats, "fastballs")
    combined_fastballs = existing_fastballs + new_fastballs

    existing_total_fastball_velo = (
        safe_get(existing_stats, "avg_fastball_velo") * existing_fastballs
    )
    new_total_fastball_velo = safe_get(new_stats, "avg_fastball_velo") * new_fastballs
    combined_avg_fastball_velo = (
        (existing_total_fastball_velo + new_total_fastball_velo) / combined_fastballs
        if combined_fastballs > 0
        else None
    )

    combined_dates = sorted(existing_dates.union(new_dates))

    return {
        "Pitcher": new_stats["Pitcher"],
        "PitcherTeam": new_stats["PitcherTeam"],
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
        "fastballs": combined_fastballs,
        "avg_fastball_velo": (
            round(combined_avg_fastball_velo, 1)
            if combined_avg_fastball_velo is not None
            else None
        ),
        "ground_balls": combined_ground_balls,
        "gb_per": round(combined_gb_per, 3) if combined_gb_per is not None else None,
        "processed_dates": combined_dates,
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
                key = (record["Pitcher"], record["PitcherTeam"], record["Year"])
                existing_stats[key] = record
            offset += batch_size

        # Combine new stats with existing stats
        combined_stats = {}
        updated_count = 0
        new_count = 0
        for key, new_stat in pitchers_dict.items():
            if key in existing_stats:
                combined = combine_advanced_pitching_stats(
                    existing_stats[key], new_stat
                )
                if combined is existing_stats[key]:
                    continue
                updated_count += 1
            else:
                combined = new_stat
                new_count += 1
            combined_stats[key] = combined

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
                    + "avg_fastball_velo, gb_per"
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
            temp["bb_per_rank"] = rank_and_scale_to_1_100(
                temp["bb_per"], ascending=False
            )
            temp["la_sweet_spot_per_rank"] = rank_and_scale_to_1_100(
                temp["la_sweet_spot_per"], ascending=False
            )
            temp["hard_hit_per_rank"] = rank_and_scale_to_1_100(
                temp["hard_hit_per"], ascending=False
            )
            temp["whiff_per_rank"] = rank_and_scale_to_1_100(
                temp["whiff_per"], ascending=True
            )
            temp["chase_per_rank"] = rank_and_scale_to_1_100(
                temp["chase_per"], ascending=True
            )
            temp["avg_fastball_rank"] = rank_and_scale_to_1_100(
                temp["avg_fastball_velo"], ascending=True
            )
            temp["gb_per_rank"] = rank_and_scale_to_1_100(
                temp["gb_per"], ascending=True
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

        print(
            f"Successfully updated ranks for {total_updated} records across all years."
        )

    except Exception as e:
        print(f"Supabase error: {e}")


if __name__ == "__main__":
    # Module entry point; designed for import
    print("Advanced Pitching Stats utility module loaded")
