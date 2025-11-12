# pitch_bin.py  (13 zones: 3x3 inner + 4 outer quadrants)
import json
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from supabase import Client, create_client

from .common import SUPABASE_KEY, SUPABASE_URL, NumpyEncoder, check_practice, check_supabase_vars
from .file_date import CSVFilenameParser

# -----------------------------------------------------------------------------
# Supabase client
# -----------------------------------------------------------------------------
check_supabase_vars()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)  # type: ignore[arg-type]

# -----------------------------------------------------------------------------
# Fixed visualization zone (consistent with our UI)
# -----------------------------------------------------------------------------
ZONE_VERSION = "fixed_v3"

# inner box bounds (feet)
Z_X_HALF = 0.83  # ~ 17" plate half-width (≈ 0.7083) plus small margin if desired
Z_Y_BOT = 1.50
Z_Y_TOP = 3.50

# 3x3 splits (row 1 = bottom, col 1 = left)
SPLITS = 3
X_EDGES = np.linspace(-Z_X_HALF, +Z_X_HALF, SPLITS + 1)  # 4 edges
Y_EDGES = np.linspace(Z_Y_BOT, Z_Y_TOP, SPLITS + 1)

MID_X = 0.0
MID_Y = float((Z_Y_BOT + Z_Y_TOP) / 2.0)

# ZoneId map (row-major for inner)
# 1=IBL,2=IBM,3=IBR, 4=IML,5=IMM,6=IMR, 7=ITL,8=ITM,9=ITR, 10=OTL,11=OTR,12=OBL,13=OBR
OUTER_ID = {"OTL": 10, "OTR": 11, "OBL": 12, "OBR": 13}


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def norm_pitch_type(s: str) -> str:
    """
    Canonicalize pitch type -> one of:
      FourSeam, Sinker, Slider, Curveball, Changeup, Cutter, Splitter, Other
    Extend this map to fit your data as needed.
    """
    if not isinstance(s, str):
        return "Other"
    t = s.strip().lower()
    # fastballs
    if t in {
        "four-seam",
        "four seam",
        "fourseam",
        "4-seam",
        "4 seam",
        "ff",
        "fastball",
        "fb",
    }:
        return "FourSeam"
    if t in {
        "sinker",
        "two-seam",
        "two seam",
        "2-seam",
        "2 seam",
        "si",
        "two-seam fastball",
    }:
        return "Sinker"
    if t in {"cutter", "fc"}:
        return "Cutter"
    # breakers & offspeed
    if t in {"slider", "sl"}:
        return "Slider"
    if t in {"curveball", "curve", "cu", "knuckle curve", "kc"}:
        return "Curveball"
    if t in {"changeup", "change", "ch"}:
        return "Changeup"
    if t in {"splitter", "split-finger", "split finger", "fs", "forkball"}:
        return "Splitter"
    return "Other"


def norm_side(s: str) -> str:
    """Return 'L' or 'R'. If unknown/missing, default to 'R' to satisfy DB CHECK."""
    if not isinstance(s, str):
        return "R"
    t = s.strip().upper()
    if t.startswith("L"):
        return "L"
    if t.startswith("R"):
        return "R"
    return "R"


def classify_13(x: float, y: float):
    """
    Return dict with keys:
      InZone (bool), ZoneRow, ZoneCol, ZoneCell,
      OuterLabel ('NA' or OTL/OTR/OBL/OBR), ZoneId (1..13)
    Rules:
      - Inside rectangle => 3x3 via X_EDGES/Y_EDGES, ZoneCell=(row-1)*3+col, ZoneId=ZoneCell.
      - Outside => big 2x2 quadrants using MID_X/MID_Y:
            y > MID_Y and x < 0 -> OTL (10)
            y > MID_Y and x >=0 -> OTR (11)
            y <=MID_Y and x < 0 -> OBL (12)
            y <=MID_Y and x >=0 -> OBR (13)
    """
    in_x = -Z_X_HALF <= x <= +Z_X_HALF
    in_y = Z_Y_BOT <= y <= Z_Y_TOP
    if in_x and in_y:
        col = int(np.digitize(x, X_EDGES, right=False))  # pass scalar directly
        row = int(np.digitize(y, Y_EDGES, right=False))
        col = max(1, min(SPLITS, col))
        row = max(1, min(SPLITS, row))
        cell = (row - 1) * SPLITS + col  # 1..9
        return dict(
            InZone=True,
            ZoneRow=row,
            ZoneCol=col,
            ZoneCell=cell,
            OuterLabel="NA",
            ZoneId=cell,
        )
    # outside -> quadrant
    if y > MID_Y:
        label = "OTL" if x < MID_X else "OTR"
    else:
        label = "OBL" if x < MID_X else "OBR"
    return dict(
        InZone=False,
        ZoneRow=0,
        ZoneCol=0,
        ZoneCell=0,
        OuterLabel=label,
        ZoneId=OUTER_ID[label],
    )


