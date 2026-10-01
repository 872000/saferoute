"""A* pathfinding with a safety-weighted edge cost.

Edge cost for stepping from block ``a`` to adjacent block ``b``:

    cost(a → b) = α · distance(a, b) + (1 − α) · (1 − safety(a, b))

α (alpha) is the user-facing safety↔distance tradeoff slider:
  α = 1.0 → shortest route (ignores safety)
  α = 0.0 → safest route (ignores distance)
  α = 0.5 → balances both

The heuristic h(n) = α · manhattan(n, goal) is admissible because the
safety term of every edge cost is non-negative, so A* returns the optimal
path for the chosen α.
"""

from __future__ import annotations

import heapq

from .city import GridCity


def edge_cost(city: GridCity, a, b, alpha: float) -> float:
    """Weighted cost of traversing one step a → b."""
    dist = city.edge_distance(a, b)
    safety = city.edge_safety(a, b)
    return alpha * dist + (1.0 - alpha) * (1.0 - safety)


def astar(city: GridCity, start, goal, alpha: float = 0.5):
    """Return the optimal path as a list of nodes [(r, c), ...].

    Raises ValueError if alpha ∉ [0, 1]. A* on a grid with non-negative
    edge costs always finds a path when one exists (grids are connected
    here, so it always terminates with a path).
    """
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha must be in [0, 1]")
    if start == goal:
        return [start]

    def h(n):
        return alpha * GridCity.manhattan(n, goal)

    open_heap = [(h(start), 0.0, start)]  # (f, g, node)
    g_score = {start: 0.0}
    came_from = {}
    closed = set()

    while open_heap:
        _, g, current = heapq.heappop(open_heap)
        if current in closed:
            continue
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            return path[::-1]
        closed.add(current)

        for nxt in city.neighbors(current):
            tentative = g + edge_cost(city, current, nxt, alpha)
            if tentative < g_score.get(nxt, float("inf")):
                g_score[nxt] = tentative
                came_from[nxt] = current
                heapq.heappush(open_heap, (tentative + h(nxt), tentative, nxt))

    raise RuntimeError("no path found (city grid should be fully connected)")


def route_stats(city: GridCity, path) -> dict:
    """Distance (blocks), average safety, and incident exposure of a path."""
    if len(path) < 2:
        return {"distance": 0, "avg_safety": city.block_safety(path[0]),
                "incidents": int(city.incidents[path[0]]), "steps": 0}

    total_dist = 0.0
    edge_safety_sum = 0.0
    incidents = 0
    for a, b in zip(path, path[1:]):
        total_dist += city.edge_distance(a, b)
        edge_safety_sum += city.edge_safety(a, b)
        incidents += int(city.incidents[a])
    incidents += int(city.incidents[path[-1]])

    n = len(path) - 1
    return {
        "distance": total_dist,
        "avg_safety": edge_safety_sum / n,
        "incidents": incidents,
        "steps": n,
    }
