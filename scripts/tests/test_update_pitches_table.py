from io import StringIO

from utils.pitch_counts_upload import get_pitch_counts_from_buffer


def test_get_pitch_counts_from_buffer():
    csv = """Pitcher,PitcherTeam,AutoPitchType,TaggedPitchType,GameUID
Ace,AUB_TIG,Four-Seam,Fastball,G1
Ace,AUB_TIG,Slider,Fastball,G1
Ace,AUB_TIG,Other,Fastball,G1
Ace,AUB_TIG,Sinker,Fastball,G2
Ace,AUB_TIG,,Fastball,G2
Ace,AUB_TIG,Changeup,Changeup,G2
"""
    stats = get_pitch_counts_from_buffer(StringIO(csv), "20240216-Game-1.csv")
    key = ("Ace", "AUB_TIG", 2024)
    assert key in stats
    record = stats[key]

    assert record["total_pitches"] == 6
    assert record["fourseam_count"] == 1
    assert record["slider_count"] == 1
    assert record["sinker_count"] == 1
    assert record["changeup_count"] == 1
    assert record["twoseam_count"] == 4
    assert record["other_count"] == 2
    assert record["games"] == 2
