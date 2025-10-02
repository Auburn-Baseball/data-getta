import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client
import re
import json
import numpy as np
from typing import Dict, Tuple, List, Set
from pathlib import Path

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


def calculate_innings_pitched(strikeouts, outs_on_play):
    """Calculate innings pitched from outs (3 outs = 1 inning)"""
    total_outs = strikeouts + outs_on_play
    full_innings = total_outs // 3
    partial_outs = total_outs % 3
    return round(full_innings + (partial_outs / 10), 1)


def get_pitcher_stats_from_buffer(buffer, filename: str) -> Dict[Tuple[str, str, int], Dict]:
    """Extract pitcher statistics from a CSV file"""
    try:
        df = pd.read_csv(buffer)

        # Check if required columns exist
        required_columns = [
            "Pitcher",
            "PitcherTeam",
            "KorBB",
            "PitchCall",
            "PlateLocHeight",
            "PlateLocSide",
            "Inning",
            "Outs",
            "Balls",
            "Strikes",
            "PAofInning",
            "OutsOnPlay",
            "Batter",
        ]
        if not all(col in df.columns for col in required_columns):
            print(f"Warning: Missing required columns in {file_path}")
            return {}

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

            key = (pitcher_name, pitcher_team, 2025)

            # Calculate basic counting stats
            total_strikeouts_pitcher = len(group[group["KorBB"] == "Strikeout"])
            total_walks_pitcher = len(group[group["KorBB"] == "Walk"])
            pitches = len(group)

            # Calculate games started (first batter of first inning with 0-0 count)
            games_started = len(
                group[
                    (group["Inning"] == 1)
                    & (group["Outs"] == 0)
                    & (group["Balls"] == 0)
                    & (group["Strikes"] == 0)
                    & (group["PAofInning"] == 1)
                ]
            )

            # Calculate innings pitched
            strikeouts_for_innings = total_strikeouts_pitcher
            outs_on_play = group["OutsOnPlay"].fillna(0).astype(int).sum()
            total_innings_pitched = calculate_innings_pitched(
                strikeouts_for_innings, outs_on_play
            )

            # Calculate batters faced (unique plate appearances)
            if "GameUID" in group.columns:
                total_batters_faced = len(
                    group.drop_duplicates(["PAofInning", "Inning", "Batter", "GameUID"])
                )
            else:
                total_batters_faced = len(
                    group.drop_duplicates(["PAofInning", "Inning", "Batter"])
                )

            # Calculate zone statistics
            in_zone_count = 0
            out_of_zone_count = 0
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
                            in_zone_count += 1
                            if row["PitchCall"] == "StrikeSwinging":
                                in_zone_whiffs += 1
                        else:
                            out_of_zone_count += 1
                            if row["PitchCall"] in [
                                "StrikeSwinging",
                                "FoulBallNotFieldable",
                                "InPlay",
                            ]:
                                out_of_zone_swings += 1
                except (ValueError, TypeError):
                    continue

            # Calculate percentages
            k_percentage = (
                total_strikeouts_pitcher / total_batters_faced
                if total_batters_faced > 0
                else None
            )
            base_on_ball_percentage = (
                total_walks_pitcher / total_batters_faced
                if total_batters_faced > 0
                else None
            )
            in_zone_whiff_percentage = (
                in_zone_whiffs / in_zone_count if in_zone_count > 0 else None
            )
            chase_percentage = (
                out_of_zone_swings / out_of_zone_count
                if out_of_zone_count > 0
                else None
            )

            # Get unique games from this file - store as a set for later merging
            unique_games = (
                set(group["GameUID"].dropna().unique())
                if "GameUID" in group.columns
                else set()
            )

            pitcher_stats = {
                "Pitcher": pitcher_name,
                "PitcherTeam": pitcher_team,
                "total_strikeouts_pitcher": total_strikeouts_pitcher,
                "total_walks_pitcher": total_walks_pitcher,
                "total_out_of_zone_pitches": out_of_zone_count,
                "total_in_zone_pitches": in_zone_count,
                "misses_in_zone": in_zone_whiffs,
                "swings_in_zone": 0,  # This requires more complex logic from the SQL
                "total_num_chases": out_of_zone_swings,
                "pitches": pitches,
                "games_started": games_started,
                "total_innings_pitched": total_innings_pitched,
                "total_batters_faced": total_batters_faced,
                "k_percentage": round(k_percentage, 3)
                if k_percentage is not None
                else None,
                "base_on_ball_percentage": round(base_on_ball_percentage, 3)
                if base_on_ball_percentage is not None
                else None,
                "in_zone_whiff_percentage": round(in_zone_whiff_percentage, 3)
                if in_zone_whiff_percentage is not None
                else None,
                "chase_percentage": round(chase_percentage, 3)
                if chase_percentage is not None
                else None,
                "unique_games": unique_games,  # Store the set of unique games
                "games": len(unique_games),  # This will be recalculated later
            }

            pitchers_dict[key] = pitcher_stats

        return pitchers_dict

    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {}


def upload_pitchers_to_supabase(pitchers_dict: Dict[Tuple[str, str, int], Dict]):
    """Upload pitcher statistics to Supabase"""
    if not pitchers_dict:
        print("No pitchers to upload")
        return

    try:
        # Convert dictionary values to list and ensure JSON serializable
        pitcher_data = []
        for pitcher_dict in pitchers_dict.values():
            # Remove the unique_games set before uploading (it's not needed in the DB)
            clean_dict = {k: v for k, v in pitcher_dict.items() if k != "unique_games"}

            # Convert to JSON and back to ensure all numpy types are converted
            json_str = json.dumps(clean_dict, cls=NumpyEncoder)
            clean_pitcher = json.loads(json_str)
            pitcher_data.append(clean_pitcher)

        print(f"Preparing to upload {len(pitcher_data)} unique pitchers...")

        # Insert data in batches to avoid request size limits
        batch_size = 100
        total_inserted = 0

        for i in range(0, len(pitcher_data), batch_size):
            batch = pitcher_data[i : i + batch_size]

            try:
                # Use upsert to handle conflicts based on primary key
                result = (
                    supabase.table(f"PitcherStats")
                    .upsert(batch, on_conflict="Pitcher,PitcherTeam,Date")
                    .execute()
                )

                total_inserted += len(batch)
                print(f"Uploaded batch {i//batch_size + 1}: {len(batch)} records")

            except Exception as batch_error:
                print(f"Error uploading batch {i//batch_size + 1}: {batch_error}")
                # Print first record of failed batch for debugging
                if batch:
                    print(f"Sample record from failed batch: {batch[0]}")
                continue

        print(f"Successfully processed {total_inserted} pitcher records")

        # Get final count
        count_result = (
            supabase.table(f"PitcherStats")
            .select("*", count="exact")
            .execute()
        )
        total_pitchers = count_result.count
        print(f"Total 2025 pitchers in database: {total_pitchers}")

    except Exception as e:
        print(f"Supabase error: {e}")
