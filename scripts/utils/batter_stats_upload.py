import json
from typing import Dict, Tuple

import pandas as pd
from supabase import Client, create_client

from .common import SUPABASE_KEY, SUPABASE_URL, NumpyEncoder, is_in_strike_zone
from .file_date import CSVFilenameParser

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


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


def get_batter_stats_from_buffer(
    buffer, filename: str
) -> Dict[Tuple[str, str, int], Dict]:
    """Extract batter statistics from a CSV file in-memory"""
    try:
        df = pd.read_csv(buffer)

        # Determines if this is practice data by checking the League column
        is_practice = False
        if "League" in df.columns:
            league_values = df["League"].dropna().astype(str).str.strip().str.upper()
            is_practice = (league_values == "TEAM").any()
        # Get game date from filename
        date_parser = CSVFilenameParser()
        game_date_obj = date_parser.get_date_object(filename)
        if game_date_obj is None:
            raise ValueError(f"Unable to parse game date from filename: {filename}")
        game_date = str(game_date_obj)
        season_year = game_date_obj.year

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
            print(f"Warning: Missing required columns in {filename}")
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

            key = (batter_name, batter_team, season_year)

            # Calculate hits
            hits = len(group[group["PlayResult"].isin(["Single", "Double", "Triple", "HomeRun"])])

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

            # Calculate singles
            singles = len(group[group["PlayResult"] == "Single"])

            # Calculate doubles
            doubles = len(group[group["PlayResult"] == "Double"])

            # Calculate triples
            triples = len(group[group["PlayResult"] == "Triple"])

            # Calculate home runs
            homeruns = len(group[group["PlayResult"] == "HomeRun"])

            # Calculate extra base hits
            extra_base_hits = len(group[group["PlayResult"].isin(["Double", "Triple", "HomeRun"])])

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
                        float(row["PlateLocHeight"]) if pd.notna(row["PlateLocHeight"]) else None
                    )
                    side = float(row["PlateLocSide"]) if pd.notna(row["PlateLocSide"]) else None

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
            batting_average = hits / at_bats if at_bats > 0 else None

            on_base_percentage = (
                ((hits + walks + hit_by_pitch) / (at_bats + walks + hit_by_pitch + sacrifice))
                if (at_bats + walks + hit_by_pitch + sacrifice) > 0
                else None
            )

            slugging_percentage = total_bases / at_bats if at_bats > 0 else None

            onbase_plus_slugging = (
                ((on_base_percentage or 0) + (slugging_percentage or 0))
                if (on_base_percentage is not None and slugging_percentage is not None)
                else None
            )

            isolated_power = (
                (slugging_percentage or 0) - (batting_average or 0)
                if (slugging_percentage is not None and batting_average is not None)
                else None
            )

            k_percentage = strikeouts / plate_appearances if plate_appearances > 0 else None

            base_on_ball_percentage = walks / plate_appearances if plate_appearances > 0 else None

            chase_percentage = (
                out_of_zone_swings / out_of_zone_count if out_of_zone_count > 0 else None
            )

            in_zone_whiff_percentage = in_zone_whiffs / in_zone_count if in_zone_count > 0 else None

            # Get unique games from this file - store as a set for later merging
            unique_games = (
                set(group["GameUID"].dropna().unique()) if "GameUID" in group.columns else set()
            )

            # Calculate total exit velocity
            if "ExitSpeed" in group.columns:
                # Convert to numeric (in case it's read as string)
                group["ExitSpeed"] = pd.to_numeric(group["ExitSpeed"], errors="coerce")

                total_exit_velo = group[
                    (group["PitchCall"] == "InPlay") & (group["ExitSpeed"].notna())
                ]["ExitSpeed"].sum()

            else:
                total_exit_velo = 0

            batter_stats = {
                "Batter": batter_name,
                "BatterTeam": batter_team,
                "Date": game_date,
                "hits": hits,
                "at_bats": at_bats,
                "strikes": strikes,
                "walks": walks,
                "strikeouts": strikeouts,
                "singles": singles,
                "doubles": doubles,
                "triples": triples,
                "homeruns": homeruns,
                "extra_base_hits": extra_base_hits,
                "plate_appearances": plate_appearances,
                "hit_by_pitch": hit_by_pitch,
                "sacrifice": sacrifice,
                "total_bases": total_bases,
                "is_practice": is_practice,
                "total_exit_velo": round(total_exit_velo, 1),
                "is_practice": is_practice,
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
                "isolated_power": round(isolated_power, 3) if isolated_power is not None else None,
                "k_percentage": round(k_percentage, 3) if k_percentage is not None else None,
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
        print(f"Error reading {filename}: {e}")
        return {}


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
        batch_size = 1000
        total_inserted = 0

        for i in range(0, len(batter_data), batch_size):
            batch = batter_data[i : i + batch_size]

            try:
                # Use upsert to handle conflicts based on primary key
                result = (
                    supabase.table("BatterStats")
                    .upsert(batch, on_conflict="Batter,BatterTeam,Date")
                    .execute()
                )

                total_inserted += len(batch)
                print(f"Uploaded batch {i//batch_size + 1}: {len(batch)} records")

            except Exception as batch_error:
                print(f"Error uploading batch {i//batch_size + 1}: {batch_error}")
                # Print first record of failed batch for debugging
                if batch:
                    print(f"Sample record from failed batch: {batch[0]}")
                    print(result.data)
                continue

        print(f"Successfully processed {total_inserted} batter records")

        # Get final count
        count_result = supabase.table("BatterStats").select("*", count="exact").execute()

        total_batters = count_result.count
        print(f"Total batters in database: {total_batters}")

    except Exception as e:
        print(f"Supabase error: {e}")
