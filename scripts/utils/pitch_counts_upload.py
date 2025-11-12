import json
from typing import Dict, Tuple

import pandas as pd
from postgrest.types import CountMethod
from supabase import Client, create_client

from .common import SUPABASE_KEY, SUPABASE_URL, NumpyEncoder, check_practice, check_supabase_vars
from .file_date import CSVFilenameParser

check_supabase_vars()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)  # type: ignore[arg-type]


def get_pitch_counts_from_buffer(buffer, filename: str) -> Dict[Tuple[str, str, int], Dict]:
    """Extract pitch count statistics from a CSV file"""
    try:
        df = pd.read_csv(buffer)

        # Determine if this is practice data by checking League column
        is_practice = check_practice(df)

        # Get game date from filename
        date_parser = CSVFilenameParser()
        game_date_obj = date_parser.get_date_object(filename)
        if game_date_obj is None:
            raise ValueError(f"Unable to parse game date from filename: {filename}")
        game_date = str(game_date_obj)
        season_year = game_date_obj.year

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
            pitcher_name = str(pitcher_name).strip()

            # Convert different aub practice team to be consistent
            if is_practice and pitcher_team == "AUB_PRC":
                pitcher_team = "AUB_TIG"
            else:
                pitcher_team = str(pitcher_team).strip()

            key = (pitcher_name, pitcher_team, season_year)

            # Count total pitches
            total_pitches = len(group)

            # Initialize counts
            curveball_count = 0
            fourseam_count = 0
            sinker_count = 0
            slider_count = 0
            changeup_count = 0
            cutter_count = 0
            splitter_count = 0
            twoseam_count = 0
            other_count = 0

            # Standardize NaN / empty values
            auto_pitch = group["AutoPitchType"].fillna("").astype(str).str.strip()
            tagged_pitch = group["TaggedPitchType"].fillna("").astype(str).str.strip()

            for a_pt, t_pt in zip(auto_pitch, tagged_pitch):
                # Normalize both to handle missing/empty
                a_pt = a_pt if a_pt else ""
                t_pt = t_pt if t_pt else ""

                # Classification logic
                if a_pt == "Two-Seam" or t_pt == "Two-Seam":
                    twoseam_count += 1
                elif a_pt == "Four-Seam" or (t_pt == "Fastball" and a_pt == ""):
                    fourseam_count += 1
                elif a_pt == "Curveball" or t_pt == "Curveball":
                    curveball_count += 1
                elif a_pt == "Slider" or t_pt == "Slider":
                    slider_count += 1
                elif a_pt == "Changeup" or t_pt == "Changeup":
                    changeup_count += 1
                elif a_pt == "Cutter" or t_pt == "Cutter":
                    cutter_count += 1
                elif a_pt == "Splitter" or t_pt == "Splitter":
                    splitter_count += 1
                elif a_pt == "Sinker" or t_pt == "Sinker":
                    sinker_count += 1
                else:
                    other_count += 1

            # Get unique games from this file - store as a set for later merging
            unique_games = (
                set(group["GameUID"].dropna().unique()) if "GameUID" in group.columns else set()
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


def upload_pitches_to_supabase(pitchers_dict: Dict[Tuple[str, str, int], Dict], batch_size=1000):
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
        total_inserted = 0

        for i in range(0, len(pitch_data), batch_size):
            batch = pitch_data[i : i + batch_size]

            try:
                # Use upsert to handle conflicts based on primary key
                result = (
                    supabase.table("PitchCounts")
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
                try:
                    print(result.data)
                except NameError:
                    pass

                continue

        print(f"Successfully processed {total_inserted} pitch count records")

        # Get final count
        count_result = supabase.table("PitchCounts").select("*", count=CountMethod.exact).execute()
        total_pitchers = count_result.count
        print(f"Total pitcher pitch counts in database: {total_pitchers}")

    except Exception as e:
        print(f"Supabase error: {e}")
