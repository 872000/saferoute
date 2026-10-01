"""A* correctness on a tiny hand-verifiable grid.

On a 3×3 grid with α=1 (distance-only cost), every step costs exactly 1,
so the optimal route from (0,0) to (2,2) must be a 4-step Manhattan path
(5 nodes). Any optimal path is hand-verifiable: it must start at the
start, end at the goal, move only to 4-neighbours, and have total
distance exactly 4.
"""

from saferoute.city import GridCity
from saferoute.pathfinding import astar, edge_cost, route_stats


def _adjacent(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


def test_astar_finds_optimal_path_on_tiny_grid():
    city = GridCity(size=3, seed=1)
    start, goal = (0, 0), (2, 2)
    path = astar(city, start, goal, alpha=1.0)

    assert path[0] == start
    assert path[-1] == goal
    assert all(_adjacent(a, b) for a, b in zip(path, path[1:]))
    stats = route_stats(city, path)
    assert stats["distance"] == 4  # Manhattan distance: provably optimal
    assert stats["steps"] == 4
    assert len(path) == 5


def test_edge_cost_matches_cost_model():
    city = GridCity(size=3, seed=1)
    city.safety[:] = 1.0
    city.safety[1, 1] = 0.0
    a, b = (1, 0), (1, 1)
    # edge safety = (1 + 0) / 2 = 0.5
    assert edge_cost(city, a, b, alpha=1.0) == 1.0          # pure distance
    assert edge_cost(city, a, b, alpha=0.0) == 0.5          # pure safety
    assert edge_cost(city, a, b, alpha=0.5) == 0.5 * 1 + 0.5 * 0.5


def test_astar_rejects_bad_alpha():
    city = GridCity(size=3, seed=1)
    for bad in (-0.1, 1.5):
        try:
            astar(city, (0, 0), (1, 1), alpha=bad)
        except ValueError:
            continue
        raise AssertionError(f"alpha={bad} should raise ValueError")


def test_astar_start_equals_goal():
    city = GridCity(size=3, seed=1)
    assert astar(city, (1, 1), (1, 1), alpha=0.3) == [(1, 1)]
