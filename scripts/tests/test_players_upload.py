import io
from unittest.mock import MagicMock

import pytest

from scripts.utils import players_upload as mod


# -----------------------------
# Fixtures
# -----------------------------
@pytest.fixture
def sample_csv_buffer():
    csv = """Pitcher,PitcherId,PitcherTeam,Batter,BatterId,BatterTeam
John Doe,PID123,TeamA,Jane Roe,BID456,TeamB
"""
    return io.StringIO(csv)


@pytest.fixture
def sample_csv_buffer_missing_columns():
    csv = "SomeCol,AnotherCol\n1,2\n"
    return io.StringIO(csv)


@pytest.fixture
def mock_supabase(monkeypatch):
    supabase_mock = MagicMock()
    table_mock = MagicMock()
    supabase_mock.table.return_value = table_mock
    monkeypatch.setattr(mod, "supabase", supabase_mock)
    return supabase_mock, table_mock


# -----------------------------
# Tests for get_players_from_buffer
# -----------------------------
def test_get_players_from_buffer_basic(sample_csv_buffer, monkeypatch):
    # Patch CSVFilenameParser to return a fixed date
    class DummyParser:
        def get_date_object(self, filename):
            import datetime

            return datetime.date(2024, 7, 4)

    monkeypatch.setattr(mod, "CSVFilenameParser", lambda: DummyParser())
    result = mod.get_players_from_buffer(sample_csv_buffer, "game_2024-07-04.csv")

    assert len(result) == 2
    pitcher_key = ("John Doe", "TeamA", 2024)
    batter_key = ("Jane Roe", "TeamB", 2024)
    assert pitcher_key in result
    assert batter_key in result
    assert result[pitcher_key]["PitcherId"] == "PID123"
    assert result[batter_key]["BatterId"] == "BID456"


def test_get_players_from_buffer_missing_columns(sample_csv_buffer_missing_columns):
    result = mod.get_players_from_buffer(sample_csv_buffer_missing_columns, "dummy.csv")
    assert result == {}


def test_get_players_from_buffer_invalid_date(capsys):
    invalid_filename = "invalid_filename.csv"

    # Use an empty buffer since the date parsing is the focus
    import io

    buffer = io.StringIO("Pitcher,PitcherId,PitcherTeam\n")

    from scripts.utils import players_upload as mod

    players = mod.get_players_from_buffer(buffer, invalid_filename)

    # Function should return an empty dict
    assert players == {}

    # Check printed output contains the expected message
    captured = capsys.readouterr()
    assert "Unable to parse game date from filename" in captured.out


def test_get_players_from_buffer_existing_player_no_id():
    # CSV data with two rows for the same pitcher, first row has PitcherId missing
    csv_data = """Pitcher,PitcherId,PitcherTeam,Batter,BatterId,BatterTeam
,,,Player A,BID123,TeamA
Player B,PID123,TeamB,,,
"""
    buffer = io.StringIO(csv_data)
    filename = "20240704-game-01.csv"  # matches v3 pattern YYYYMMDD-Description-Number

    players_dict = mod.get_players_from_buffer(buffer, filename)

    key_a = ("Player A", "TeamA", 2024)
    key_b = ("Player B", "TeamB", 2024)

    # Single Batter or Pitcher
    assert key_a in players_dict
    assert key_b in players_dict

    assert players_dict[key_a]["PitcherId"] == None
    assert players_dict[key_a]["BatterId"] == "BID123"

    assert players_dict[key_b]["PitcherId"] == "PID123"
    assert players_dict[key_b]["BatterId"] == None

    csv_data = """Pitcher,PitcherId,PitcherTeam,Batter,BatterId,BatterTeam
,,,Player A,BID123,TeamA
Player A,PID123,TeamA,,,
"""

    buffer = io.StringIO(csv_data)
    filename = "20240704-game-02.csv"  # matches v3 pattern YYYYMMDD-Description-Number

    players_dict = mod.get_players_from_buffer(buffer, filename)

    key_a = ("Player A", "TeamA", 2024)

    # Player plays both ways batter first
    assert key_a in players_dict

    assert players_dict[key_a]["PitcherId"] == "PID123"
    assert players_dict[key_a]["BatterId"] == "BID123"

    csv_data = """Pitcher,PitcherId,PitcherTeam,Batter,BatterId,BatterTeam
Player A,PID123,TeamA,,,
,,,Player A,BID123,TeamA
"""

    buffer = io.StringIO(csv_data)
    filename = "20240704-game-02.csv"  # matches v3 pattern YYYYMMDD-Description-Number

    players_dict = mod.get_players_from_buffer(buffer, filename)

    key_a = ("Player A", "TeamA", 2024)

    # Player plays both ways pitcher first
    assert key_a in players_dict

    assert players_dict[key_a]["PitcherId"] == "PID123"
    assert players_dict[key_a]["BatterId"] == "BID123"


