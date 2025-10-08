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
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        return super(NumpyEncoder, self).default(obj)


def get_advanced_batting_stats_from_buffer(buffer, filename: str) -> Dict[Tuple[str, str, int], Dict]:
    """Extract advanced batting statistics from a CSV file in-memory"""
    try:
        df = pd.read_csv(buffer)

        # Check if required columns exist
        required_columns = [
            "Batter",
            "BatterTeam",
            "KorBB",
            "PitchCall",
            "ExitSpeed",
        ]
        if not all(col in df.columns for col in required_columns):
            print(f"Warning: Missing required columns in {filename}")
            return {}

        # Extract year from filename
        file_date_parser = CSVFilenameParser()
        date_components = file_date_parser.get_date_components(filename)
        if not date_components:
            print(f"Warning: Could not extract date from filename {filename}, defaulting to 2025")
            year = 2025
        else:
            year = date_components[0]  # year is the first component

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

            key = (batter_name, batter_team, year)

            # Calculate plate appearances
            plate_appearances = len(
                group[
                    group["KorBB"].isin(["Walk", "Strikeout"])
                    | group["PitchCall"].isin(["InPlay", "HitByPitch"])
                ]
            )

            # Calculate batted balls (balls in play with exit speed)
            batted_balls = group[
                (group["PitchCall"] == "InPlay") &
                (group["ExitSpeed"].notna())
            ].shape[0]

            # Calculate total exit velocity for average
            total_exit_velo = group[
                (group["PitchCall"] == "InPlay") &
                (group["ExitSpeed"].notna())
            ]["ExitSpeed"].sum()

            # Calculate average exit velocity
            avg_exit_velo = total_exit_velo / batted_balls if batted_balls > 0 else None

            # Calculate walks
            walks = len(group[group["KorBB"] == "Walk"])

            # Calculate strikeouts
            strikeouts = len(group[group["KorBB"] == "Strikeout"])

            # Calculate percentages
            k_percentage = (
                strikeouts / plate_appearances if plate_appearances > 0 else None
            )

            bb_percentage = (
                walks / plate_appearances if plate_appearances > 0 else None
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
                "Year": year,
                "plate_app": plate_appearances,
                "batted_balls": batted_balls,
                "avg_exit_velo": round(avg_exit_velo, 1) if avg_exit_velo is not None else None,
                "k_per": round(k_percentage, 3) if k_percentage is not None else None,
                "bb_per": round(bb_percentage, 3) if bb_percentage is not None else None,
                "unique_games": unique_games,  # Store the set of unique games
                "games": len(unique_games),  # This will be recalculated later
            }

            batters_dict[key] = batter_stats

        return batters_dict

    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return {}


def get_existing_advanced_batting_stats(batter_name: str, batter_team: str, year: int) -> Dict:
    """Get existing advanced batting stats for a player from Supabase"""
    try:
        result = (
            supabase.table("AdvancedBattingStats")
            .select("*")
            .eq("Batter", batter_name)
            .eq("BatterTeam", batter_team)
            .eq("Year", year)
            .execute()
        )
        
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"Error fetching existing stats for {batter_name}: {e}")
        return None


