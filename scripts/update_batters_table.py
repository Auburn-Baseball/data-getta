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


def should_exclude_file(filename: str) -> bool:
    """Check if file should be excluded based on name patterns"""
    exclude_patterns = ["playerpositioning", "fhc", "unverified"]
    filename_lower = filename.lower()
    return any(pattern in filename_lower for pattern in exclude_patterns)


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


def calculate_total_bases(play_result):
    """Calculate total bases for a play result"""
    if play_result == "Single":
        return 1
    elif play_result == "Double":
        return 2
    elif play_result == "Triple":
        return 3
    elif play_result == "HomeRun":
        return 4
    else:
        return 0


def get_batter_stats_from_csv(file_path: str) -> Dict[Tuple[str, str, int], Dict]:
    """Extract batter statistics from a CSV file"""
    try:
        df = pd.read_csv(file_path)

        # Check if required columns exist
        required_columns = [
            "Batter",
            "BatterTeam",
            "PlayResult",
            "KorBB",
            "PitchCall",
            "PlateLocHeight",
            "PlateLocSide",
            "TaggedHitType",
        ]
        if not all(col in df.columns for col in required_columns):
            print(f"Warning: Missing required columns in {file_path}")
            return {}

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

            key = (batter_name, batter_team, 2025)

            # Calculate hits
            hits = len(
                group[
                    group["PlayResult"].isin(["Single", "Double", "Triple", "HomeRun"])
                ]
            )

            # Calculate at-bats
            at_bats = len(
                group[
                    group["PlayResult"].isin(
                        [
                            "Error",
                            "Out",
                            "FieldersChoice",
                            "Single",
                            "Double",
                            "Triple",
                            "HomeRun",
                        ]
                    )
                    | (group["KorBB"] == "Strikeout")
                ]
            )

            # Calculate strikes
            strikes = len(
                group[
                    group["PitchCall"].isin(
                        ["StrikeCalled", "StrikeSwinging", "FoulBallNotFieldable"]
                    )
                ]
            )

            # Calculate walks
            walks = len(group[group["KorBB"] == "Walk"])

            # Calculate strikeouts
            strikeouts = len(group[group["KorBB"] == "Strikeout"])

            # Calculate home runs
            homeruns = len(group[group["PlayResult"] == "HomeRun"])

            # Calculate extra base hits
            extra_base_hits = len(
                group[group["PlayResult"].isin(["Double", "Triple", "HomeRun"])]
            )

            # Calculate plate appearances
            plate_appearances = len(
                group[
                    group["KorBB"].isin(["Walk", "Strikeout"])
                    | group["PitchCall"].isin(["InPlay", "HitByPitch"])
                ]
            )

            # Calculate hit by pitch
            hit_by_pitch = len(group[group["PitchCall"] == "HitByPitch"])

            # Calculate sacrifices
            sacrifice = len(group[group["PlayResult"] == "Sacrifice"])

            # Calculate total bases
            total_bases = group["PlayResult"].apply(calculate_total_bases).sum()

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
            batting_average = round(hits / at_bats, 3) if at_bats > 0 else 0.000

            on_base_percentage = round(
                (hits + walks + hit_by_pitch) / (at_bats + walks + hit_by_pitch + sacrifice), 3
            ) if (at_bats + walks + hit_by_pitch + sacrifice) > 0 else 0.000

            slugging_percentage = round(total_bases / at_bats, 3) if at_bats > 0 else 0.000

            onbase_plus_slugging = round(on_base_percentage + slugging_percentage, 3)

            isolated_power = round(slugging_percentage - batting_average, 3)

            k_percentage = (
                strikeouts / plate_appearances if plate_appearances > 0 else None
            )

            base_on_ball_percentage = (
                walks / plate_appearances if plate_appearances > 0 else None
            )

            chase_percentage = (
                out_of_zone_swings / out_of_zone_count
                if out_of_zone_count > 0
                else None
            )

            in_zone_whiff_percentage = (
                in_zone_whiffs / in_zone_count if in_zone_count > 0 else None
            )

            # Get unique games from this file - store as a set for later merging
            unique_games = (
                set(group["GameUID"].dropna().unique())
                if "GameUID" in group.columns
                else set()
            )

            batter_stats = {
                "Batter": batter_name,
                "BatterTeam": batter_team,
                "Year": 2025,
                "hits": hits,
                "at_bats": at_bats,
                "strikes": strikes,
                "walks": walks,
                "strikeouts": strikeouts,
                "homeruns": homeruns,
                "extra_base_hits": extra_base_hits,
                "plate_appearances": plate_appearances,
                "hit_by_pitch": hit_by_pitch,
                "sacrifice": sacrifice,
                "total_bases": total_bases,
                "batting_average": round(batting_average, 3)
                if batting_average is not None
                else None,
                "on_base_percentage": round(on_base_percentage, 3)
                if on_base_percentage is not None
                else None,
                "slugging_percentage": round(slugging_percentage, 3)
                if slugging_percentage is not None
                else None,
                "onbase_plus_slugging": round(onbase_plus_slugging, 3)
                if onbase_plus_slugging is not None
                else None,
                "isolated_power": round(isolated_power, 3)
                if isolated_power is not None
                else None,
                "k_percentage": round(k_percentage, 3)
                if k_percentage is not None
                else None,
                "base_on_ball_percentage": round(base_on_ball_percentage, 3)
                if base_on_ball_percentage is not None
                else None,
                "chase_percentage": round(chase_percentage, 3)
                if chase_percentage is not None
                else None,
                "in_zone_whiff_percentage": round(in_zone_whiff_percentage, 3)
                if in_zone_whiff_percentage is not None
                else None,
                "unique_games": unique_games,  # Store the set of unique games
                "games": len(unique_games),  # This will be recalculated later
            }

            batters_dict[key] = batter_stats

        return batters_dict

    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {}


