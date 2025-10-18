from io import StringIO

from utils.update_batter_pitch_bins_table import (
    classify_zone,
    get_batter_bins_from_buffer,
    norm_pitch_type,
)


def test_norm_pitch_type_aliases():
    assert norm_pitch_type("Four seam") == "FourSeam"
    assert norm_pitch_type("SL") == "Slider"
    assert norm_pitch_type("forkball") == "Splitter"
    assert norm_pitch_type(123) == "Other"


def test_classify_zone_in_and_out():
    center = classify_zone(0.0, 2.5)
    assert center["InZone"] is True
    assert center["ZoneId"] == 5

    outer = classify_zone(1.0, 1.0)
    assert outer["InZone"] is False
    assert outer["OuterLabel"] == "OBR"
    assert outer["ZoneId"] == 13


def test_get_batter_bins_from_buffer():
    csv = """Batter,BatterTeam,AutoPitchType,PlateLocSide,PlateLocHeight,PitchCall,PlayResult
Doe,AUB_TIG,Four-Seam,0.0,2.5,StrikeSwinging,Single
Doe,AUB_TIG,Slider,1.0,1.0,BallCalled,
"""
    bins = get_batter_bins_from_buffer(StringIO(csv), "20240216-Game-1.csv")
    assert len(bins) == 2

    keys = list(bins.keys())
    zone5 = [k for k in keys if k[-1] == 5][0]
    zone13 = [k for k in keys if k[-1] == 13][0]

    record_zone5 = bins[zone5]
    assert record_zone5["TotalPitchCount"] == 1
    assert record_zone5["TotalSwingCount"] == 1
    assert record_zone5["TotalHitCount"] == 1
    assert record_zone5["Count_FourSeam"] == 1
    assert record_zone5["SwingCount_FourSeam"] == 1
    assert record_zone5["HitCount_FourSeam"] == 1

    record_zone13 = bins[zone13]
    assert record_zone13["TotalPitchCount"] == 1
    assert record_zone13["Count_Slider"] == 1
    assert record_zone13["TotalSwingCount"] == 0
    assert record_zone13["TotalHitCount"] == 0
