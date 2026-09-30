"""aar: command line for the After Action Report package.

    aar synth   --out data/synthetic/mission.sqlite [--nodes 10 --hours 6 --interval 60 --seed 7]
    aar summary data/synthetic/mission.sqlite

synth writes a synthetic mission store. summary prints what a store holds and its gaps.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from aar import __version__, synthetic
from aar.replay import gaps
from aar.store import db


def cmd_synth(args: argparse.Namespace) -> int:
    out = Path(args.out)
    con = db.create(
        out,
        mission_id=out.stem,
        name=f"synthetic {args.nodes}x{args.hours}h@{args.interval}s",
        started_at="2026-10-03T14:00:00Z",
    )
    s = synthetic.generate(
        con, n_nodes=args.nodes, hours=args.hours, interval_s=args.interval, seed=args.seed
    )
    con.close()
    print(
        f"wrote {out}: {s.nodes} nodes, {s.positions} positions "
        f"({s.positions_without_fix} without a fix), {s.telemetry} telemetry, "
        f"{s.events} events, {s.started_at} to {s.ended_at}"
    )
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    con = db.connect(args.store)
    m = con.execute("SELECT * FROM mission").fetchone()
    n_nodes = con.execute("SELECT count(*) FROM node").fetchone()[0]
    n_pos, n_nofix = con.execute(
        "SELECT count(*), sum(device_time IS NULL) FROM position"
    ).fetchone()
    n_pkt = con.execute("SELECT count(*) FROM packet").fetchone()[0]
    n_evt = con.execute("SELECT count(*) FROM event").fetchone()[0]
    g = gaps(con, threshold_s=args.gap_threshold)
    print(f"mission   {m['mission_id']}  '{m['name']}'  schema {m['schema_ver']}")
    print(f"time      {m['started_at']} to {m['ended_at'] or '(open)'}")
    print(f"nodes     {n_nodes}")
    print(f"packets   {n_pkt}   positions {n_pos} ({n_nofix or 0} without a fix)   events {n_evt}")
    print(f"gaps      {len(g)} over {args.gap_threshold:.0f} s")
    for row in g[: args.show]:
        print(
            f"          node {row['node_num']:#x}  {row['last_heard']} -> {row['next_heard']}"
            f"  {row['gap_s']:.0f} s"
        )
    con.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="aar", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--version", action="version", version=f"aar {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("synth", help="write a synthetic mission store")
    p.add_argument("--out", default="data/synthetic/mission.sqlite")
    p.add_argument("--nodes", type=int, default=10)
    p.add_argument("--hours", type=float, default=6.0)
    p.add_argument("--interval", type=int, default=60, help="position interval in seconds")
    p.add_argument("--seed", type=int, default=7)
    p.set_defaults(fn=cmd_synth)

    p = sub.add_parser("summary", help="print what a mission store holds")
    p.add_argument("store")
    p.add_argument("--gap-threshold", type=float, default=300.0, help="seconds; default 300")
    p.add_argument("--show", type=int, default=10, help="how many gaps to list")
    p.set_defaults(fn=cmd_summary)

    args = ap.parse_args(argv)
    return int(args.fn(args))


if __name__ == "__main__":
    sys.exit(main())
