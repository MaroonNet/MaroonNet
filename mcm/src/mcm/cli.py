"""mcm: command line for the Mesh Connectivity Map package.

    mcm airtime [--nodes 5 10 20] [--interval 60 120] [--preset LONG_FAST MEDIUM_FAST]
    mcm synth   [--out data/synthetic/feed.jsonl --nodes 6 --hours 1 --interval 60 --seed 7]
    mcm inspect data/synthetic/feed.jsonl [--interval 60 --gap-factor 3]
    mcm profile

airtime prints the channel utilization table (MCM v1.1 section 6.1). synth writes a synthetic
radio feed as JSON Lines. inspect summarizes a feed and lists its out-of-range gaps. profile prints
the radio profile and whether the firmware is pinned.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from mcm import __version__
from mcm.contract.record import read_jsonl, write_jsonl
from mcm.mesh import airtime, gaps
from mcm.radio import profile as profile_mod
from mcm.sim import synthetic


def cmd_airtime(args: argparse.Namespace) -> int:
    presets = args.preset
    head = f"{'nodes':>5} {'interval':>8}  " + "  ".join(f"{p:>14}" for p in presets)
    print(head)
    for n in args.nodes:
        for i in args.interval:
            cells = []
            for p in presets:
                u = airtime.utilization(n, i, p, args.payload, args.transmissions)
                cells.append(f"{u * 100:5.1f}% {airtime.status(u):>8}")
            print(f"{n:>5} {i:>7}s  " + "  ".join(cells))
    print()
    for p in presets:
        t = airtime.time_on_air_s(p, args.payload)
        print(f"{p}: {t * 1000:.0f} ms per {args.payload}-byte packet")
    return 0


def cmd_synth(args: argparse.Namespace) -> int:
    out = Path(args.out)
    if out.exists():
        print(f"refusing to overwrite {out}", file=sys.stderr)
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        n = write_jsonl(
            synthetic.records(
                n_nodes=args.nodes, hours=args.hours, interval_s=args.interval, seed=args.seed
            ),
            fh,
        )
    print(f"wrote {out}: {n} records")
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    recs = list(read_jsonl(args.path))
    kinds = Counter(r.kind for r in recs)
    nodes = {r.header.from_node for r in recs}
    direct = sum(1 for r in recs if r.header.heard_directly)
    no_fix = sum(1 for r in recs if r.position is not None and r.position.device_time is None)
    print(f"{len(recs)} records from {len(nodes)} radios")
    print("kinds: " + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())))
    print(f"heard directly: {direct}; positions with no device time: {no_fix}")
    found = gaps.find_gaps(recs, args.interval * args.gap_factor)
    print(f"gaps over {args.interval * args.gap_factor:.0f} s: {len(found)}")
    for g in found:
        print(f"  node {g.node:#010x}  {g.last_heard} -> {g.next_heard}  {g.seconds / 60:.1f} min")
    return 0


def cmd_profile(args: argparse.Namespace) -> int:
    p = profile_mod.load(args.path) if args.path else profile_mod.load()
    for k, v in vars(p).items():
        print(f"{k:>22}: {v!r}")
    print(f"{'firmware pinned':>22}: {p.is_pinned}")
    print(f"{'gap threshold':>22}: {p.gap_threshold_s:.0f} s")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="mcm", description="MaroonNet Mesh Connectivity Map")
    ap.add_argument("--version", action="version", version=f"mcm {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("airtime", help="channel utilization table")
    a.add_argument("--nodes", type=int, nargs="+", default=[5, 10, 20])
    a.add_argument("--interval", type=int, nargs="+", default=[60, 120, 180])
    a.add_argument("--preset", nargs="+", default=["LONG_FAST", "MEDIUM_FAST"])
    a.add_argument("--payload", type=int, default=50)
    a.add_argument("--transmissions", type=float, default=3)
    a.set_defaults(func=cmd_airtime)

    s = sub.add_parser("synth", help="write a synthetic radio feed")
    s.add_argument("--out", default="data/synthetic/feed.jsonl")
    s.add_argument("--nodes", type=int, default=6)
    s.add_argument("--hours", type=float, default=1.0)
    s.add_argument("--interval", type=int, default=60)
    s.add_argument("--seed", type=int, default=7)
    s.set_defaults(func=cmd_synth)

    i = sub.add_parser("inspect", help="summarize a feed and list its gaps")
    i.add_argument("path")
    i.add_argument("--interval", type=int, default=60)
    i.add_argument("--gap-factor", type=float, default=3.0)
    i.set_defaults(func=cmd_inspect)

    p = sub.add_parser("profile", help="print the radio profile")
    p.add_argument("--path", default=None)
    p.set_defaults(func=cmd_profile)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
