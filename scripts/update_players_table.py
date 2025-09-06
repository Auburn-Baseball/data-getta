import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client
import re
from typing import Dict, Tuple, List
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


def should_exclude_file(filename: str) -> bool:
    """Check if file should be excluded based on name patterns"""
    exclude_patterns = ["playerpositioning", "fhc", "unverified"]
    filename_lower = filename.lower()
    return any(pattern in filename_lower for pattern in exclude_patterns)


def get_players_from_csv(file_path: str) -> Dict[Tuple[str, str, int], Dict]:
    """Extract players from a CSV file using dict for deduplication"""
    try:
        df = pd.read_csv(file_path)

        # Check if required columns exist
        if "Pitcher" not in df.columns and "Batter" not in df.columns:
            print(f"Warning: No Pitcher or Batter columns found in {file_path}")
            return {}

        players_dict = {}

        # Extract pitchers
        if all(col in df.columns for col in ["Pitcher", "PitcherId", "PitcherTeam"]):
            pitcher_data = df[["Pitcher", "PitcherId", "PitcherTeam"]].dropna()
            for _, row in pitcher_data.iterrows():
                pitcher_name = str(row["Pitcher"]).strip()
                pitcher_id = str(row["PitcherId"]).strip()
                pitcher_team = str(row["PitcherTeam"]).strip()

                if pitcher_name and pitcher_id and pitcher_team:
                    # Primary key tuple: (Name, TeamTrackmanAbbreviation, Year)
                    key = (pitcher_name, pitcher_team, 2025)

                    # If player already exists, update IDs if not already set
                    if key in players_dict:
                        if not players_dict[key]["PitcherId"]:
                            players_dict[key]["PitcherId"] = pitcher_id
                    else:
                        players_dict[key] = {
                            "Name": pitcher_name,
                            "PitcherId": pitcher_id,
                            "BatterId": None,
                            "TeamTrackmanAbbreviation": pitcher_team,
                            "Year": 2025,
                        }

        # Extract batters
        if all(col in df.columns for col in ["Batter", "BatterId", "BatterTeam"]):
            batter_data = df[["Batter", "BatterId", "BatterTeam"]].dropna()
            for _, row in batter_data.iterrows():
                batter_name = str(row["Batter"]).strip()
                batter_id = str(row["BatterId"]).strip()
                batter_team = str(row["BatterTeam"]).strip()

                if batter_name and batter_id and batter_team:
                    # Primary key tuple: (Name, TeamTrackmanAbbreviation, Year)
                    key = (batter_name, batter_team, 2025)

                    # If player already exists, update IDs if not already set
                    if key in players_dict:
                        if not players_dict[key]["BatterId"]:
                            players_dict[key]["BatterId"] = batter_id
                    else:
                        players_dict[key] = {
                            "Name": batter_name,
                            "PitcherId": None,
                            "BatterId": batter_id,
                            "TeamTrackmanAbbreviation": batter_team,
                            "Year": 2025,
                        }

        return players_dict

    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {}


def process_csv_folder(csv_folder_path: str) -> Dict[Tuple[str, str, int], Dict]:
    """Process all 2025 CSV files in the folder"""
    all_players = {}

    # Look in the 2025 subfolder
    year_folder = os.path.join(csv_folder_path, "2025")

    if not os.path.exists(year_folder):
        print(f"2025 CSV folder not found: {year_folder}")
        return all_players

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

        players_from_file = get_players_from_csv(file_path)

        # Merge players from this file with the main dictionary
        for key, player_data in players_from_file.items():
            if key in all_players:
                # Player already exists, merge the IDs if they're not already set
                if not all_players[key]["PitcherId"] and player_data["PitcherId"]:
                    all_players[key]["PitcherId"] = player_data["PitcherId"]
                if not all_players[key]["BatterId"] and player_data["BatterId"]:
                    all_players[key]["BatterId"] = player_data["BatterId"]
            else:
                # New player, add to dictionary
                all_players[key] = player_data

        print(f"  Found {len(players_from_file)} unique players in this file")
        print(f"  Total unique players so far: {len(all_players)}")

    return all_players


def upload_players_to_supabase(players_dict: Dict[Tuple[str, str, int], Dict]):
    """Upload players to Supabase"""
    if not players_dict:
        print("No players to upload")
        return

    try:
        # Convert dictionary values to list for Supabase
        player_data = list(players_dict.values())

        print(f"Preparing to upload {len(player_data)} unique players...")

        # Insert data in batches to avoid request size limits
        batch_size = 100
        total_inserted = 0

        for i in range(0, len(player_data), batch_size):
            batch = player_data[i : i + batch_size]

            try:
                # Use upsert to handle conflicts based on primary key
                result = (
                    supabase.table("Players")
                    .upsert(batch, on_conflict="Name,TeamTrackmanAbbreviation,Year")
                    .execute()
                )

                total_inserted += len(batch)
                print(f"Uploaded batch {i//batch_size + 1}: {len(batch)} records")

            except Exception as batch_error:
                print(f"Error uploading batch {i//batch_size + 1}: {batch_error}")
                continue

        print(f"Successfully processed {total_inserted} player records")

        # Get final count
        count_result = (
            supabase.table("Players")
            .select("*", count="exact")
            .eq("Year", 2025)
            .execute()
        )
        total_players = count_result.count
        print(f"Total 2025 players in database: {total_players}")

    except Exception as e:
        print(f"Supabase error: {e}")


def main():
    print("Starting CSV processing...")

    # Set the path to your CSV folder
    csv_folder_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "csv")
    print(f"Looking for CSV files in: {csv_folder_path}")

    # Process all CSV files and collect unique players
    all_players = process_csv_folder(csv_folder_path)

    print(f"\nTotal unique players found: {len(all_players)}")

    # Show sample of players found
    if all_players:
        print("\nSample players:")
        for i, (key, player) in enumerate(list(all_players.items())[:10]):
            name, team, year = key
            print(
                f"  {player['Name']} - Team: {player['TeamTrackmanAbbreviation']}, "
                f"PitcherID: {player['PitcherId']}, BatterID: {player['BatterId']}"
            )
            if i >= 4:  # Show first 5
                break

        # Show some statistics
        pitchers_count = sum(1 for p in all_players.values() if p["PitcherId"])
        batters_count = sum(1 for p in all_players.values() if p["BatterId"])
        both_count = sum(
            1 for p in all_players.values() if p["PitcherId"] and p["BatterId"]
        )

        print(f"\nStatistics:")
        print(f"  Players with PitcherID: {pitchers_count}")
        print(f"  Players with BatterID: {batters_count}")
        print(f"  Players with both IDs: {both_count}")

        # Upload to Supabase
        print("\nUploading to Supabase...")
        upload_players_to_supabase(all_players)
    else:
        print("No players found to upload")


if __name__ == "__main__":
    main()
