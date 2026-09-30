"""Every module imports, every stub raises NotImplementedError, and ``pmp status`` runs."""

from __future__ import annotations

import importlib
import io
from pathlib import Path

import pytest

from pmp.contract.mission_input import LatLon
from pmp.planning.assignment import Assignment
from pmp.planning.sectors import Sector

MODULES = [
    "pmp",
    "pmp.cli",
    "pmp.contract",
    "pmp.contract.messages",
    "pmp.contract.mission_input",
    "pmp.contract.events",
    "pmp.daemon",
    "pmp.daemon.bridge",
    "pmp.daemon.outbound",
    "pmp.api",
    "pmp.api.surface",
    "pmp.planning",
    "pmp.planning.sectors",
    "pmp.planning.assignment",
    "pmp.planning.spacing",
    "pmp.planning.coverage",
    "pmp.maps",
    "pmp.maps.package",
    "pmp.maps.region",
]


@pytest.mark.parametrize("name", MODULES)
def test_module_imports(name: str) -> None:
    module = importlib.import_module(name)
    assert module.__doc__, f"{name} has no module docstring"


def _sector() -> Sector:
    return Sector("S1", 1, {"type": "Polygon", "coordinates": []}, "2026-10-01T00:00:00Z")


def _assignment() -> Assignment:
    return Assignment(1, "Searcher A", "Team 1", "S1", "2026-10-01T00:00:00Z")


def _stubs() -> list[tuple[str, object, tuple]]:
    from pmp.api import surface
    from pmp.contract import events
    from pmp.daemon import bridge, outbound
    from pmp.maps import package, region
    from pmp.planning import assignment, coverage, sectors, spacing

    b = bridge.Bridge(store=None, push=lambda m: None)
    return [
        ("bridge.row_from_record", bridge.row_from_record, ({},)),
        ("Bridge.on_record", b.on_record, ({},)),
        ("Bridge.stop", b.stop, ()),
        ("Bridge.on_quiet", b.on_quiet, (1, "2026-10-01T00:00:00Z", 180.0)),
        ("outbound.send_text", outbound.send_text, (None, "hello")),
        ("outbound.send_waypoint", outbound.send_waypoint, (None, "CP", 39.0, -105.0)),
        ("surface.mission_end", surface.mission_end, ("m1",)),
        ("surface.surface_get", surface.surface_get, ("m1",)),
        ("surface.sectors_get", surface.sectors_get, ("m1",)),
        ("surface.sectors_put", surface.sectors_put, ("m1", [], None)),
        ("surface.assignments_put", surface.assignments_put, ("m1", [])),
        ("surface.push_subscribe", surface.push_subscribe, ("m1", 0, lambda m: None)),
        ("surface.terrain_get", surface.terrain_get, ("r1", "basemap")),
        ("events.dispatch_time_s", events.dispatch_time_s, ([],)),
        ("sectors.generate_sectors", sectors.generate_sectors, (None, None)),
        ("sectors.split_sector", sectors.split_sector, (_sector(), {}, "2026-10-01T00:00:00Z")),
        ("sectors.merge_sectors", sectors.merge_sectors, (_sector(), _sector(), "t")),
        ("sectors.sum_surface_per_sector", sectors.sum_surface_per_sector, (None, [])),
        ("assignment.assign", assignment.assign, (_assignment(),)),
        ("assignment.unassign", assignment.unassign, (_assignment(), "t")),
        ("assignment.current_assignments", assignment.current_assignments, ([], "t")),
        ("spacing.radio_spacing", spacing.radio_spacing, (6, 6, 7)),
        (
            "coverage.planned_coverage",
            coverage.planned_coverage,
            ([LatLon(39.0, -105.0)], None, None),
        ),
        ("package.write_manifest", package.write_manifest, (None, Path("."))),
        ("package.read_manifest", package.read_manifest, (Path("."),)),
        ("region.select_region", region.select_region, ("r", (0.0, 0.0, 1.0, 1.0), 25.0)),
        ("region.build_basemap", region.build_basemap, (None, Path("a"), Path("b"))),
        ("region.fetch_elevation", region.fetch_elevation, (None, Path("a"))),
        ("region.fetch_landcover", region.fetch_landcover, (None, Path("a"))),
    ]


STUBS = _stubs()


@pytest.mark.parametrize("label,func,args", STUBS, ids=[s[0] for s in STUBS])
def test_stub_raises_not_implemented(label: str, func, args: tuple) -> None:
    with pytest.raises(NotImplementedError) as info:
        func(*args)
    assert str(info.value), f"{label} raises with no reason"


def test_bridge_run_is_a_coroutine_stub() -> None:
    import asyncio

    from pmp.daemon.bridge import Bridge

    b = Bridge(store=None, push=lambda m: None)
    with pytest.raises(NotImplementedError):
        asyncio.run(b.run(gateway=None))


def test_as_mapping_takes_a_dataclass_or_a_dict() -> None:
    from dataclasses import dataclass

    from pmp.daemon.bridge import as_mapping

    @dataclass(frozen=True)
    class Rec:
        schema: str
        seq: int

    assert as_mapping(Rec("mcm.radio_record/0.1-draft", 3)) == {
        "schema": "mcm.radio_record/0.1-draft",
        "seq": 3,
    }
    assert as_mapping({"schema": "x", "seq": 1}) == {"schema": "x", "seq": 1}


def test_cli_status_runs() -> None:
    from pmp.cli import main, status

    out = io.StringIO()
    assert status(out) == 0
    text = out.getvalue()
    assert "phase 0" in text
    assert "push_subscribe" in text
    assert main(["status"]) == 0
