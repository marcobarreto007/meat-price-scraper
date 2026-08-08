import pytest
from src.geo import (
    MONTREAL_COORDS,
    distance_from_center,
    geocode,
    haversine_km,
    is_within_radius,
    CENTER_LAT,
    CENTER_LON,
    RADIUS_KM,
)


def test_haversine_same_point():
    assert haversine_km(45.5, -73.6, 45.5, -73.6) == 0.0


def test_haversine_known_distance():
    dist = haversine_km(45.5225, -73.5940, 45.5030, -73.5700)
    assert 2.0 < dist < 3.0


def test_haversine_long_distance():
    dist = haversine_km(45.5225, -73.5940, 48.8566, 2.3522)
    assert 5000 < dist < 6000


class TestGeocode:
    def test_exact_postal_code(self):
        coords = geocode("H2T1S8")
        assert coords == (45.5225, -73.5940)

    def test_exact_with_space(self):
        coords = geocode("H2T 1S8")
        assert coords == (45.5225, -73.5940)

    def test_fsa_match(self):
        coords = geocode("H3A 1B2")
        assert coords == MONTREAL_COORDS["H3A"]

    def test_unknown(self):
        assert geocode("ZZZ999") is None

    def test_lowercase(self):
        coords = geocode("h2t1s8")
        assert coords == (45.5225, -73.5940)


class TestRadius:
    def test_center_is_within(self):
        assert is_within_radius(CENTER_LAT, CENTER_LON) is True

    def test_montreal_is_within(self):
        assert is_within_radius(45.5030, -73.5700) is True

    def test_toronto_is_outside(self):
        assert is_within_radius(43.6532, -79.3832) is False

    def test_laval_is_within(self):
        assert is_within_radius(45.6100, -73.6400) is True

    def test_extreme_near_edge(self):
        d = distance_from_center(45.5225, -73.15)
        assert d > 30
