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
env = os.getenv('ENV', 'development')
load_dotenv(project_root / f'.env.{env}')

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

# Custom encoder to handle numpy types
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
    """Check if pitch is in strike zone"""
    try:
        height = float(plate_loc_height)
        side = float(plate_loc_side)
        return (
            MIN_PLATE_HEIGHT <= height <= MAX_PLATE_HEIGHT
            and MIN_PLATE_SIDE <= side <= MAX_PLATE_SIDE
        )
    except (ValueError, TypeError):
        return False


def get_advanced_batting_stats_from_buffer(buffer, filename: str) -> Dict[Tuple[str, str, int], Dict]:
    """Extract advanced batting statistics from a CSV file in-memory"""
    try:
        df = pd.read_csv(buffer)

        # Check if required columns exist
        required_columns = [
            "Batter",
            "BatterTeam",
            "KorBB",
            "PitchCall",
            "ExitSpeed",
        ]
        if not all(col in df.columns for col in required_columns):
            print(f"Warning: Missing required columns in {filename}")
            return {}

        # Extract year from filename
        file_date_parser = CSVFilenameParser()
        date_components = file_date_parser.get_date_components(filename)
        if not date_components:
            print(f"Warning: Could not extract date from filename {filename}, defaulting to 2025")
            year = 2025
        else:
            year = date_components[0]  # year is the first component

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
                ]
            )

            # Calculate batted balls (balls in play with exit speed)
            batted_balls = group[
                (group["PitchCall"] == "InPlay") &
                (group["ExitSpeed"].notna())
            ].shape[0]

            # Calculate LA Sweet Spot (launch angle between 8 and 32 degrees)
            sweet_spot_balls = group[
                (group["PitchCall"] == "InPlay") &
                (group["ExitSpeed"].notna()) &
                (group["Angle"].notna()) &
                (group["Angle"] >= 8) & (group["Angle"] <= 32)
            ].shape[0]
            la_sweet_spot_per = (sweet_spot_balls / batted_balls) if batted_balls > 0 else None

            # Calculate hard hit percentage (exit velocity >= 95 mph)
            hard_hit_balls = group[
                (group["PitchCall"] == "InPlay") &
                (group["ExitSpeed"].notna()) &
                (group["ExitSpeed"] >= 95)
            ].shape[0]
            hard_hit_per = (hard_hit_balls / batted_balls) if batted_balls > 0 else None

            # Calculate total exit velocity for average
            total_exit_velo = group[
                (group["PitchCall"] == "InPlay") &
                (group["ExitSpeed"].notna())
            ]["ExitSpeed"].sum()

            # Calculate average exit velocity
            avg_exit_velo = total_exit_velo / batted_balls if batted_balls > 0 else None

            # Calculate walks
            walks = len(group[group["KorBB"] == "Walk"])

            # Calculate strikeouts
            strikeouts = len(group[group["KorBB"] == "Strikeout"])

            # Calculate K %
            k_percentage = (
                strikeouts / plate_appearances if plate_appearances > 0 else None
            )

            # Calculate BB %
            bb_percentage = (
                walks / plate_appearances if plate_appearances > 0 else None
            )

            # Calculate zone statistics
            in_zone_pitches = 0
            out_of_zone_pitches = 0
            in_zone_whiffs = 0
            out_of_zone_swings = 0

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

            # Calculate whiff %
            whiff_per = (
                in_zone_whiffs / in_zone_pitches if in_zone_pitches > 0 else None
            )

            # Calculate chase %
            chase_per = (
                out_of_zone_swings / out_of_zone_pitches
                if out_of_zone_pitches > 0
                else None
            )

            batter_stats = {
                "Batter": batter_name,
                "BatterTeam": batter_team,
                "Year": year,
                "plate_app": plate_appearances,
                "batted_balls": batted_balls,
                "avg_exit_velo": round(avg_exit_velo, 1) if avg_exit_velo is not None else None,
                "k_per": round(k_percentage, 3) if k_percentage is not None else None,
                "bb_per": round(bb_percentage, 3) if bb_percentage is not None else None,
                "la_sweet_spot_per": round(la_sweet_spot_per, 3) if la_sweet_spot_per is not None else None,
                "hard_hit_per": round(hard_hit_per, 3) if hard_hit_per is not None else None,
                "in_zone_pitches": in_zone_pitches,
                "whiff_per": round(whiff_per, 3) if whiff_per is not None else None,
                "out_of_zone_pitches": out_of_zone_pitches,
                "chase_per": round(chase_per, 3) if chase_per is not None else None,
            }

            batters_dict[key] = batter_stats

        return batters_dict

    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return {}


