"""Regression test: plot_route_map fails loudly on an empty paths dict.

Without the guard, _draw_paths hit ``next(iter(paths.values()))`` on an
empty dict and died with a bare StopIteration — a confusing traceback for
a caller mistake.
"""

import pytest

from saferoute.city import GridCity
from saferoute.viz import plot_route_map


def test_plot_route_map_rejects_empty_paths(tmp_path):
    city = GridCity(size=3, seed=1)
    with pytest.raises(ValueError, match="at least one path"):
        plot_route_map(city, {}, str(tmp_path / "empty.png"))