# -----------------------------
# Tests for upload_players_to_supabase
# -----------------------------
def test_upload_players_to_supabase_normal(monkeypatch):
    # Prepare dummy player dict
    player_dict = {
        ("John Doe", "TeamA", 2024): {
            "Name": "John Doe",
            "PitcherId": "PID123",
            "BatterId": None,
            "TeamTrackmanAbbreviation": "TeamA",
            "Year": 2024,
            "unique_games": set(),
        }
    }

    supabase_mock = MagicMock()
    table_mock = MagicMock()
    supabase_mock.table.return_value = table_mock
    table_mock.upsert.return_value.execute.return_value = None
    table_mock.select.return_value.execute.return_value.data = [
        {"PitcherId": "PID123", "BatterId": None}
    ]
    monkeypatch.setattr(mod, "supabase", supabase_mock)

    mod.upload_players_to_supabase(player_dict)

    # Should call upsert and select
    assert table_mock.upsert.called
    assert table_mock.select.called


def test_upload_players_to_supabase_batch_continue(monkeypatch):
    # Create 3 players, batch size 1 to force multiple batches
    players = {}
    for i in range(3):
        players[(f"Pitcher{i}", f"Team{i}", 2024)] = {
            "Name": f"Pitcher{i}",
            "PitcherId": f"PID{i}",
            "BatterId": None,
            "TeamTrackmanAbbreviation": f"Team{i}",
            "Year": 2024,
            "unique_games": set(),
        }

    supabase_mock = MagicMock()
    table_mock = MagicMock()
    monkeypatch.setattr(mod, "supabase", supabase_mock)
    supabase_mock.table.return_value = table_mock

    # Simulate first upsert failing
    def raise_error(*args, **kwargs):
        raise RuntimeError("Simulated upsert failure")

    table_mock.upsert.return_value.execute.side_effect = raise_error

    # Should not raise, should hit continue
    mod.upload_players_to_supabase(players, batch_size=1)

    assert table_mock.upsert.call_count == 3  # Each batch attempted despite failures


def test_upload_players_to_supabase_outer_exception(monkeypatch):
    # Single player
    players = {
        ("John Doe", "TeamA", 2024): {
            "Name": "John Doe",
            "PitcherId": "PID123",
            "BatterId": None,
            "TeamTrackmanAbbreviation": "TeamA",
            "Year": 2024,
            "unique_games": set(),
        }
    }

    supabase_mock = MagicMock()
    table_mock = MagicMock()
    monkeypatch.setattr(mod, "supabase", supabase_mock)
    supabase_mock.table.return_value = table_mock
    table_mock.upsert.return_value.execute.return_value = None

    # Final select raises exception
    table_mock.select.side_effect = RuntimeError("Simulated final count failure")

    mod.upload_players_to_supabase(players)

    # Upsert should still be called for batch
    assert table_mock.upsert.called


def test_upload_players_to_supabase_empty_dict(capsys):
    """Test that empty players_dict is handled correctly"""
    # Test with empty dictionary
    mod.upload_players_to_supabase({})

    # Capture the printed output
    captured = capsys.readouterr()
    assert "No players to upload" in captured.out

    # Test with None (if you want to be extra thorough)
    mod.upload_players_to_supabase(None)

    captured = capsys.readouterr()
    assert "No players to upload" in captured.out
