"""Matplotlib visualizations: city safety heatmap with route overlays."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # headless-safe PNG rendering
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch

from .city import GridCity

# red (dangerous) → yellow → green (safe)
SAFETY_CMAP = LinearSegmentedColormap.from_list(
    "safety", ["#d73027", "#fee08b", "#1a9850"]
)


def _draw_paths(ax, paths: dict, city: GridCity):
    styles = {
        "safest": {"color": "#1a9850", "lw": 3.0, "ls": "-", "label": "safest route (α=0)"},
        "shortest": {"color": "#2166ac", "lw": 3.0, "ls": "--", "label": "shortest route (α=1)"},
        "balanced": {"color": "#88419d", "lw": 3.0, "ls": ":", "label": "balanced route (α=0.5)"},
    }
    for key, path in paths.items():
        if not path:
            continue
        ys = [r + 0.5 for r, _ in path]
        xs = [c + 0.5 for _, c in path]
        st = styles.get(key, styles["balanced"])
        ax.plot(xs, ys, **{k: v for k, v in st.items() if k != "label"},
                label=st["label"], zorder=5)
    # start / end markers
    any_path = next(iter(paths.values()))
    ax.scatter([any_path[0][1] + 0.5], [any_path[0][0] + 0.5], c="black",
               s=120, marker="o", edgecolors="white", linewidths=2,
               zorder=6, label=f"start {city.label(any_path[0])}")
    ax.scatter([any_path[-1][1] + 0.5], [any_path[-1][0] + 0.5], c="black",
               s=120, marker="*", edgecolors="white", linewidths=2,
               zorder=6, label=f"end {city.label(any_path[-1])}")


def plot_route_map(city: GridCity, paths: dict, out_path: str,
                   title: str = "SafeRoute — safety heatmap with route overlay"):
    """Save a PNG: safety heatmap of the city with route(s) drawn on top.

    ``paths`` maps a name ('safest', 'shortest', 'balanced', or a custom
    'route') to a list of (r, c) nodes.
    """
    fig, ax = plt.subplots(figsize=(9, 9))
    im = ax.imshow(city.safety, cmap=SAFETY_CMAP, vmin=0.0, vmax=1.0,
                   origin="upper")
    _draw_paths(ax, paths, city)

    n = city.size
    ax.set_xlim(0, n)
    ax.set_ylim(n, 0)
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels([str(c + 1) for c in range(n)], fontsize=7)
    ax.set_yticklabels([chr(ord("A") + r) for r in range(n)], fontsize=7)
    ax.grid(True, color="white", linewidth=0.4, alpha=0.6)
    ax.set_title(title, fontsize=14, pad=12)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("block safety score (0 = risky, 1 = safe)")

    ax.legend(loc="lower left", fontsize=9, framealpha=0.95, edgecolor="white")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path