def combine_advanced_batting_stats(existing_stats: Dict, new_stats: Dict) -> Dict:
    """Combine existing and new advanced batting stats"""
    if not existing_stats:
        return new_stats
    
    # Combine plate appearances
    combined_plate_app = existing_stats.get("plate_app", 0) + new_stats.get("plate_app", 0)
    
    # Combine batted balls
    combined_batted_balls = existing_stats.get("batted_balls", 0) + new_stats.get("batted_balls", 0)
    
    # Calculate combined average exit velocity
    existing_total_exit_velo = (existing_stats.get("avg_exit_velo", 0) or 0) * (existing_stats.get("batted_balls", 0) or 0)
    new_total_exit_velo = (new_stats.get("avg_exit_velo", 0) or 0) * (new_stats.get("batted_balls", 0) or 0)
    
    combined_avg_exit_velo = None
    if combined_batted_balls > 0:
        total_exit_velo = existing_total_exit_velo + new_total_exit_velo
        combined_avg_exit_velo = total_exit_velo / combined_batted_balls
    
    # Calculate combined K% and BB%
    existing_strikeouts = (existing_stats.get("k_per", 0) or 0) * (existing_stats.get("plate_app", 0) or 0)
    new_strikeouts = (new_stats.get("k_per", 0) or 0) * (new_stats.get("plate_app", 0) or 0)
    combined_k_per = (existing_strikeouts + new_strikeouts) / combined_plate_app if combined_plate_app > 0 else None
    
    existing_walks = (existing_stats.get("bb_per", 0) or 0) * (existing_stats.get("plate_app", 0) or 0)
    new_walks = (new_stats.get("bb_per", 0) or 0) * (new_stats.get("plate_app", 0) or 0)
    combined_bb_per = (existing_walks + new_walks) / combined_plate_app if combined_plate_app > 0 else None
    
    # Combine unique games
    existing_games = set(existing_stats.get("unique_games", [])) if existing_stats.get("unique_games") else set()
    new_games = new_stats.get("unique_games", set())
    combined_games = existing_games.union(new_games)
    
    return {
        "Batter": new_stats["Batter"],
        "BatterTeam": new_stats["BatterTeam"],
        "Year": new_stats["Year"],
        "plate_app": combined_plate_app,
        "batted_balls": combined_batted_balls,
        "avg_exit_velo": round(combined_avg_exit_velo, 1) if combined_avg_exit_velo is not None else None,
        "k_per": round(combined_k_per, 3) if combined_k_per is not None else None,
        "bb_per": round(combined_bb_per, 3) if combined_bb_per is not None else None,
        "unique_games": list(combined_games),
        "games": len(combined_games),
    }


def upload_advanced_batting_to_supabase(batters_dict: Dict[Tuple[str, str, int], Dict]):
    """Upload advanced batting statistics to Supabase with proper upsert logic"""
    if not batters_dict:
        print("No advanced batting stats to upload")
        return

    try:
        # Process each batter individually to handle existing records
        for key, new_stats in batters_dict.items():
            batter_name, batter_team, year = key
            
            # Get existing stats
            existing_stats = get_existing_advanced_batting_stats(batter_name, batter_team, year)
            
            # Combine stats if existing record found
            if existing_stats:
                combined_stats = combine_advanced_batting_stats(existing_stats, new_stats)
                print(f"Updating existing record for {batter_name} ({batter_team})")
            else:
                combined_stats = new_stats
                print(f"Creating new record for {batter_name} ({batter_team})")
            
            # Remove unique_games from the data before uploading
            clean_stats = {k: v for k, v in combined_stats.items() if k != "unique_games"}
            
            # Convert to JSON and back to ensure all numpy types are converted
            json_str = json.dumps(clean_stats, cls=NumpyEncoder)
            clean_batter = json.loads(json_str)
            
            try:
                # Use upsert to handle conflicts based on primary key
                result = (
                    supabase.table("AdvancedBattingStats")
                    .upsert(clean_batter, on_conflict="Batter,BatterTeam,Year")
                    .execute()
                )
                print(f"Successfully processed {batter_name} ({batter_team})")
                
            except Exception as upload_error:
                print(f"Error uploading {batter_name} ({batter_team}): {upload_error}")
                continue

        print(f"Successfully processed {len(batters_dict)} advanced batting records")

        # Get final count for the year being processed
        # Note: This will show count for the most recent year processed
        # For a more accurate count, you might want to pass the year as a parameter
        count_result = (
            supabase.table("AdvancedBattingStats")
            .select("*", count="exact")
            .execute()
        )

        total_batters = count_result.count
        print(f"Total advanced batting records in database: {total_batters}")

    except Exception as e:
        print(f"Supabase error: {e}")


if __name__ == "__main__":
    # This script is designed to be imported and used by other scripts
    # The main processing logic should be called from the main data processing script
    print("Advanced Batting Stats utility module loaded")
