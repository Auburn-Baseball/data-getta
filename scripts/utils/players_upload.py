from typing import Any, Dict, Mapping, Tuple, cast

import pandas as pd
from supabase import Client, create_client

from .common import SUPABASE_KEY, SUPABASE_URL, check_practice, check_supabase_vars
from .file_date import CSVFilenameParser

# Initialize Supabase client
check_supabase_vars()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)  # type: ignore[arg-type]


def get_players_from_buffer(buffer, filename: str) -> Dict[Tuple[str, str, int], Dict]:
    """Extract players from a CSV file using dict for deduplication"""
    try:
        df = pd.read_csv(buffer)

        # Determine if this is practice data by checking League column
        is_practice = check_practice(df)

        # Check if required columns exist
        if "Pitcher" not in df.columns and "Batter" not in df.columns:
            print(f"Warning: No Pitcher or Batter columns found in {filename}")
            return {}

        date_parser = CSVFilenameParser()
        key_date = date_parser.get_date_object(filename)
        if key_date is None:
            raise ValueError(f"Unable to parse game date from filename: {filename}")
        season_year = key_date.year

        players_dict: Dict[Tuple[str, str, int], Dict] = {}

        # Extract pitchers
        if all(col in df.columns for col in ["Pitcher", "PitcherId", "PitcherTeam"]):
            pitcher_data = df[["Pitcher", "PitcherId", "PitcherTeam"]].dropna()
            for _, row in pitcher_data.iterrows():
                pitcher_name = str(row["Pitcher"]).strip()
                pitcher_id = str(row["PitcherId"]).strip()
                pitcher_team = str(row["PitcherTeam"]).strip()
                # Convert different aub practice team to be consistent
                if is_practice and pitcher_team == "AUB_PRC":
                    pitcher_team = "AUB_TIG"
                else:
                    pitcher_team = str(pitcher_team).strip()

                if pitcher_name and pitcher_id and pitcher_team:
                    # Primary key tuple: (Name, TeamTrackmanAbbreviation, Year)
                    key = (pitcher_name, pitcher_team, season_year)

                    # No pitchers without IDs will exist yet, so no need to check for that
                    if key not in players_dict:
                        players_dict[key] = {
                            "Name": pitcher_name,
                            "PitcherId": pitcher_id,
                            "BatterId": None,
                            "TeamTrackmanAbbreviation": pitcher_team,
                            "Year": season_year,
                        }

        # Extract batters
        if all(col in df.columns for col in ["Batter", "BatterId", "BatterTeam"]):
            batter_data = df[["Batter", "BatterId", "BatterTeam"]].dropna()
            for _, row in batter_data.iterrows():
                batter_name = str(row["Batter"]).strip()
                batter_id = str(row["BatterId"]).strip()
                batter_team = str(row["BatterTeam"]).strip()
                # Convert different aub practice team to be consistent
                if is_practice and batter_team == "AUB_PRC":
                    batter_team = "AUB_TIG"
                else:
                    batter_team = str(batter_team).strip()

                if batter_name and batter_id and batter_team:
                    # Primary key tuple: (Name, TeamTrackmanAbbreviation, Year)
                    key = (batter_name, batter_team, season_year)

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
                            "Year": season_year,
                        }

        return players_dict

    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return {}


def upload_players_to_supabase(players_dict: Dict[Tuple[str, str, int], Dict], batch_size=1000):
    """Upload players to Supabase"""
    if not players_dict:
        print("No players to upload")
        return

    try:
        # Convert dictionary values to list for Supabase
        player_data = list(players_dict.values())

        print(f"Preparing to upload {len(player_data)} unique players...")

        # Insert data in batches to avoid request size limits
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
                if batch:
                    print(f"Batch Error: {batch_error}")
                    print(f"Sample record from failed batch: {batch[0]}")
                try:
                    print(result.data)
                except NameError:
                    pass
                continue

        print(f"Successfully processed {total_inserted} player records")

        # Get final count
        count_result = supabase.table("Players").select("BatterId, PitcherId").execute()

        player_rows = cast(list[Mapping[str, Any]], count_result.data)
        unique_players: set[tuple[str, str]] = set()
        for record in player_rows:
            batter_id = cast(str, record.get("BatterId"))
            pitcher_id = cast(str, record.get("PitcherId"))
            unique_players.add((batter_id, pitcher_id))
        total_players = len(unique_players)

        print(f"Total unique players in database: {total_players}")

    except Exception as e:
        print(f"Supabase error: {e}")
