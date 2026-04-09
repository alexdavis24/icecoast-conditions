import pytest
from pipeline.locations import load_locations

def test_load_locations():
    locations = load_locations()
    assert len(locations) >= 5
    stowe = next(loc for loc in locations if loc.slug == "stowe-vt")
    assert stowe.name == "Stowe, Vermont"
    assert stowe.latitude == 44.4654
