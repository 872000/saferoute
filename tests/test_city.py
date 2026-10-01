"""GridCity: seeded reproducibility, safety bounds, label parsing."""

import numpy as np

from saferoute.city import GridCity


def test_seeded_generation_is_reproducible():
    a = GridCity(size=20, seed=42)
    b = GridCity(size=20, seed=42)
    assert np.array_equal(a.safety, b.safety)
    assert np.array_equal(a.lighting, b.lighting)
    assert np.array_equal(a.incidents, b.incidents)


def test_different_seeds_give_different_maps():
    a = GridCity(size=20, seed=42)
    b = GridCity(size=20, seed=43)
    assert not np.array_equal(a.safety, b.safety)


def test_safety_scores_are_bounded():
    city = GridCity(size=20, seed=7)
    assert city.safety.min() >= 0.0
    assert city.safety.max() <= 1.0
    assert (city.lighting >= 0.0).all() and (city.lighting <= 1.0).all()
    assert (city.incidents >= 0).all()


def test_label_roundtrip():
    assert GridCity.parse_label("A1", 20) == (0, 0)
    assert GridCity.parse_label("T20", 20) == (19, 19)
    assert GridCity.parse_label("j10", 20) == (9, 9)  # case-insensitive
    city = GridCity(size=20, seed=1)
    assert city.label((0, 0)) == "A1"
    assert city.label((19, 19)) == "T20"


def test_bad_labels_rejected():
    for bad in ("", "1A", "A0", "A21", "U1", "AA"):
        try:
            GridCity.parse_label(bad, 20)
        except ValueError:
            continue
        raise AssertionError(f"{bad!r} should raise ValueError")
