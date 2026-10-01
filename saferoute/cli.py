"""SafeRoute command-line interface.

Commands:
    route    --from A --to B --safety 0.8 [--seed N]   compute one route
    compare  --from A --to B [--seed N]                safest vs shortest side by side
    sos      --at C [--seed N]                         simulate the SOS contact cascade
    demo                                               bundled end-to-end demo
"""

from __future__ import annotations

import argparse
import os
import sys

from . import __version__
from .city import GridCity
from .pathfinding import astar, route_stats
from .sos import DEFAULT_CONTACTS, trigger_sos
from .viz import plot_route_map

CITY_SIZE = 20
DEFAULT_SEED = 42
DEMO_SEED = 49  # chosen so the safest route visibly detours around risk
DEMO_START, DEMO_END = "A1", "T20"
DEMO_SAFETY = 0.85  # safety-first: α = 1 − 0.85 = 0.15
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")


def build_city(seed: int) -> GridCity:
    return GridCity(size=CITY_SIZE, seed=seed)


def _fmt_stats(stats: dict) -> str:
    return (f"distance: {stats['distance']:.0f} blocks | "
            f"avg safety: {stats['avg_safety']:.2f}/1.00 | "
            f"incident exposure: {stats['incidents']} past incidents along route")


def _path_labels(city: GridCity, path) -> str:
    return " → ".join(city.label(n) for n in path)


def cmd_route(args) -> int:
    city = build_city(args.seed)
    # --safety 0..1: 1 = safest, 0 = shortest → alpha = 1 - safety
    alpha = 1.0 - args.safety
    start = GridCity.parse_label(args.from_, CITY_SIZE)
    end = GridCity.parse_label(args.to, CITY_SIZE)
    path = astar(city, start, end, alpha=alpha)
    stats = route_stats(city, path)

    print(f"SafeRoute v{__version__} — safety preference {args.safety:.2f} "
          f"(α={alpha:.2f})")
    print(f"Route {city.label(start)} → {city.label(end)} "
          f"({len(path)} blocks visited)")
    print(_fmt_stats(stats))
    print("Path: " + _path_labels(city, path))

    out = os.path.join(ASSETS_DIR, "route.png")
    os.makedirs(ASSETS_DIR, exist_ok=True)
    plot_route_map(city, {"route": path}, out,
                   title=(f"SafeRoute route {city.label(start)} → "
                          f"{city.label(end)} (safety pref. {args.safety:.2f})"))
    print(f"Map saved → {out}")
    return 0


def cmd_compare(args) -> int:
    city = build_city(args.seed)
    start = GridCity.parse_label(args.from_, CITY_SIZE)
    end = GridCity.parse_label(args.to, CITY_SIZE)

    safest = astar(city, start, end, alpha=0.0)
    shortest = astar(city, start, end, alpha=1.0)
    s_safest, s_shortest = route_stats(city, safest), route_stats(city, shortest)

    print(f"Safest route   (α=0): {_fmt_stats(s_safest)}")
    print(f"Shortest route (α=1): {_fmt_stats(s_shortest)}")
    print()
    extra = s_safest["distance"] - s_shortest["distance"]
    safer = s_safest["avg_safety"] - s_shortest["avg_safety"]
    print(f"The safest route is {extra:.0f} blocks longer but "
          f"{safer:+.2f} safer on average.")

    out = os.path.join(ASSETS_DIR, "compare.png")
    os.makedirs(ASSETS_DIR, exist_ok=True)
    plot_route_map(city, {"safest": safest, "shortest": shortest}, out,
                   title=(f"SafeRoute: safest vs shortest "
                          f"({city.label(start)} → {city.label(end)})"))
    print(f"Map saved → {out}")
    return 0


def cmd_sos(args) -> int:
    city = build_city(args.seed)
    location = GridCity.parse_label(args.at, CITY_SIZE)
    trigger_sos(city, location, contacts=DEFAULT_CONTACTS,
                seed=args.seed, wait_seconds=args.wait)
    return 0


def cmd_demo(args) -> int:
    print("=" * 52)
    print("  SafeRoute — bundled demo")
    print("  Fixed map (seed 49), A1 → T20, safety-first routing")
    print("=" * 52)
    print()
    print("### 1. Safety-first route (safety 0.85)")
    rc = cmd_route(argparse.Namespace(from_=DEMO_START, to=DEMO_END,
                                      safety=DEMO_SAFETY, seed=DEMO_SEED))
    print()
    print("### 2. Safest vs shortest comparison")
    rc = cmd_compare(argparse.Namespace(from_=DEMO_START, to=DEMO_END,
                                        seed=DEMO_SEED)) or rc
    print()
    print("### 3. SOS simulation from block J10")
    rc = cmd_sos(argparse.Namespace(at="J10", seed=DEMO_SEED,
                                    wait=0.15)) or rc
    print()
    print("Demo complete — see assets/ for the generated route maps.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="saferoute",
                                description="Route for safety, not just distance.")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    pr = sub.add_parser("route", help="compute one route with a safety preference")
    pr.add_argument("--from", dest="from_", required=True, help="start block, e.g. A1")
    pr.add_argument("--to", dest="to", required=True, help="destination block, e.g. T20")
    pr.add_argument("--safety", type=float, default=0.5,
                    help="safety preference 0 (shortest) … 1 (safest)")
    pr.add_argument("--seed", type=int, default=DEFAULT_SEED)
    pr.set_defaults(func=cmd_route)

    pc = sub.add_parser("compare", help="safest vs shortest, side by side")
    pc.add_argument("--from", dest="from_", required=True)
    pc.add_argument("--to", dest="to", required=True)
    pc.add_argument("--seed", type=int, default=DEFAULT_SEED)
    pc.set_defaults(func=cmd_compare)

    ps = sub.add_parser("sos", help="simulate the SOS contact cascade")
    ps.add_argument("--at", default="J10", help="current block, e.g. J10")
    ps.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ps.add_argument("--wait", type=float, default=0.4,
                    help="simulated seconds spent waiting per contact")
    ps.set_defaults(func=cmd_sos)

    pd = sub.add_parser("demo", help="run the bundled end-to-end demo")
    pd.set_defaults(func=cmd_demo)

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "safety", None) is not None and not 0.0 <= args.safety <= 1.0:
        parser.error("--safety must be in [0, 1]")
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
