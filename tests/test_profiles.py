import pytest
import os
import json
import tempfile
from app.profiles import ProfileManager, DEFAULT_PROFILES


@pytest.fixture
def temp_profiles_dir(tmp_path):
    d = tmp_path / "profiles"
    d.mkdir()
    return str(d)


def test_profile_manager_creates_defaults(temp_profiles_dir):
    mgr = ProfileManager(profiles_dir=temp_profiles_dir)
    profiles = mgr.list_profiles()
    assert "forza" in profiles
    assert "default" in profiles
    assert "beamng" in profiles
    assert "assettocorsa" in profiles
    assert "f1" in profiles
    assert "dirtrally" in profiles
    assert "trackmania" in profiles


def test_load_valid_profile(temp_profiles_dir):
    mgr = ProfileManager(profiles_dir=temp_profiles_dir)
    data = mgr.load_profile("forza")
    assert "steering" in data
    assert data["input_mode"] == "GAMEPAD"


def test_load_unknown_profile_fallback(temp_profiles_dir):
    mgr = ProfileManager(profiles_dir=temp_profiles_dir)
    data = mgr.load_profile("nonexistent_profile_xyz")
    assert "steering" in data


def test_save_and_load_custom_profile(temp_profiles_dir):
    mgr = ProfileManager(profiles_dir=temp_profiles_dir)
    custom = {
        "name": "My Custom Profile",
        "input_mode": "GAMEPAD",
        "steering": {"max_angle": 90.0, "curve": "CUBIC"}
    }
    assert mgr.save_profile("my_custom", custom)
    loaded = mgr.load_profile("my_custom")
    assert loaded["name"] == "My Custom Profile"
    assert loaded["steering"]["max_angle"] == 90.0


def test_delete_profile(temp_profiles_dir):
    mgr = ProfileManager(profiles_dir=temp_profiles_dir)
    mgr.save_profile("temp_profile", {"name": "Temp"})
    assert "temp_profile" in mgr.list_profiles()
    result = mgr.delete_profile("temp_profile")
    assert result
    assert "temp_profile" not in mgr.list_profiles()


def test_cannot_delete_forza(temp_profiles_dir):
    mgr = ProfileManager(profiles_dir=temp_profiles_dir)
    result = mgr.delete_profile("forza")
    assert not result  # Protected profile


def test_duplicate_profile(temp_profiles_dir):
    mgr = ProfileManager(profiles_dir=temp_profiles_dir)
    result = mgr.duplicate_profile("forza", "forza_copy")
    assert result
    data = mgr.load_profile("forza_copy")
    assert "steering" in data


def test_corrupted_profile_fallback(temp_profiles_dir):
    """Corrupt JSON should fall back to default gracefully."""
    corrupt_path = os.path.join(temp_profiles_dir, "corrupt.json")
    with open(corrupt_path, "w") as f:
        f.write("{invalid json!!!")
    mgr = ProfileManager(profiles_dir=temp_profiles_dir)
    data = mgr.load_profile("corrupt")
    assert isinstance(data, dict)
    assert "steering" in data


def test_export_import_profile(temp_profiles_dir, tmp_path):
    mgr = ProfileManager(profiles_dir=temp_profiles_dir)
    export_path = str(tmp_path / "exported_forza.json")
    result = mgr.export_profile("forza", export_path)
    assert result
    assert os.path.exists(export_path)

    result2 = mgr.import_profile(export_path, "forza_imported")
    assert result2
    assert "forza_imported" in mgr.list_profiles()


def test_all_default_profiles_have_steering():
    """All built-in DEFAULT_PROFILES should have a valid steering section."""
    for key, data in DEFAULT_PROFILES.items():
        assert "steering" in data, f"Profile '{key}' missing steering section"


def test_all_default_profiles_have_name():
    for key, data in DEFAULT_PROFILES.items():
        assert "name" in data, f"Profile '{key}' missing name field"