def get_existing_advanced_batting_stats(batter_name: str, batter_team: str, year: int) -> Dict:
    """Get existing advanced batting stats for a player from Supabase"""
    try:
        result = (
            supabase.table("AdvancedBattingStats")
            .select("*")
            .eq("Batter", batter_name)
            .eq("BatterTeam", batter_team)
            .eq("Year", year)
            .execute()
        )
        
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"Error fetching existing stats for {batter_name}: {e}")
        return None


def combine_advanced_batting_stats(existing_stats: Dict, new_stats: Dict) -> Dict:
    """Combine existing and new advanced batting stats"""
    if not existing_stats:
        return new_stats
    
    # Combine plate appearances
    combined_plate_app = existing_stats.get("plate_app", 0) + new_stats.get("plate_app", 0)
    
    # Combine batted balls
    combined_batted_balls = existing_stats.get("batted_balls", 0) + new_stats.get("batted_balls", 0)
    
    # Calculate combined average exit velocity
    existing_total_exit_velo = (existing_stats.get("avg_exit_velo", 0) or 0) * (existing_stats.get("batted_balls", 0) or 0)
    new_total_exit_velo = (new_stats.get("avg_exit_velo", 0) or 0) * (new_stats.get("batted_balls", 0) or 0)
    
    combined_avg_exit_velo = None
    if combined_batted_balls > 0:
        total_exit_velo = existing_total_exit_velo + new_total_exit_velo
        combined_avg_exit_velo = total_exit_velo / combined_batted_balls
    
    # Combine K%
    existing_strikeouts = (existing_stats.get("k_per", 0) or 0) * (existing_stats.get("plate_app", 0) or 0)
    new_strikeouts = (new_stats.get("k_per", 0) or 0) * (new_stats.get("plate_app", 0) or 0)
    combined_k_per = (existing_strikeouts + new_strikeouts) / combined_plate_app if combined_plate_app > 0 else None
    
    # Combine BB%
    existing_walks = (existing_stats.get("bb_per", 0) or 0) * (existing_stats.get("plate_app", 0) or 0)
    new_walks = (new_stats.get("bb_per", 0) or 0) * (new_stats.get("plate_app", 0) or 0)
    combined_bb_per = (existing_walks + new_walks) / combined_plate_app if combined_plate_app > 0 else None
    
    # Combine LA Sweet Spot %
    existing_sweet_spot = (existing_stats.get("la_sweet_spot_per", 0) or 0) * (existing_stats.get("batted_balls", 0) or 0)
    new_sweet_spot = (new_stats.get("la_sweet_spot_per", 0) or 0) * (new_stats.get("batted_balls", 0) or 0)
    combined_sweet_spot_per = (existing_sweet_spot + new_sweet_spot) / combined_batted_balls if combined_batted_balls > 0 else None
    
    # Combine Hard Hit %
    existing_hard_hit = (existing_stats.get("hard_hit_per", 0) or 0) * (existing_stats.get("batted_balls", 0) or 0)
    new_hard_hit = (new_stats.get("hard_hit_per", 0) or 0) * (new_stats.get("batted_balls", 0) or 0)
    combined_hard_hit_per = (existing_hard_hit + new_hard_hit) / combined_batted_balls if combined_batted_balls > 0 else None

    # Combine in_zone_pitches
    combined_in_zone_pitches = existing_stats.get("in_zone_pitches", 0) + new_stats.get("in_zone_pitches", 0)

    # Combine whiff %
    existing_in_zone_whiffs = (existing_stats.get("whiff_per", 0) or 0) * (existing_stats.get("in_zone_pitches", 0) or 0)
    new_in_zone_whiffs = (new_stats.get("whiff_per", 0) or 0) * (new_stats.get("in_zone_pitches", 0) or 0)
    combined_whiff_per = (existing_in_zone_whiffs + new_in_zone_whiffs) / combined_in_zone_pitches if combined_in_zone_pitches > 0 else None

    # Combine out_of_zone_pitches
    combined_out_of_zone_pitches = existing_stats.get("out_of_zone_pitches", 0) + new_stats.get("out_of_zone_pitches", 0)

    # Combine chase %
    existing_out_of_zone_swings = (existing_stats.get("chase_per", 0) or 0) * (existing_stats.get("out_of_zone_pitches", 0) or 0)
    new_out_of_zone_swings = (new_stats.get("chase_per", 0) or 0) * (new_stats.get("out_of_zone_pitches", 0) or 0)
    combined_chase_per = (existing_out_of_zone_swings + new_out_of_zone_swings) / combined_out_of_zone_pitches if combined_out_of_zone_pitches > 0 else None

    return {
        "Batter": new_stats["Batter"],
        "BatterTeam": new_stats["BatterTeam"],
        "Year": new_stats["Year"],
        "plate_app": combined_plate_app,
        "batted_balls": combined_batted_balls,
        "avg_exit_velo": round(combined_avg_exit_velo, 1) if combined_avg_exit_velo is not None else None,
        "k_per": round(combined_k_per, 3) if combined_k_per is not None else None,
        "bb_per": round(combined_bb_per, 3) if combined_bb_per is not None else None,
        "la_sweet_spot_per": round(combined_sweet_spot_per, 3) if combined_sweet_spot_per is not None else None,
        "hard_hit_per": round(combined_hard_hit_per, 3) if combined_hard_hit_per is not None else None,
        "in_zone_pitches": combined_in_zone_pitches,
        "whiff_per": round(combined_whiff_per, 3) if combined_whiff_per is not None else None,
        "out_of_zone_pitches": combined_out_of_zone_pitches,
        "chase_per": round(combined_chase_per, 3) if combined_chase_per is not None else None,
    }