def process_csv_folder(csv_folder_path: str) -> Dict[Tuple[str, str, int], Dict]:
    """Process all 2025 CSV files in the folder"""
    all_batters = {}

    # Look in the 2025 subfolder
    year_folder = os.path.join(csv_folder_path, "2025")

    if not os.path.exists(year_folder):
        print(f"2025 CSV folder not found: {year_folder}")
        return all_batters

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

        batters_from_file = get_batter_stats_from_csv(file_path)

        # Merge batters from this file with the main dictionary
        for key, batter_data in batters_from_file.items():
            if key in all_batters:
                # Batter already exists, merge the stats
                existing = all_batters[key]

                # Add up counting stats
                for stat in [
                    "hits",
                    "at_bats",
                    "strikes",
                    "walks",
                    "strikeouts",
                    "homeruns",
                    "extra_base_hits",
                    "plate_appearances",
                    "hit_by_pitch",
                    "sacrifice",
                    "total_bases",
                ]:
                    existing[stat] += batter_data[stat]

                # MERGE THE UNIQUE GAMES SETS - This is the key fix!
                existing["unique_games"].update(batter_data["unique_games"])
                existing["games"] = len(existing["unique_games"])

                # Recalculate percentages
                existing["batting_average"] = round(existing["hits"] / existing["at_bats"], 3) \
                    if existing["at_bats"] > 0 else 0.000
                existing["on_base_percentage"] = round(
                    (existing["hits"] + existing["walks"] + existing["hit_by_pitch"]) /
                    (existing["at_bats"] + existing["walks"] + existing["hit_by_pitch"] + existing["sacrifice"]),
                    3
                ) if (existing["at_bats"] + existing["walks"] + existing["hit_by_pitch"] + existing["sacrifice"]) > 0 else 0.000
                existing["slugging_percentage"] = round(existing["total_bases"] / existing["at_bats"], 3) \
                    if existing["at_bats"] > 0 else 0.000

                existing["onbase_plus_slugging"] = round(
                    existing["on_base_percentage"] + existing["slugging_percentage"], 3
                )

                existing["isolated_power"] = round(
                    existing["slugging_percentage"] - existing["batting_average"], 3
                )
                existing["k_percentage"] = (
                    round(existing["strikeouts"] / existing["plate_appearances"], 3)
                    if existing["plate_appearances"] > 0
                    else None
                )
                existing["base_on_ball_percentage"] = (
                    round(existing["walks"] / existing["plate_appearances"], 3)
                    if existing["plate_appearances"] > 0
                    else None
                )
            else:
                # New batter, add to dictionary
                all_batters[key] = batter_data

        print(f"  Found {len(batters_from_file)} unique batters in this file")
        print(f"  Total unique batters so far: {len(all_batters)}")

    return all_batters


