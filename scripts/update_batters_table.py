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


def format_stat(value: float) -> str:
    """Format a stat as a string with exactly 3 decimal places"""
    return f"{value:.3f}"


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
        grouped = df.groupby(["Batter", "BatterTeam"])

        for (batter_name, batter_team), group in grouped:
            if pd.isna(batter_name) or pd.isna(batter_team):
                continue

            batter_name = str(batter_name).strip()
            batter_team = str(batter_team).strip()
            if not batter_name or not batter_team:
                continue

            key = (batter_name, batter_team, 2025)

            hits = len(group[group["PlayResult"].isin(["Single", "Double", "Triple", "HomeRun"])])
            at_bats = len(group[
                group["PlayResult"].isin(["Error", "Out", "FieldersChoice", "Single", "Double", "Triple", "HomeRun"])
                | (group["KorBB"] == "Strikeout")
            ])
            strikes = len(group[group["PitchCall"].isin(["StrikeCalled", "StrikeSwinging", "FoulBallNotFieldable"])])
            walks = len(group[group["KorBB"] == "Walk"])
            strikeouts = len(group[group["KorBB"] == "Strikeout"])
            homeruns = len(group[group["PlayResult"] == "HomeRun"])
            extra_base_hits = len(group[group["PlayResult"].isin(["Double", "Triple", "HomeRun"])])
            plate_appearances = len(group[
                group["KorBB"].isin(["Walk", "Strikeout"])
                | group["PitchCall"].isin(["InPlay", "HitByPitch"])
            ])
            hit_by_pitch = len(group[group["PitchCall"] == "HitByPitch"])
            sacrifice = len(group[group["PlayResult"] == "Sacrifice"])
            total_bases = group["PlayResult"].apply(calculate_total_bases).sum()

            # Zone stats
            in_zone_count = 0
            out_of_zone_count = 0
            in_zone_whiffs = 0
            out_of_zone_swings = 0

            for _, row in group.iterrows():
                try:
                    height = float(row["PlateLocHeight"]) if pd.notna(row["PlateLocHeight"]) else None
                    side = float(row["PlateLocSide"]) if pd.notna(row["PlateLocSide"]) else None
                    if height is not None and side is not None:
                        if is_in_strike_zone(height, side):
                            in_zone_count += 1
                            if row["PitchCall"] == "StrikeSwinging":
                                in_zone_whiffs += 1
                        else:
                            out_of_zone_count += 1
                            if row["PitchCall"] in ["StrikeSwinging", "FoulBallNotFieldable", "InPlay"]:
                                out_of_zone_swings += 1
                except (ValueError, TypeError):
                    continue

            # Format stats to always 3 decimal places
            batting_average = format_stat(hits / at_bats) if at_bats > 0 else "0.000"
            on_base_percentage = format_stat(
                (hits + walks + hit_by_pitch) / (at_bats + walks + hit_by_pitch + sacrifice)
            ) if (at_bats + walks + hit_by_pitch + sacrifice) > 0 else "0.000"
            slugging_percentage = format_stat(total_bases / at_bats) if at_bats > 0 else "0.000"
            onbase_plus_slugging = format_stat(float(on_base_percentage) + float(slugging_percentage))
            isolated_power = format_stat(float(slugging_percentage) - float(batting_average))
            k_percentage = round(strikeouts / plate_appearances, 3) if plate_appearances > 0 else None
            base_on_ball_percentage = round(walks / plate_appearances, 3) if plate_appearances > 0 else None
            chase_percentage = round(out_of_zone_swings / out_of_zone_count, 3) if out_of_zone_count > 0 else None
            in_zone_whiff_percentage = round(in_zone_whiffs / in_zone_count, 3) if in_zone_count > 0 else None

            unique_games = set(group["GameUID"].dropna().unique()) if "GameUID" in group.columns else set()

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
                "batting_average": batting_average,
                "on_base_percentage": on_base_percentage,
                "slugging_percentage": slugging_percentage,
                "onbase_plus_slugging": onbase_plus_slugging,
                "isolated_power": isolated_power,
                "k_percentage": k_percentage,
                "base_on_ball_percentage": base_on_ball_percentage,
                "chase_percentage": chase_percentage,
                "in_zone_whiff_percentage": in_zone_whiff_percentage,
                "unique_games": unique_games,
                "games": len(unique_games),
            }

            batters_dict[key] = batter_stats

        return batters_dict

    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {}


