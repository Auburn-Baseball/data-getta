"""
Author: Joshua Reed
Created: 3 November 2025

Unit test cases for common.py functions.
"""

import json

import numpy as np
import pytest

from scripts.utils import common as mod

# ---------- Tests for Supabase variable validation ----------


def test_supabase_vars():
    # Test that missing Supabase credentials raise a ValueError
    mod.SUPABASE_URL = None
    mod.SUPABASE_KEY = None
    with pytest.raises(ValueError):
        mod.check_supabase_vars()

    # Test that valid Supabase credentials do not raise an error
    mod.SUPABASE_URL = "https://example.supabase.co"
    mod.SUPABASE_KEY = "fake_key_123"
    mod.check_supabase_vars()  # should pass silently


# ---------- Tests for custom NumpyEncoder class ----------


def test_numpy_encoder_integer():
    # NumPy integer should serialize as a standard JSON integer
    data = {"val": np.int32(42)}
    encoded = json.dumps(data, cls=mod.NumpyEncoder)
    assert encoded == '{"val": 42}'


def test_numpy_encoder_float_direct_call():
    # NumPy float should serialize as a standard Python float
    encoder = mod.NumpyEncoder()
    result = encoder.default(np.float64(3.14))
    assert result == 3.14


def test_numpy_encoder_bool():
    # NumPy boolean should serialize as a JSON true/false
    data = {"val": np.bool_(True)}
    encoded = json.dumps(data, cls=mod.NumpyEncoder)
    assert encoded == '{"val": true}'


def test_numpy_encoder_array():
    # NumPy array should serialize as a JSON list
    data = {"arr": np.array([1, 2, 3])}
    encoded = json.dumps(data, cls=mod.NumpyEncoder)
    assert encoded == '{"arr": [1, 2, 3]}'


def test_numpy_encoder_nan_branch():
    # np.nan should be converted to None
    encoder = mod.NumpyEncoder()
    assert encoder.default(np.nan) is None


def test_numpy_encoder_default_fallback():
    # Unsupported object types should raise a TypeError
    class CustomObject:
        pass

    obj = CustomObject()
    with pytest.raises(TypeError):
        json.dumps(obj, cls=mod.NumpyEncoder)


# ---------- Tests for is_in_strike_zone ----------


@pytest.fixture(autouse=True)
def setup_strike_zone(monkeypatch):
    # Mock strike zone constants for consistent testing
    monkeypatch.setattr(mod, "MIN_PLATE_HEIGHT", 1.5)
    monkeypatch.setattr(mod, "MAX_PLATE_HEIGHT", 3.5)
    monkeypatch.setattr(mod, "MIN_PLATE_SIDE", -0.95)
    monkeypatch.setattr(mod, "MAX_PLATE_SIDE", 0.95)


def test_is_in_strike_zone_true():
    # Within strike zone boundaries (should return True)
    assert mod.is_in_strike_zone(2.5, 0.0) is True


def test_is_in_strike_zone_height_too_low():
    # Below minimum height (should return False)
    assert mod.is_in_strike_zone(1.4, 0.0) is False


def test_is_in_strike_zone_height_too_high():
    # Above maximum height (should return False)
    assert mod.is_in_strike_zone(3.6, 0.0) is False


def test_is_in_strike_zone_side_too_left():
    # Too far left horizontally (should return False)
    assert mod.is_in_strike_zone(2.5, -1.0) is False


def test_is_in_strike_zone_side_too_right():
    # Too far right horizontally (should return False)
    assert mod.is_in_strike_zone(2.5, 1.0) is False


def test_is_in_strike_zone_with_string_inputs():
    # Numeric strings should be converted and evaluated correctly
    assert mod.is_in_strike_zone("2.5", "0.5") is True


def test_is_in_strike_zone_with_invalid_inputs():
    # Invalid or non-numeric inputs should safely return False
    assert mod.is_in_strike_zone("bad", 0.5) is False
    assert mod.is_in_strike_zone(None, 0.5) is False
    assert mod.is_in_strike_zone(2.5, "nan") is False
