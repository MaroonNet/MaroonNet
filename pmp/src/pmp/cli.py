"""The ``pmp`` command. Phase 0 has one subcommand: ``pmp status``.

It prints what exists in the package, what each piece waits on, and the API surface, from the
architecture document ((P)MP Architecture v1.0 sections 8, 10, 12). Later phases add
``pmp serve`` or ``pmp daemon`` (PM-01 decides which) and ``pmp region``.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from pmp import SEGMENT, __version__
from pmp.api.surface import SURFACE

# module, state, waits on. Section 12 of the architecture document.
INVENTORY: tuple[tuple[str, str, str], ...] = (
    ("contract.messages", "record defined", "C-02 transport: R-03"),
    ("contract.mission_input", "record defined", "category set: R-07 with JJ"),
    ("contract.events", "record defined", "C-09 list: Open, answered on PR #5"),
    ("daemon.bridge", "stub", "M-01 acceptance; store meeting R-01, R-04; PM-01"),
    ("daemon.outbound", "stub", "C-07 (MCM writes)"),
    ("api.surface", "stub", "R-03 framework bake-off"),
    ("planning.sectors", "stub", "C-04, C-05; sector research"),
    ("planning.assignment", "stub", "C-09 list"),
    ("planning.spacing", "stub", "I-14 sweep widths; M-04 preset and interval (field test)"),
    ("planning.coverage", "stub", "C-06 split: R-08 with Diego"),
    ("maps.package", "manifest defined", "R-05, R-06; on-disk location A-04"),
    ("maps.region", "stub", "R-05; the owner's Planetiler run"),
    ("web/", "placeholder", "R-10 map library; A-05 replay home"),
)


def status(out=sys.stdout) -> int:
    """Print the inventory and the API surface."""
    print(
        f"MaroonNet {SEGMENT} package pmp {__version__}: phase 0, folders, docs, and stubs.",
        file=out,
    )
    print(file=out)
    print("Module                   State              Waits on", file=out)
    for module, state, waits in INVENTORY:
        print(f"{module:<24} {state:<18} {waits}", file=out)
    print(file=out)
    print("API surface (framework-neutral; R-03 picks the framework)", file=out)
    for name, kind, contract, note in SURFACE:
        print(f"{name:<18} {kind:<5} {contract:<12} {note}", file=out)
    print(file=out)
    print(
        "Nothing here is decided. See docs/architecture/maroonnet-pmp-architecture-v1_0.md.",
        file=out,
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the ``pmp`` command."""
    parser = argparse.ArgumentParser(prog="pmp", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="print what exists and what it waits on")
    args = parser.parse_args(argv)
    if args.command == "status":
        return status()
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