def upload_batters_to_supabase(batters_dict: Dict[Tuple[str, str, int], Dict]):
    """Upload batter statistics to Supabase"""
    if not batters_dict:
        print("No batters to upload")
        return

    try:
        # Convert dictionary values to list and ensure JSON serializable
        batter_data = []
        for batter_dict in batters_dict.values():
            # Remove the unique_games set before uploading (it's not needed in the DB)
            clean_dict = {k: v for k, v in batter_dict.items() if k != "unique_games"}

            # Convert to JSON and back to ensure all numpy types are converted
            json_str = json.dumps(clean_dict, cls=NumpyEncoder)
            clean_batter = json.loads(json_str)
            batter_data.append(clean_batter)

        print(f"Preparing to upload {len(batter_data)} unique batters...")

        # Insert data in batches to avoid request size limits
        batch_size = 100
        total_inserted = 0

        for i in range(0, len(batter_data), batch_size):
            batch = batter_data[i : i + batch_size]

            try:
                # Use upsert to handle conflicts based on primary key
                result = (
                    supabase.table("BatterStats")
                    .upsert(batch, on_conflict="Batter,BatterTeam,Year")
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

        print(f"Successfully processed {total_inserted} batter records")

        # Get final count
        count_result = (
            supabase.table("BatterStats")
            .select("*", count="exact")
            .eq("Year", 2025)
            .execute()
        )
        total_batters = count_result.count
        print(f"Total 2025 batters in database: {total_batters}")

    except Exception as e:
        print(f"Supabase error: {e}")


def main():
    print("Starting batter statistics CSV processing...")

    # Set the path to your CSV folder
    csv_folder_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "csv")
    print(f"Looking for CSV files in: {csv_folder_path}")

    # Process all CSV files and collect unique batters
    all_batters = process_csv_folder(csv_folder_path)

    print(f"\nTotal unique batters found: {len(all_batters)}")

    # Show sample of batters found
    if all_batters:
        print("\nSample batters:")
        for i, (key, batter) in enumerate(list(all_batters.items())[:5]):
            name, team, year = key
            print(
                f"  {batter['Batter']} - Team: {batter['BatterTeam']}, "
                f"AVG: {batter['batting_average']}, HR: {batter['homeruns']}, Games: {batter['games']}"
            )

        # Show some statistics
        total_hits = sum(b["hits"] for b in all_batters.values())
        total_at_bats = sum(b["at_bats"] for b in all_batters.values())
        total_homeruns = sum(b["homeruns"] for b in all_batters.values())
        total_games = sum(b["games"] for b in all_batters.values())

        print(f"\nStatistics:")
        print(f"  Total hits: {total_hits}")
        print(f"  Total at-bats: {total_at_bats}")
        print(f"  Total home runs: {total_homeruns}")
        print(f"  Total games played (all players): {total_games}")
        print(
            f"  Overall batting average: {round(total_hits / total_at_bats, 3) if total_at_bats > 0 else 'N/A'}"
        )

        # Upload to Supabase
        print("\nUploading to Supabase...")
        upload_batters_to_supabase(all_batters)
    else:
        print("No batters found to upload")


if __name__ == "__main__":
    main()