def upload_advanced_batting_to_supabase(batters_dict: Dict[Tuple[str, str, int], Dict]):
    """Upload advanced batting statistics to Supabase and compute scaled percentile ranks"""
    if not batters_dict:
        print("No advanced batting stats to upload")
        return

    try:
        # Convert dictionary values to list and ensure JSON serializable
        batter_data = []
        for batter_dict in batters_dict.values():
            clean_dict = {k: v for k, v in batter_dict.items() if k != "unique_games"}
            json_str = json.dumps(clean_dict, cls=NumpyEncoder)
            clean_batter = json.loads(json_str)
            batter_data.append(clean_batter)

        print(f"Preparing to upload {len(batter_data)} advanced batting stats...")

        # Upload initial data in batches
        batch_size = 100
        total_inserted = 0

        for i in range(0, len(batter_data), batch_size):
            batch = batter_data[i : i + batch_size]
            try:
                supabase.table("AdvancedBattingStats").upsert(
                    batch, on_conflict="Batter,BatterTeam,Year"
                ).execute()
                total_inserted += len(batch)
                print(f"Uploaded batch {i//batch_size + 1}: {len(batch)} records")
            except Exception as batch_error:
                print(f"Error uploading batch {i//batch_size + 1}: {batch_error}")
                if batch:
                    print(f"Sample record: {batch[0]}")
                continue

        print(f"Successfully processed {total_inserted} batter records")

        # ================================================
        # Compute 1-99 scaled percentile ranks
        # ================================================
        print("Fetching all batter records to compute scaled percentile ranks...")

        all_records = []
        offset = 0
        batch_size = 1000

        while True:
            result = supabase.table("AdvancedBattingStats").select(
                "Batter,BatterTeam,Year,avg_exit_velo,k_per,bb_per,la_sweet_spot_per,hard_hit_per,whiff_per,chase_per"
            ).range(offset, offset + batch_size - 1).execute()
            
            data = result.data
            if not data:
                break
            all_records.extend(data)
            offset += batch_size
            print(f"Fetched {len(data)} records (total so far: {len(all_records)})")

        if not all_records:
            print("No records found to rank.")
            return

        df = pd.DataFrame(all_records).dropna(subset=["Year"])

        # Corrected ranking function
        def rank_and_scale_to_1_99(series, ascending=False):
            """
            Rank the series with ties sharing the same rank, then apply min-max scaling (1-99).
            ascending=False means higher values are better.
            """
            series = series.copy()
            mask = series.notna()
            if mask.sum() == 0:
                return pd.Series([None] * len(series), index=series.index)
            
            # Step 1: Rank with ties — same rank for equal values
            ranks = series[mask].rank(method="min", ascending=ascending)
            
            # Step 2: Min-max scale ranks to 1–99
            min_rank = ranks.min()
            max_rank = ranks.max()
            if min_rank == max_rank:
                scaled = pd.Series([99.0] * mask.sum(), index=series[mask].index)
            else:
                scaled = 1 + (ranks - min_rank) / (max_rank - min_rank) * 98
            
            result = pd.Series([None] * len(series), index=series.index)
            result[mask] = scaled.round(3)
            return result

        print("\nComputing ranked and scaled percentile values per year...")

        ranked_dfs = []
        for year, group in df.groupby("Year"):
            temp = group.copy()

            # Higher is better for most metrics, lower is better for k_per
            temp["avg_exit_velo_rank"] = rank_and_scale_to_1_99(temp["avg_exit_velo"], ascending=True)
            temp["k_per_rank"] = rank_and_scale_to_1_99(temp["k_per"], ascending=False)
            temp["bb_per_rank"] = rank_and_scale_to_1_99(temp["bb_per"], ascending=True)
            temp["la_sweet_spot_per_rank"] = rank_and_scale_to_1_99(temp["la_sweet_spot_per"], ascending=True)
            temp["hard_hit_per_rank"] = rank_and_scale_to_1_99(temp["hard_hit_per"], ascending=True)
            temp["whiff_per_rank"] = rank_and_scale_to_1_99(temp["whiff_per"], ascending=False)
            temp["chase_per_rank"] = rank_and_scale_to_1_99(temp["chase_per"], ascending=False)

            ranked_dfs.append(temp)

        ranked_df = pd.concat(ranked_dfs, ignore_index=True)
        print("Computed ranked and scaled percentile values by year.")


        # Prepare data for Supabase
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

        # Sanitize NaN / inf values
        for record in update_data:
            for key, value in record.items():
                if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
                    record[key] = None

        # Upload ranks in batches
        print("Uploading scaled percentile rank updates to Supabase...")
        total_updated = 0
        for i in range(0, len(update_data), batch_size):
            batch = update_data[i : i + batch_size]
            try:
                supabase.table("AdvancedBattingStats").upsert(
                    batch, on_conflict="Batter,BatterTeam,Year"
                ).execute()
                total_updated += len(batch)
                print(f"Updated rank batch {i//batch_size + 1}: {len(batch)} records")
            except Exception as update_err:
                print(f"Error updating batch {i//batch_size + 1}: {update_err}")
                if batch:
                    print(f"Sample record: {batch[0]}")
                continue

        print(f"Successfully updated scaled percentile ranks for {total_updated} records across all years.")

    except Exception as e:
        print(f"Supabase error: {e}")


if __name__ == "__main__":
    # This script is designed to be imported and used by other scripts
    # The main processing logic should be called from the main data processing script
    print("Advanced Batting Stats utility module loaded")
