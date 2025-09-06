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
project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env')

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
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        return super(NumpyEncoder, self).default(obj)


def should_exclude_file(filename: str) -> bool:
    """Check if file should be excluded based on name patterns"""
    exclude_patterns = ["playerpositioning", "fhc", "unverified"]
    filename_lower = filename.lower()
    return any(pattern in filename_lower for pattern in exclude_patterns)


def get_pitch_counts_from_csv(file_path: str) -> Dict[Tuple[str, str, int], Dict]:
    """Extract pitch count statistics from a CSV file"""
    try:
        df = pd.read_csv(file_path)

        # Check if required columns exist
        required_columns = [
            "Pitcher",
            "PitcherTeam",
            "AutoPitchType",
            "TaggedPitchType",
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
                "Year": 2025,
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
            }

            pitchers_dict[key] = pitch_stats

        return pitchers_dict

    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {}


def process_csv_folder(csv_folder_path: str) -> Dict[Tuple[str, str, int], Dict]:
    """Process all 2025 CSV files in the folder"""
    all_pitchers = {}

    # Look in the 2025 subfolder
    year_folder = os.path.join(csv_folder_path, "2025")

    if not os.path.exists(year_folder):
        print(f"2025 CSV folder not found: {year_folder}")
        return all_pitchers

    # Get all CSV files
    csv_files = [f for f in os.listdir(year_folder) if f.endswith(".csv")]

    # Filter out unwanted patterns
    filtered_files = []
    for file in csv_files:
        if not should_exclude_file(file):
            filtered_files.append(file)
        else:
            print(f"Excluding file: {file}")

    print(f"Found {len(filtered_files)} 2025 CSV files to process")

    for filename in filtered_files:
        file_path = os.path.join(year_folder, filename)

        print(f"Processing: {filename}")

        pitchers_from_file = get_pitch_counts_from_csv(file_path)

        # Merge pitchers from this file with the main dictionary
        for key, pitcher_data in pitchers_from_file.items():
            if key in all_pitchers:
                # Pitcher already exists, merge the stats
                existing = all_pitchers[key]

                # Add up counting stats
                counting_stats = [
                    "total_pitches",
                    "curveball_count",
                    "fourseam_count",
                    "sinker_count",
                    "slider_count",
                    "twoseam_count",
                    "changeup_count",
                    "cutter_count",
                    "splitter_count",
                    "other_count",
                ]
                for stat in counting_stats:
                    existing[stat] += pitcher_data[stat]

                # MERGE THE UNIQUE GAMES SETS
                existing["unique_games"].update(pitcher_data["unique_games"])
                existing["games"] = len(existing["unique_games"])

            else:
                # New pitcher, add to dictionary
                all_pitchers[key] = pitcher_data

        print(f"  Found {len(pitchers_from_file)} unique pitchers in this file")
        print(f"  Total unique pitchers so far: {len(all_pitchers)}")

    return all_pitchers


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
                    supabase.table("PitchCounts")
                    .upsert(batch, on_conflict="Pitcher,PitcherTeam,Year")
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
            supabase.table("PitchCounts")
            .select("*", count="exact")
            .eq("Year", 2025)
            .execute()
        )
        total_pitchers = count_result.count
        print(f"Total 2025 pitcher pitch counts in database: {total_pitchers}")

    except Exception as e:
        print(f"Supabase error: {e}")


def main():
    print("Starting pitch count CSV processing...")

    # Set the path to your CSV folder
    csv_folder_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "csv")
    print(f"Looking for CSV files in: {csv_folder_path}")

    # Process all CSV files and collect unique pitchers
    all_pitchers = process_csv_folder(csv_folder_path)

    print(f"\nTotal unique pitchers found: {len(all_pitchers)}")

    # Show sample of pitchers found
    if all_pitchers:
        print("\nSample pitchers:")
        for i, (key, pitcher) in enumerate(list(all_pitchers.items())[:5]):
            name, team, year = key
            print(
                f"  {pitcher['Pitcher']} - Team: {pitcher['PitcherTeam']}, "
                f"Total Pitches: {pitcher['total_pitches']}, "
                f"Fastballs: {pitcher['fourseam_count']}, "
                f"Curveballs: {pitcher['curveball_count']}, "
                f"Games: {pitcher['games']}"
            )

        # Show some statistics
        total_pitches = sum(p["total_pitches"] for p in all_pitchers.values())
        total_fastballs = sum(p["fourseam_count"] for p in all_pitchers.values())
        total_curveballs = sum(p["curveball_count"] for p in all_pitchers.values())
        total_sliders = sum(p["slider_count"] for p in all_pitchers.values())
        total_games = sum(p["games"] for p in all_pitchers.values())

        print(f"\nStatistics:")
        print(f"  Total pitches: {total_pitches}")
        print(f"  Total four-seam fastballs: {total_fastballs}")
        print(f"  Total curveballs: {total_curveballs}")
        print(f"  Total sliders: {total_sliders}")
        print(f"  Total games pitched (all players): {total_games}")
        print(
            f"  Average pitches per game: {round(total_pitches / total_games, 1) if total_games > 0 else 'N/A'}"
        )

        # Upload to Supabase
        print("\nUploading to Supabase...")
        upload_pitches_to_supabase(all_pitchers)
    else:
        print("No pitch data found to upload")


if __name__ == "__main__":
    main()
