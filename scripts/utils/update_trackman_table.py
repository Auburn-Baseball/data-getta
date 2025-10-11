import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client
import json
import numpy as np
from typing import Dict, Any
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


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for NumPy types"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def get_trackman_data_from_buffer(buffer, filename: str) -> Dict[str, Dict[str, Any]]:
    """Extract TrackMan data from a CSV file in-memory and return as Dict[PitchUID, Dict]"""
    try:
        df = pd.read_csv(buffer)

        # Define types according to TrackmanData schema
        column_types = {
            "PitchUID": str,
            "PitchNo": int,
            "GameDate": str,
            "Pitcher": str,
            "PitcherId": int,
            "PitcherThrows": str,
            "PitcherTeam": str,
            "Batter": str,
            "BatterId": int,
            "BatterSide": str,
            "BatterTeam": str,
            "Inning": int,
            "Outs": int,
            "Balls": int,
            "Strikes": int,
            "TaggedPitchType": str,
            "PitchCall": str,
            "KorBB": str,
            "TaggedHitType": str,
            "PlayResult": str,
            "OutsOnPlay": int,
            "RunsScored": int,
            "RelSpeed": float,
            "VertRelAngle": float,
            "HorzRelAngle": float,
            "SpinRate": float,
            "RelHeight": float,
            "RelSide": float,
            "Extension": float,
            "VertBreak": float,
            "HorzBreak": float,
            "PlateLocHeight": float,
            "PlateLocSide": float,
            "ZoneSpeed": float,
            "VertApprAngle": float,
            "HorzApprAngle": float,
            "ZoneTime": float,
            "ExitSpeed": float,
            "Angle": float,
            "Direction": float,
            "HitSpinRate": float,
            "Distance": float,
            "LastTracked": float,
            "Bearing": float,
            "HangTime": float,
            "HomeTeam": str,
            "AwayTeam": str,
            "Stadium": str,
            "Level": str,
            "League": str,
            "GameID": str,
            "MaxHeight": float,
            "ContactPositionX": float,
            "ContactPositionY": float,
            "ContactPositionZ": float,
            "AutoHitType": str,
            "HomeTeamForeignID": int,
            "AwayTeamForeignID": int,
            "GameType": str
        }

        # Keep only columns that exist in CSV
        df = df[[col for col in column_types.keys() if col in df.columns]]

        # Apply type conversion
        for col, dtype in column_types.items():
            if col in df.columns:
                try:
                    df[col] = df[col].astype(dtype)
                except Exception:
                    if dtype in [int, float]:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    else:
                        df[col] = df[col].astype(str)

        # Replace NaNs with None
        df = df.where(pd.notnull(df), None)

        # Calculate GameType based on League
        if "League" in df.columns:
            df["GameType"] = df["League"].apply(lambda x: "Practice" if x == "Team" else "Regular")



        # Build dict using PitchUID as key
        result: Dict[str, Dict[str, Any]] = {}
        for _, row in df.iterrows():
            try:
                pitch_uid = str(row["PitchUID"])
                value = row.to_dict()
                value.pop("PitchUID", None)
                result[pitch_uid] = value
            except Exception as e:
                print(f"Skipping row due to error: {e}")

        return result

    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return {}


def clean_row_for_json(row_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Replace NaN, inf, -inf, 'nan' strings with None and convert ID fields to int."""
    clean = {}
    id_fields = {"PitcherId", "BatterId", "HomeTeamForeignID", "AwayTeamForeignID", "PitchNo", "Inning", "Outs", "Balls", "Strikes", "OutsOnPlay", "RunsScored"}
    
    for k, v in row_dict.items():
        if v is None:
            clean[k] = None
            continue
        
        # Handle floats that are actually integers
        if k in id_fields:
            try:
                clean[k] = int(v)
            except (ValueError, TypeError):
                clean[k] = None
            continue
        
        if isinstance(v, float):
            if pd.isna(v) or v in [float('inf'), float('-inf')]:
                clean[k] = None
            else:
                clean[k] = v
        elif isinstance(v, str):
            if v.lower() == 'nan':
                clean[k] = None
            else:
                clean[k] = v
        else:
            clean[k] = v

    return clean



def upload_trackman_to_supabase(trackman_data):
    """Upload TrackMan data to Supabase safely, handling NumPy types and NaNs."""
    # Convert dict to DataFrame if necessary
    if isinstance(trackman_data, dict):
        if not trackman_data:
            print("No TrackMan data to upload")
            return

        records = []
        for pitch_uid, data in trackman_data.items():
            record = {'PitchUID': pitch_uid}
            record.update(data)
            records.append(record)
        trackman_df = pd.DataFrame(records)
    else:
        trackman_df = trackman_data

    if trackman_df.empty:
        print("No TrackMan data to upload")
        return

    # Clean all rows for JSON serialization
    trackman_records = [
        clean_row_for_json(row.to_dict())
        for _, row in trackman_df.iterrows()
    ]

    print(f"Prepared {len(trackman_records)} records for upload")

    # Batch upsert
    batch_size = 1000
    total_inserted = 0
    for i in range(0, len(trackman_records), batch_size):
        batch = trackman_records[i : i + batch_size]
        try:
            supabase.table("TrackmanData").upsert(batch, on_conflict="PitchUID").execute()
            total_inserted += len(batch)
            print(f"Uploaded batch {i // batch_size + 1}: {len(batch)} records")
        except Exception as e:
            print(f"Error uploading batch {i // batch_size + 1}: {e}")
            if batch:
                print(f"Sample record from failed batch: {batch[0]}")
            continue

    print(f"Successfully processed {total_inserted} TrackMan records")
