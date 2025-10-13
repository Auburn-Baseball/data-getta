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

# Custom encoder to handle numpy types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        return super(NumpyEncoder, self).default(obj)


def get_pitch_counts_from_buffer(buffer, filename: str) -> Dict[Tuple[str, str, int], Dict]:
    """Extract pitch count statistics from a CSV file"""
    try:
        df = pd.read_csv(buffer)

        # Determine if this is practice data by checking League column
        is_pratice = False
        if "League" in df.columns:
            league_values = df["League"].dropna().astype(str).str.strip().str.upper()
            is_practice = (league_values == "TEAM").any()
        # Get game date from filename
        date_parser = CSVFilenameParser()
        game_date = str(date_parser.get_date_object(filename))

        # Check if required columns exist
        required_columns = [
            "Pitcher",
            "PitcherTeam",
            "AutoPitchType",
            "TaggedPitchType",
        ]
        if not all(col in df.columns for col in required_columns):
            print(f"Warning: Missing required columns in {filename}")
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

            # Count total pitches
            total_pitches = len(group)

            # Count specific pitch types based on AutoPitchType
            curveball_count = len(group[group["AutoPitchType"] == "Curveball"])
            fourseam_count = len(group[group["AutoPitchType"] == "Four-Seam"])
            sinker_count = len(group[group["AutoPitchType"] == "Sinker"])
            slider_count = len(group[group["AutoPitchType"] == "Slider"])
            changeup_count = len(group[group["AutoPitchType"] == "Changeup"])
            cutter_count = len(group[group["AutoPitchType"] == "Cutter"])
            splitter_count = len(group[group["AutoPitchType"] == "Splitter"])

            # Two-seam count: TaggedPitchType = 'Fastball' AND AutoPitchType != 'Four-Seam'
            twoseam_count = len(
                group[
                    (group["TaggedPitchType"] == "Fastball")
                    & (group["AutoPitchType"] != "Four-Seam")
                ]
            )

            # Other count: AutoPitchType = 'Other' OR 'NaN' (including actual NaN values)
            other_count = len(
                group[
                    (group["AutoPitchType"] == "Other")
                    | (group["AutoPitchType"] == "NaN")
                    | (group["AutoPitchType"].isna())
                ]
            )

            # Get unique games from this file - store as a set for later merging
            unique_games = (
                set(group["GameUID"].dropna().unique())
                if "GameUID" in group.columns
                else set()
            )

            pitch_stats = {
                "Pitcher": pitcher_name,
                "PitcherTeam": pitcher_team,
                "Date": game_date,
                "total_pitches": total_pitches,
                "curveball_count": curveball_count,
                "fourseam_count": fourseam_count,
                "sinker_count": sinker_count,
                "slider_count": slider_count,
                "twoseam_count": twoseam_count,
                "changeup_count": changeup_count,
                "cutter_count": cutter_count,
                "splitter_count": splitter_count,
                "other_count": other_count,
                "unique_games": unique_games,  # Store the set of unique games
                "games": len(unique_games),  # This will be recalculated later
                "is_practice": is_practice,
            }

            pitchers_dict[key] = pitch_stats

        return pitchers_dict

    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return {}


def upload_pitches_to_supabase(pitchers_dict: Dict[Tuple[str, str, int], Dict]):
    """Upload pitch count statistics to Supabase"""
    if not pitchers_dict:
        print("No pitch data to upload")
        return

    try:
        # Convert dictionary values to list and ensure JSON serializable
        pitch_data = []
        for pitcher_dict in pitchers_dict.values():
            # Remove the unique_games set before uploading (it's not needed in the DB)
            clean_dict = {k: v for k, v in pitcher_dict.items() if k != "unique_games"}

            # Convert to JSON and back to ensure all numpy types are converted
            json_str = json.dumps(clean_dict, cls=NumpyEncoder)
            clean_pitcher = json.loads(json_str)
            pitch_data.append(clean_pitcher)

        print(f"Preparing to upload {len(pitch_data)} unique pitcher pitch counts...")

        # Insert data in batches to avoid request size limits
        batch_size = 100
        total_inserted = 0

        for i in range(0, len(pitch_data), batch_size):
            batch = pitch_data[i : i + batch_size]

            try:
                # Use upsert to handle conflicts based on primary key
                result = (
                    supabase.table(f"PitchCounts")
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

        print(f"Successfully processed {total_inserted} pitch count records")

        # Get final count
        count_result = (
            supabase.table(f"PitchCounts")
            .select("*", count="exact")
            .execute()
        )
        total_pitchers = count_result.count
        print(f"Total pitcher pitch counts in database: {total_pitchers}")

    except Exception as e:
        print(f"Supabase error: {e}")
