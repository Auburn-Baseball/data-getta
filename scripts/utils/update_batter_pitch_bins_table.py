"""Aggregate batter heat-map bins and upsert into Supabase."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from supabase import Client, create_client
from .file_date import CSVFilenameParser

# ---------------------------------------------------------------------------
# Environment / Supabase
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV = os.getenv("ENV", "development")
load_dotenv(PROJECT_ROOT / f".env.{ENV}")

SUPABASE_URL = os.getenv("VITE_SUPABASE_PROJECT_URL")
SUPABASE_KEY = os.getenv("VITE_SUPABASE_API_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("VITE_SUPABASE_PROJECT_URL and VITE_SUPABASE_API_KEY must be set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------------------------------------------------------
# Strike-zone geometry (matches UI + pitcher script)
# ---------------------------------------------------------------------------
ZONE_VERSION = "fixed_v3"
Z_X_HALF = 0.83
Z_Y_BOT = 1.50
Z_Y_TOP = 3.50
SPLITS = 3
X_EDGES = np.linspace(-Z_X_HALF, +Z_X_HALF, SPLITS + 1)
Y_EDGES = np.linspace(Z_Y_BOT, Z_Y_TOP, SPLITS + 1)
MID_X = 0.0
MID_Y = float((Z_Y_BOT + Z_Y_TOP) / 2.0)
OUTER = {"OTL": 10, "OTR": 11, "OBL": 12, "OBR": 13}

# Outcome buckets
SWING_PITCH_CALLS = {
    "StrikeSwinging",
    "StrikeSwingingBlocked",
    "FoulBall",
    "FoulBallNotFieldable",
    "FoulBallFieldable",
    "FoulTip",
    "InPlay",
}
HIT_RESULTS = {"Single", "Double", "Triple", "HomeRun"}

PITCH_KEYS = [
    "FourSeam",
    "Sinker",
    "Slider",
    "Curveball",
    "Changeup",
    "Cutter",
    "Splitter",
    "Other",
]

COUNT_COLUMNS = [f"Count_{k}" for k in PITCH_KEYS]
SWING_COLUMNS = [f"SwingCount_{k}" for k in PITCH_KEYS]
HIT_COLUMNS = [f"HitCount_{k}" for k in PITCH_KEYS]
ALL_TRACKED_COLUMNS = [
    "TotalPitchCount",
    "TotalSwingCount",
    "TotalHitCount",
    *COUNT_COLUMNS,
    *SWING_COLUMNS,
    *HIT_COLUMNS,
]

BinKey = Tuple[str, str, str, int]  # BatterTeam, Date, Batter, ZoneId


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        if pd.isna(obj):
            return None
        return super().default(obj)


def norm_pitch_type(value: str) -> str:
    if not isinstance(value, str):
        return "Other"
    t = value.strip().lower()
    if t in {"four-seam", "four seam", "fourseam", "4-seam", "ff", "fastball", "fb"}:
        return "FourSeam"
    if t in {"sinker", "two-seam", "two seam", "2-seam", "si"}:
        return "Sinker"
    if t in {"slider", "sl"}:
        return "Slider"
    if t in {"curveball", "curve", "cu", "knuckle curve", "kc"}:
        return "Curveball"
    if t in {"changeup", "change", "ch"}:
        return "Changeup"
    if t in {"cutter", "fc"}:
        return "Cutter"
    if t in {"splitter", "split-finger", "split finger", "fs", "forkball"}:
        return "Splitter"
    return "Other"


def classify_zone(x: float, y: float) -> Dict[str, object]:
    in_x = -Z_X_HALF <= x <= Z_X_HALF
    in_y = Z_Y_BOT <= y <= Z_Y_TOP
    if in_x and in_y:
        col = int(np.digitize([x], X_EDGES, right=False)[0])
        row = int(np.digitize([y], Y_EDGES, right=False)[0])
        col = max(1, min(SPLITS, col))
        row = max(1, min(SPLITS, row))
        cell = (row - 1) * SPLITS + col
        return {
            "ZoneId": cell,
            "InZone": True,
            "ZoneRow": row,
            "ZoneCol": col,
            "ZoneCell": cell,
            "OuterLabel": "NA",
        }

    if y > MID_Y:
        label = "OTL" if x < MID_X else "OTR"
    else:
        label = "OBL" if x < MID_X else "OBR"
    return {
        "ZoneId": OUTER[label],
        "InZone": False,
        "ZoneRow": 0,
        "ZoneCol": 0,
        "ZoneCell": 0,
        "OuterLabel": label,
    }


def empty_row(team: str, game_date, batter: str, zone_meta: Dict[str, object]) -> Dict[str, float]:
    row: Dict[str, float] = {
        "BatterTeam": team,
        "Date": game_date,
        "Batter": batter,
        "ZoneId": int(zone_meta["ZoneId"]),
        "InZone": bool(zone_meta["InZone"]),
        "ZoneRow": int(zone_meta["ZoneRow"]),
        "ZoneCol": int(zone_meta["ZoneCol"]),
        "ZoneCell": int(zone_meta["ZoneCell"]),
        "OuterLabel": str(zone_meta["OuterLabel"]),
        "ZoneVersion": ZONE_VERSION,
    }
    for col in ALL_TRACKED_COLUMNS:
        row[col] = 0
    return row


def get_batter_bins_from_buffer(buffer, filename: str) -> Dict[BinKey, Dict[str, float]]:
    df = pd.read_csv(buffer)

    # Get date from filename
    date_parser = CSVFilenameParser()
    game_date = str(date_parser.get_date_object(filename))

    required = [
        "Batter",
        "BatterTeam",
        "AutoPitchType",
        "PlateLocSide",
        "PlateLocHeight",
        "PitchCall",
        "PlayResult",
    ]
    if not all(col in df.columns for col in required):
        print(f"Skipping {csv_path.name}: missing required columns")
        return {}

    df = df.dropna(subset=["Batter", "BatterTeam", "PlateLocSide", "PlateLocHeight"]).copy()
    df["Date"] = game_date

    bins: Dict[BinKey, Dict[str, float]] = {}

    for _, row in df.iterrows():
        try:
            x = float(row["PlateLocSide"])
            y = float(row["PlateLocHeight"])
        except (TypeError, ValueError):
            continue

        zone_meta = classify_zone(x, y)
        team = str(row["BatterTeam"]).strip()
        batter = str(row["Batter"]).strip()
        if not team or not batter:
            continue

        key: BinKey = (team, game_date, batter, int(zone_meta["ZoneId"]))
        record = bins.get(key)
        if record is None:
            record = empty_row(team, game_date, batter, zone_meta)
            bins[key] = record

        record["TotalPitchCount"] += 1

        pitch_key = norm_pitch_type(row.get("AutoPitchType", ""))
        record[f"Count_{pitch_key}"] += 1

        pitch_call = str(row.get("PitchCall", "")).strip()
        play_result = str(row.get("PlayResult", "")).strip()

        is_swing = pitch_call in SWING_PITCH_CALLS
        is_hit = play_result in HIT_RESULTS

        if is_swing:
            record["TotalSwingCount"] += 1
            record[f"SwingCount_{pitch_key}"] += 1
        if is_hit:
            record["TotalHitCount"] += 1
            record[f"HitCount_{pitch_key}"] += 1

    return bins


def upload_batter_pitch_bins(bins: Dict[BinKey, Dict[str, float]]):
    if not bins:
        print("No batter bins to upload.")
        return

    payload = [json.loads(json.dumps(row, cls=NumpyEncoder)) for row in bins.values()]
    batch = 200
    uploaded = 0
    for start in range(0, len(payload), batch):
        chunk = payload[start : start + batch]
        try:
            supabase.table("BatterPitchBins").upsert(
                chunk,
                on_conflict="BatterTeam,Date,Batter,ZoneId",
            ).execute()
            uploaded += len(chunk)
            print(f"Uploaded batch {(start // batch) + 1}: {len(chunk)} records")
        except Exception as exc:
            print(f"Failed batch {(start // batch) + 1}: {exc}")
    print(f"Uploaded {uploaded} BatterPitchBins records")


def main():
    csv_root = PROJECT_ROOT / "scripts" / "csv"
    year = int(os.getenv("BINS_YEAR", "2025"))

    year_folder = csv_root / str(year)
    if not year_folder.exists():
        raise RuntimeError(f"CSV folder not found: {year_folder}")

    csv_files = [p for p in year_folder.glob("*.csv") if p.is_file()]
    print(f"Processing {len(csv_files)} batter CSV files for {year}")

    aggregated: Dict[BinKey, Dict[str, float]] = {}
    for csv_path in csv_files:
        print(f"  -> {csv_path.name}")
        bins = process_csv(csv_path, year)
        merge_bins(aggregated, bins)

    print(f"Aggregated {len(aggregated)} batter-zone rows")
    upload(aggregated)


if __name__ == "__main__":
    main()