def process_csv_folder(csv_folder_path: str) -> Dict[Tuple[str, str, int], Dict]:
    """Process all 2025 CSV files in the folder"""
    all_batters = {}
    year_folder = os.path.join(csv_folder_path, "2025")

    if not os.path.exists(year_folder):
        print(f"2025 CSV folder not found: {year_folder}")
        return all_batters

    csv_files = [f for f in os.listdir(year_folder) if f.endswith(".csv")]
    filtered_files = [f for f in csv_files if not should_exclude_file(f)]

    print(f"Found {len(filtered_files)} 2025 CSV files to process")

    for filename in filtered_files:
        file_path = os.path.join(year_folder, filename)
        print(f"Processing: {filename}")
        batters_from_file = get_batter_stats_from_csv(file_path)

        for key, batter_data in batters_from_file.items():
            if key in all_batters:
                existing = all_batters[key]
                for stat in [
                    "hits", "at_bats", "strikes", "walks", "strikeouts",
                    "homeruns", "extra_base_hits", "plate_appearances",
                    "hit_by_pitch", "sacrifice", "total_bases"
                ]:
                    existing[stat] += batter_data[stat]

                existing["unique_games"].update(batter_data["unique_games"])
                existing["games"] = len(existing["unique_games"])

                # Recalculate formatted stats
                existing["batting_average"] = format_stat(existing["hits"] / existing["at_bats"]) if existing["at_bats"] > 0 else "0.000"
                existing["on_base_percentage"] = format_stat(
                    (existing["hits"] + existing["walks"] + existing["hit_by_pitch"]) /
                    (existing["at_bats"] + existing["walks"] + existing["hit_by_pitch"] + existing["sacrifice"])
                ) if (existing["at_bats"] + existing["walks"] + existing["hit_by_pitch"] + existing["sacrifice"]) > 0 else "0.000"
                existing["slugging_percentage"] = format_stat(existing["total_bases"] / existing["at_bats"]) if existing["at_bats"] > 0 else "0.000"
                existing["onbase_plus_slugging"] = format_stat(float(existing["on_base_percentage"]) + float(existing["slugging_percentage"]))
                existing["isolated_power"] = format_stat(float(existing["slugging_percentage"]) - float(existing["batting_average"]))
                existing["k_percentage"] = round(existing["strikeouts"] / existing["plate_appearances"], 3) if existing["plate_appearances"] > 0 else None
                existing["base_on_ball_percentage"] = round(existing["walks"] / existing["plate_appearances"], 3) if existing["plate_appearances"] > 0 else None
            else:
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
        batter_data = []
        for batter_dict in batters_dict.values():
            clean_dict = {k: v for k, v in batter_dict.items() if k != "unique_games"}
            json_str = json.dumps(clean_dict, cls=NumpyEncoder)
            clean_batter = json.loads(json_str)
            batter_data.append(clean_batter)

        print(f"Preparing to upload {len(batter_data)} unique batters...")
        batch_size = 100
        total_inserted = 0

        for i in range(0, len(batter_data), batch_size):
            batch = batter_data[i : i + batch_size]
            try:
                supabase.table("BatterStats").upsert(batch, on_conflict="Batter,BatterTeam,Year").execute()
                total_inserted += len(batch)
                print(f"Uploaded batch {i//batch_size + 1}: {len(batch)} records")
            except Exception as batch_error:
                print(f"Error uploading batch {i//batch_size + 1}: {batch_error}")
                if batch:
                    print(f"Sample record from failed batch: {batch[0]}")
                continue

        print(f"Successfully processed {total_inserted} batter records")
        count_result = supabase.table("BatterStats").select("*", count="exact").eq("Year", 2025).execute()
        total_batters = count_result.count
        print(f"Total 2025 batters in database: {total_batters}")

    except Exception as e:
        print(f"Supabase error: {e}")


def main():
    print("Starting batter statistics CSV processing...")
    csv_folder_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "csv")
    print(f"Looking for CSV files in: {csv_folder_path}")
    all_batters = process_csv_folder(csv_folder_path)
    print(f"\nTotal unique batters found: {len(all_batters)}")

    if all_batters:
        print("\nSample batters:")
        for i, (key, batter) in enumerate(list(all_batters.items())[:5]):
            name, team, year = key
            print(
                f"  {batter['Batter']} - Team: {batter['BatterTeam']}, "
                f"AVG: {batter['batting_average']}, HR: {batter['homeruns']}, Games: {batter['games']}"
            )

        total_hits = sum(b["hits"] for b in all_batters.values())
        total_at_bats = sum(b["at_bats"] for b in all_batters.values())
        total_homeruns = sum(b["homeruns"] for b in all_batters.values())
        total_games = sum(b["games"] for b in all_batters.values())

        print(f"\nStatistics:")
        print(f"  Total hits: {total_hits}")
        print(f"  Total at-bats: {total_at_bats}")
        print(f"  Total home runs: {total_homeruns}")
        print(f"  Total games played (all players): {total_games}")
        print(f"  Overall batting average: {format_stat(total_hits / total_at_bats) if total_at_bats > 0 else '0.000'}")

        print("\nUploading to Supabase...")
        upload_batters_to_supabase(all_batters)
    else:
        print("No batters found to upload")


if __name__ == "__main__":
    main()