def should_exclude_file(filename: str) -> bool:
    f = filename.lower()
    return any(p in f for p in ["fhc", "unverified", "playerpositioning"])


# -----------------------------------------------------------------------------
# Aggregation
# -----------------------------------------------------------------------------
PitchKey = Tuple[str, str, str, int]  # (PitcherTeam, Year, Pitcher, ZoneId)

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

PITCH_COLUMNS = [f"Count_{k}" for k in PITCH_KEYS]
SIDE_PITCH_COLUMNS = {side: [f"Count_{side}_{k}" for k in PITCH_KEYS] for side in ("L", "R")}
ALL_PITCH_COLUMNS = PITCH_COLUMNS + SIDE_PITCH_COLUMNS["L"] + SIDE_PITCH_COLUMNS["R"]


def empty_row(team: str, game_date, pitcher: str, meta: dict) -> dict:
    base = {
        "PitcherTeam": team,
        "Date": game_date,
        "Pitcher": pitcher,
        "ZoneId": int(meta["ZoneId"]),
        "InZone": bool(meta["InZone"]),
        "ZoneRow": int(meta["ZoneRow"]),
        "ZoneCol": int(meta["ZoneCol"]),
        "ZoneCell": int(meta["ZoneCell"]),
        "OuterLabel": str(meta["OuterLabel"]),
        "ZoneVersion": ZONE_VERSION,
        "TotalPitchCount": 0,
    }
    for col in ALL_PITCH_COLUMNS:
        base[col] = 0
    return base


def get_pitcher_bins_from_buffer(buffer, filename: str) -> Dict[PitchKey, dict]:
    df = pd.read_csv(buffer)

    # Determine if this is practice data by checking League column
    is_practice = check_practice(df)

    # Get game date from the filename
    date_parser = CSVFilenameParser()
    game_date = str(date_parser.get_date_object(filename))

    required = [
        "Pitcher",
        "PitcherTeam",
        "BatterSide",
        "AutoPitchType",
        "PlateLocSide",
        "PlateLocHeight",
    ]
    if not all(c in df.columns for c in required):
        print(f"Warning: missing required columns in {filename}")
        return {}

    df = df.dropna(subset=["Pitcher", "PitcherTeam", "PlateLocSide", "PlateLocHeight"]).copy()
    df["Date"] = game_date

    out: Dict[PitchKey, dict] = {}

    for _, r in df.iterrows():
        try:
            x = float(r["PlateLocSide"])
            y = float(r["PlateLocHeight"])
        except Exception:
            continue

        meta = classify_13(x, y)
        # Convert different aub practice team to be consistent
        pitcher_team = str(r["PitcherTeam"]).strip()
        if is_practice and pitcher_team == "AUB_PRC":
            team = "AUB_TIG"
        else:
            team = pitcher_team
        date = game_date
        pitcher = str(r["Pitcher"]).strip()
        zone_id = int(meta["ZoneId"])
        key: PitchKey = (team, date, pitcher, zone_id)

        rec = out.get(key)
        if rec is None:
            rec = empty_row(team, date, pitcher, meta)
            out[key] = rec

        # totals
        rec["TotalPitchCount"] += 1

        # pitch type counter (overall + side split)
        pt = norm_pitch_type(str(r.get("AutoPitchType", "")))

        overall_col = f"Count_{pt}"
        rec[overall_col] += 1

        # batter side counter (default to 'R' if unknown to satisfy DB CHECK)
        side = norm_side(str(r.get("BatterSide", "")))
        side_col = f"Count_{side}_{pt}" if pt in PITCH_KEYS else f"Count_{side}_Other"
        rec[side_col] += 1

    return out


# -----------------------------------------------------------------------------
# Upload
# -----------------------------------------------------------------------------
def upload_pitcher_pitch_bins(bins: Dict[PitchKey, dict]):
    if not bins:
        print("No bins data to upload")
        return

    payload = [json.loads(json.dumps(v, cls=NumpyEncoder)) for v in bins.values()]
    print(f"Preparing to upload {len(payload)} bins...")

    batch = 1000
    total = 0
    for i in range(0, len(payload), batch):
        chunk = payload[i : i + batch]
        try:
            supabase.table("PitcherPitchBins").upsert(
                chunk, on_conflict="PitcherTeam,Date,Pitcher,ZoneId"
            ).execute()
            total += len(chunk)
            print(f"Uploaded batch {i//batch + 1}: {len(chunk)}")
        except Exception as e:
            print(f"Error uploading batch {i//batch + 1}: {e}")
            if chunk:
                print("Sample record:", chunk[0])
            continue
    print(f"Successfully processed {total} records")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main():
    print("Starting pitch bins CSV processing...")
    # csv_folder_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "csv")
    # TODO: Add updated get_ and upload functions


if __name__ == "__main__":
    main()
