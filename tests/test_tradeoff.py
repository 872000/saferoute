"""The α=0 (safest) vs α=1 (shortest) tradeoff on a designed map.

Designed map (3 rows × 5 cols). Walking from (1,0) to (1,4) down the
middle row is the shortest route (4 steps) but passes through an unsafe
stretch (row 1, cols 1–3 have safety 0; everything else has safety 1).

  α = 1 → must take the 4-step straight route through the unsafe zone.
  α = 0 → must take the 6-step detour along the safe top row.

This proves the safety slider genuinely changes the chosen route.
"""

import numpy as np

from saferoute.city import GridCity
from saferoute.pathfinding import astar, route_stats

STRAIGHT = [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4)]
DETOUR = [(1, 0), (0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 4)]


def _designed_city() -> GridCity:
    city = GridCity(size=5, seed=99)  # 5×5, we only use the top 3 rows
    city.safety[:] = 1.0
    city.safety[1, 1] = 0.0
    city.safety[1, 2] = 0.0
    city.safety[1, 3] = 0.0
    return city


def test_alpha_one_picks_shortest_route_through_unsafe_zone():
    city = _designed_city()
    path = astar(city, (1, 0), (1, 4), alpha=1.0)
    assert path == STRAIGHT
    assert route_stats(city, path)["distance"] == 4


def test_alpha_zero_picks_safe_detour():
    city = _designed_city()
    path = astar(city, (1, 0), (1, 4), alpha=0.0)
    assert path == DETOUR
    stats = route_stats(city, path)
    assert stats["distance"] == 6
    assert stats["avg_safety"] == 1.0  # the detour is perfectly safe


def test_safety_weight_changes_the_chosen_path():
    city = _designed_city()
    shortest = astar(city, (1, 0), (1, 4), alpha=1.0)
    safest = astar(city, (1, 0), (1, 4), alpha=0.0)
    assert shortest != safest
    s_short = route_stats(city, shortest)
    s_safe = route_stats(city, safest)
    # tradeoff: safer route is longer, shortest route is less safe
    assert s_safe["distance"] > s_short["distance"]
    assert s_safe["avg_safety"] > s_short["avg_safety"]


def test_mid_alpha_still_respects_safety():
    # α=0.5 on the designed map, hand-computed:
    #   straight: 0.75 + 1.0 + 1.0 + 0.75 = 3.50
    #   detour:   6 × 0.5 = 3.00
    # → the safe detour still wins; the tradeoff degrades gracefully.
    city = _designed_city()
    path = astar(city, (1, 0), (1, 4), alpha=0.5)
    assert path == DETOUR
