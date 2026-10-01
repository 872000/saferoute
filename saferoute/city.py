"""Grid-city model with seeded synthetic safety features.

Each block of an N×N grid carries three per-block features:
  - lighting level (0..1): how well lit the streets are
  - foot-traffic level (0..1): how many people are typically around
  - incident history (count): reported safety incidents over the past year

These combine into a per-block safety score in [0, 1]. Generation is seeded,
so any (seed, size) pair always produces the same map.
"""

from __future__ import annotations

import math

import numpy as np


class GridCity:
    """An N×N grid city with synthetic, reproducible safety features."""

    # Weights for the per-block safety score.
    W_LIGHTING = 0.45
    W_FOOT_TRAFFIC = 0.35
    W_INCIDENT_FREE = 0.20
    MAX_INCIDENTS = 5  # normalization cap for incident history

    def __init__(self, size: int = 20, seed: int = 42):
        if size < 2:
            raise ValueError("city size must be >= 2")
        self.size = size
        self.seed = seed
        self._rng = np.random.default_rng(seed)
        self.lighting = np.zeros((size, size))
        self.foot_traffic = np.zeros((size, size))
        self.incidents = np.zeros((size, size), dtype=int)
        self.safety = np.zeros((size, size))
        self._generate()

    # ------------------------------------------------------------------
    # generation
    # ------------------------------------------------------------------
    def _smooth_field(self, base: float, jitter: float, hotspots: int) -> np.ndarray:
        """A spatially-correlated random field: smooth background + hotspots."""
        field = base + self._rng.normal(0, jitter, size=(self.size, self.size))
        for _ in range(hotspots):
            cx = self._rng.integers(0, self.size)
            cy = self._rng.integers(0, self.size)
            radius = self._rng.integers(2, 5)
            strength = self._rng.uniform(0.3, 0.7) * self._rng.choice([-1.0, 1.0])
            yy, xx = np.mgrid[0 : self.size, 0 : self.size]
            dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
            field += strength * np.exp(-(dist ** 2) / (2 * radius ** 2))
        return np.clip(field, 0.0, 1.0)

    def _generate(self) -> None:
        # Smooth feature fields with pockets of good/bad areas.
        self.lighting = self._smooth_field(base=0.65, jitter=0.15, hotspots=6)
        self.foot_traffic = self._smooth_field(base=0.55, jitter=0.18, hotspots=6)

        # Incident history: Poisson noise, spikier where dark & empty.
        lam = 1.2 + 2.5 * (1.0 - self.lighting) * (1.0 - self.foot_traffic)
        self.incidents = np.clip(self._rng.poisson(lam), 0, self.MAX_INCIDENTS)

        incident_free = 1.0 - self.incidents / self.MAX_INCIDENTS
        self.safety = (
            self.W_LIGHTING * self.lighting
            + self.W_FOOT_TRAFFIC * self.foot_traffic
            + self.W_INCIDENT_FREE * incident_free
        )
        self.safety = np.clip(self.safety, 0.0, 1.0)

    # ------------------------------------------------------------------
    # accessors
    # ------------------------------------------------------------------
    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.size and 0 <= c < self.size

    def neighbors(self, node):
        """4-connected neighbours: (up, down, left, right)."""
        r, c = node
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if self.in_bounds(nr, nc):
                yield (nr, nc)

    def block_safety(self, node) -> float:
        return float(self.safety[node])

    def edge_safety(self, a, b) -> float:
        """Safety of traversing from block a to adjacent block b."""
        return (self.block_safety(a) + self.block_safety(b)) / 2.0

    def edge_distance(self, a, b) -> float:
        """Distance of one grid step (1 block)."""
        return 1.0

    @staticmethod
    def manhattan(a, b) -> float:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    # ------------------------------------------------------------------
    # human-friendly block labels: rows A..T, cols 1..20  →  "A1".."T20"
    # ------------------------------------------------------------------
    def label(self, node) -> str:
        r, c = node
        return f"{chr(ord('A') + r)}{c + 1}"

    @classmethod
    def parse_label(cls, label: str, size: int):
        """Parse 'A1'.. into (row, col). Raises ValueError on bad input."""
        label = label.strip().upper()
        if len(label) < 2 or not label[0].isalpha():
            raise ValueError(f"bad block label: {label!r} (expected like 'A1')")
        r = ord(label[0]) - ord("A")
        try:
            c = int(label[1:]) - 1
        except ValueError:
            raise ValueError(f"bad block label: {label!r} (expected like 'A1')")
        if not (0 <= r < size and 0 <= c < size):
            raise ValueError(f"block {label!r} is outside the {size}×{size} city")
        return (r, c)

    def __repr__(self):  # pragma: no cover
        return f"GridCity(size={self.size}, seed={self.seed})"
