import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client
import re
from typing import Dict, Tuple, List
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


def get_players_from_buffer(buffer, filename: str) -> Dict[Tuple[str, str, int], Dict]:
    """Extract players from a CSV file using dict for deduplication"""
    try:
        df = pd.read_csv(buffer)

        # Check if required columns exist
        if "Pitcher" not in df.columns and "Batter" not in df.columns:
            print(f"Warning: No Pitcher or Batter columns found in {filename}")
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
        print(f"Error reading {filename}: {e}")
        return {}


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
                    supabase.table(f"Players")
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
            supabase.table(f"Players")
            .select("*", count="exact")
            .eq("Year", 2025)
            .execute()
        )
        total_players = count_result.count
        print(f"Total 2025 players in database: {total_players}")

    except Exception as e:
        print(f"Supabase error: {e}")
