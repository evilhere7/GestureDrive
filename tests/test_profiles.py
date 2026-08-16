import os
import shutil
import pytest
from app.profiles import ProfileManager

@pytest.fixture
def temp_profiles_dir(tmp_path):
    dir_path = tmp_path / "test_profiles"
    yield str(dir_path)
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)

def test_profile_manager_lifecycle(temp_profiles_dir):
    mgr = ProfileManager(profiles_dir=temp_profiles_dir)
    
    # Default profiles created
    profiles = mgr.list_profiles()
    assert "default" in profiles
    assert "nfs" in profiles
    assert "forza" in profiles

    # Load profile
    prof_data = mgr.load_profile("default")
    assert prof_data["input_mode"] == "KEYBOARD"

    # Save custom profile
    custom_data = {
        "name": "Custom Arcade",
        "input_mode": "KEYBOARD",
        "keyboard_mappings": {"steer_left": "j", "steer_right": "l"}
    }
    assert mgr.save_profile("arcade", custom_data)
    assert "arcade" in mgr.list_profiles()

    loaded_custom = mgr.load_profile("arcade")
    assert loaded_custom["name"] == "Custom Arcade"

    # Delete profile
    assert mgr.delete_profile("arcade")
    assert "arcade" not in mgr.list_profiles()

    # Cannot delete default
    assert not mgr.delete_profile("default")
