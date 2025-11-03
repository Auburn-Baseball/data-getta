"""
Author: Joshua Henley
Created: 15 October 2025

Organizes functions and variables that
are used over multiple files into a
single common file.
"""

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
project_root = Path(__file__).parent.parent.parent
env = os.getenv("ENV", "development")
load_dotenv(project_root / f".env.{env}")

# Supabase configuration
SUPABASE_URL = os.getenv("VITE_SUPABASE_PROJECT_URL")
SUPABASE_KEY = os.getenv("VITE_SUPABASE_API_KEY")


# Initialize Supabase client
def check_supabase_vars():
    if SUPABASE_URL is None or SUPABASE_KEY is None:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")


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
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        return super(NumpyEncoder, self).default(obj)


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


def check_practice(df_buffer) -> bool:
    """Returns true if the data is practice data, false otherwise"""
    is_practice = False
    columns = df_buffer.columns
    if "League" in columns:
        league_values = df_buffer["League"].dropna().astype(str).str.strip().str.upper()
        is_practice = bool((league_values == "TEAM").any())
    return is_practice
