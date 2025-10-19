from io import StringIO

from utils.pitcher_pitch_bins_upload import (
    classify_13,
    get_pitcher_bins_from_buffer,
    norm_pitch_type,
    norm_side,
    should_exclude_file,
)


def test_norm_pitch_type_and_side():
    assert norm_pitch_type("four seam") == "FourSeam"
    assert norm_pitch_type("Two-Seam Fastball") == "Sinker"
    assert norm_pitch_type("FAKE") == "Other"
    assert norm_side("L") == "L"
    assert norm_side("Left") == "L"
    assert norm_side("Unknown") == "R"


def test_classify_13():
    inner = classify_13(0.0, 2.5)
    assert inner["InZone"]
    assert inner["ZoneId"] == 5

    outer = classify_13(1.0, 1.0)
    assert not outer["InZone"]
    assert outer["ZoneId"] == 13


def test_should_exclude_file():
    assert should_exclude_file("unverified_data.csv")
    assert not should_exclude_file("regular_game.csv")


def test_get_pitcher_bins_from_buffer():
    csv = """Pitcher,PitcherTeam,BatterSide,AutoPitchType,PlateLocSide,PlateLocHeight
Ace,AUB_TIG,L,Four-Seam,0.0,2.5
Ace,AUB_TIG,R,Slider,1.0,1.0
"""
    bins = get_pitcher_bins_from_buffer(StringIO(csv), "20240216-Game-1.csv")
    assert len(bins) == 2
    keys = list(bins.keys())
    zone5 = [k for k in keys if k[-1] == 5][0]
    zone13 = [k for k in keys if k[-1] == 13][0]

    rec5 = bins[zone5]
    assert rec5["TotalPitchCount"] == 1
    assert rec5["Count_FourSeam"] == 1
    assert rec5["Count_L_FourSeam"] == 1

    rec13 = bins[zone13]
    assert rec13["TotalPitchCount"] == 1
    assert rec13["Count_Slider"] == 1
    assert rec13["Count_R_Slider"] == 1
