# pitch_bin.py  (13 zones: 3x3 inner + 4 outer quadrants)
import os, json
from pathlib import Path
from typing import Dict, Tuple
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

# -----------------------------------------------------------------------------
# Environment / Supabase
# -----------------------------------------------------------------------------
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

SUPABASE_URL = os.getenv("VITE_SUPABASE_PROJECT_URL")
SUPABASE_KEY = os.getenv("VITE_SUPABASE_API_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("VITE_SUPABASE_PROJECT_URL and VITE_SUPABASE_API_KEY must be set")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------------------------------------------------------
# Fixed visualization zone (consistent with our UI)
# -----------------------------------------------------------------------------
ZONE_VERSION = "fixed_v3"

# inner box bounds (feet)
Z_X_HALF = 0.83       # ~ 17" plate half-width (≈ 0.7083) plus small margin if desired
Z_Y_BOT  = 1.50
Z_Y_TOP  = 3.50

# 3x3 splits (row 1 = bottom, col 1 = left)
SPLITS = 3
X_EDGES = np.linspace(-Z_X_HALF, +Z_X_HALF, SPLITS + 1)  # 4 edges
Y_EDGES = np.linspace( Z_Y_BOT,  Z_Y_TOP,  SPLITS + 1)

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
    if t in {"four-seam", "four seam", "fourseam", "4-seam", "4 seam", "ff", "fastball", "fb"}:
        return "FourSeam"
    if t in {"sinker", "two-seam", "two seam", "2-seam", "2 seam", "si", "two-seam fastball"}:
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
      InZone (bool), ZoneRow, ZoneCol, ZoneCell, OuterLabel ('NA' or OTL/OTR/OBL/OBR), ZoneId (1..13)
    Rules:
      - Inside rectangle => 3x3 via X_EDGES/Y_EDGES, ZoneCell=(row-1)*3+col, ZoneId=ZoneCell.
      - Outside => big 2x2 quadrants using MID_X/MID_Y:
            y > MID_Y and x < 0 -> OTL (10)
            y > MID_Y and x >=0 -> OTR (11)
            y <=MID_Y and x < 0 -> OBL (12)
            y <=MID_Y and x >=0 -> OBR (13)
    """
    in_x = (-Z_X_HALF <= x <= +Z_X_HALF)
    in_y = ( Z_Y_BOT  <= y <=  Z_Y_TOP)
    if in_x and in_y:
        col = int(np.digitize([x], X_EDGES, right=False)[0])  # 1..3
        row = int(np.digitize([y], Y_EDGES, right=False)[0])  # 1..3
        col = max(1, min(SPLITS, col))
        row = max(1, min(SPLITS, row))
        cell = (row - 1) * SPLITS + col  # 1..9
        return dict(
            InZone=True, ZoneRow=row, ZoneCol=col, ZoneCell=cell,
            OuterLabel="NA", ZoneId=cell
        )
    # outside -> quadrant
    if y > MID_Y:
        label = "OTL" if x < MID_X else "OTR"
    else:
        label = "OBL" if x < MID_X else "OBR"
    return dict(
        InZone=False, ZoneRow=0, ZoneCol=0, ZoneCell=0,
        OuterLabel=label, ZoneId=OUTER_ID[label]
    )

def should_exclude_file(filename: str) -> bool:
    f = filename.lower()
    return any(p in f for p in ["fhc", "unverified", "playerpositioning"])

# -----------------------------------------------------------------------------
# Aggregation
# -----------------------------------------------------------------------------
PitchKey = Tuple[str, int, str, int]  # (PitcherTeam, Year, Pitcher, ZoneId)

PITCH_COLUMNS = [
    "Count_FourSeam", "Count_Sinker", "Count_Slider", "Count_Curveball",
    "Count_Changeup", "Count_Cutter", "Count_Splitter", "Count_Other"
]

def empty_row(team: str, year: int, pitcher: str, meta: dict) -> dict:
    base = {
        "PitcherTeam": team,
        "Year": int(year),
        "Pitcher": pitcher,
        "ZoneId": int(meta["ZoneId"]),
        "InZone": bool(meta["InZone"]),
        "ZoneRow": int(meta["ZoneRow"]),
        "ZoneCol": int(meta["ZoneCol"]),
        "ZoneCell": int(meta["ZoneCell"]),
        "OuterLabel": str(meta["OuterLabel"]),
        "ZoneVersion": ZONE_VERSION,
        "TotalPitchCount": 0,
        "Count_FourSeam": 0,
        "Count_Sinker": 0,
        "Count_Slider": 0,
        "Count_Curveball": 0,
        "Count_Changeup": 0,
        "Count_Cutter": 0,
        "Count_Splitter": 0,
        "Count_Other": 0,
        "Count_L": 0,
        "Count_R": 0,
    }
    return base

def process_csv_file(file_path: str, default_year: int = 2025) -> Dict[PitchKey, dict]:
    df = pd.read_csv(file_path)

    required = ["Pitcher","PitcherTeam","BatterSide","AutoPitchType","PlateLocSide","PlateLocHeight"]
    if not all(c in df.columns for c in required):
        print(f"Warning: missing required columns in {file_path}")
        return {}

    df = df.dropna(subset=["Pitcher","PitcherTeam","PlateLocSide","PlateLocHeight"]).copy()
    df["Year"] = int(default_year)

    out: Dict[PitchKey, dict] = {}

    for _, r in df.iterrows():
        try:
            x = float(r["PlateLocSide"])
            y = float(r["PlateLocHeight"])
        except Exception:
            continue

        meta = classify_13(x, y)
        team = str(r["PitcherTeam"])
        year = int(default_year)
        pitcher = str(r["Pitcher"])
        zone_id = int(meta["ZoneId"])
        key: PitchKey = (team, year, pitcher, zone_id)

        rec = out.get(key)
        if rec is None:
            rec = empty_row(team, year, pitcher, meta)
            out[key] = rec

        # totals
        rec["TotalPitchCount"] += 1

        # pitch type counter
        pt = norm_pitch_type(str(r.get("AutoPitchType", "")))
        col = f"Count_{pt}"
        if col not in PITCH_COLUMNS:
            col = "Count_Other"
        rec[col] += 1

        # batter side counter (default to 'R' if unknown to satisfy DB CHECK)
        side = norm_side(str(r.get("BatterSide", "")))
        if side == "L":
            rec["Count_L"] += 1
        else:
            rec["Count_R"] += 1

    return out

def process_csv_folder(csv_folder_path: str, year: int = 2025) -> Dict[PitchKey, dict]:
    year_folder = os.path.join(csv_folder_path, str(year))
    if not os.path.exists(year_folder):
        print(f"{year} CSV folder not found: {year_folder}")
        return {}

    files = [f for f in os.listdir(year_folder) if f.endswith(".csv")]
    files = [f for f in files if not should_exclude_file(f)]
    print(f"Found {len(files)} {year} CSV files to process")

    all_bins: Dict[PitchKey, dict] = {}
    for fname in files:
        fp = os.path.join(year_folder, fname)
        print(f"Processing: {fname}")
        part = process_csv_file(fp, default_year=year)
        # merge
        for k, v in part.items():
            if k in all_bins:
                dst = all_bins[k]
                dst["TotalPitchCount"] += v["TotalPitchCount"]
                for c in PITCH_COLUMNS:
                    dst[c] += v[c]
                dst["Count_L"] += v["Count_L"]
                dst["Count_R"] += v["Count_R"]
            else:
                all_bins[k] = v
    return all_bins

# -----------------------------------------------------------------------------
# Upload
# -----------------------------------------------------------------------------
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):  return int(obj)
        if isinstance(obj, (np.floating,)): return float(obj)
        if isinstance(obj, (np.ndarray,)):  return obj.tolist()
        if pd.isna(obj):                    return None
        return super().default(obj)

def upload_bins_to_supabase(bins: Dict[PitchKey, dict]):
    if not bins:
        print("No bins data to upload")
        return

    payload = [json.loads(json.dumps(v, cls=NumpyEncoder)) for v in bins.values()]
    print(f"Preparing to upload {len(payload)} bins...")

    batch = 200
    total = 0
    for i in range(0, len(payload), batch):
        chunk = payload[i:i+batch]
        try:
            supabase.table("PitcherPitchBins") \
                .upsert(chunk, on_conflict="PitcherTeam,Year,Pitcher,ZoneId") \
                .execute()
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
    csv_folder_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "csv")
    year = 2025
    print(f"Looking for CSV files in: {csv_folder_path}\\{year}")
    bins = process_csv_folder(csv_folder_path, year=year)
    print(f"\nTotal unique bins: {len(bins)}")
    if bins:
        print("Sample:")
        for i, (k, v) in enumerate(list(bins.items())[:5]):
            print(" ", k, {kk: v[kk] for kk in ['ZoneId','InZone','ZoneRow','ZoneCol','ZoneCell','OuterLabel','TotalPitchCount']})
        print("\nUploading to Supabase...")
        upload_bins_to_supabase(bins)
    else:
        print("No bins to upload")

if __name__ == "__main__":
    main()
