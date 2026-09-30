"""The API surface: the endpoints and pushes the command post screen needs, as plain functions.

(P)MP Architecture v1.0 section 7.7. No framework is imported; R-03 is Research. Each function is
one call the screen makes. ``SURFACE`` lists them with the contract each one carries, so
``pmp status`` can print the surface and the bake-off can implement the same two calls in each
framework ((P)MP v1.1 section 6.2): one REST call (``mission_create``) and one push
(``push_subscribe``).

The AAR's replay questions (Q-01 to Q-05) are answered by ``aar.replay.queries``; whether the
AAR's endpoints live in this surface or beside it waits on R-03 and A-01
(AAR Architecture v1.0 section 8.2).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from pmp.contract.events import Event
from pmp.contract.messages import DaemonMessage
from pmp.contract.mission_input import MissionInput


def mission_create(inputs: MissionInput) -> dict[str, Any]:
    """Start a mission: create its store (C-01), write the ``mission`` started event, ping SPM."""
    raise NotImplementedError("waits on R-03 and the store meeting (R-01, R-02)")


def mission_end(mission_id: str) -> dict[str, Any]:
    """End a mission: write the ``mission`` ended event, close the store."""
    raise NotImplementedError("waits on R-03 and the store meeting (R-01, R-02)")


def surface_get(mission_id: str) -> dict[str, Any]:
    """The SPM probability surface for the mission, summed per sector (I-02, C-04)."""
    raise NotImplementedError("waits on C-04 (SPM writes)")


def sectors_get(mission_id: str) -> list[dict[str, Any]]:
    """The current sector versions (C-01 ``sector`` rows) as GeoJSON."""
    raise NotImplementedError("waits on C-01 and R-03")


def sectors_put(mission_id: str, sectors: Iterable[dict[str, Any]], reason: str | None) -> Event:
    """Replace sectors after an edit: new ``sector`` versions plus one ``edit`` or ``override``."""
    raise NotImplementedError("waits on C-09 and R-03")


def assignments_put(mission_id: str, assignments: Iterable[dict[str, Any]]) -> list[Event]:
    """Assign radios to people, teams, and sectors: one ``assignment`` event each (C-09)."""
    raise NotImplementedError("waits on C-09 and R-03")


def events_post(mission_id: str, event: Event) -> Event:
    """Write a commander event: clue, find, message out."""
    raise NotImplementedError("waits on C-09 and R-03")


def push_subscribe(
    mission_id: str, since_seq: int, deliver: Callable[[DaemonMessage], None]
) -> None:
    """Subscribe the screen to C-02 messages from ``since_seq`` on. Transport waits on R-03."""
    raise NotImplementedError("waits on R-03 (C-02 transport)")


def terrain_get(region: str, layer: str) -> bytes:
    """Serve one file of the terrain package (C-05) to the map library."""
    raise NotImplementedError("waits on C-05 and R-10")


# name, kind, contract or item, one line. Printed by ``pmp status``.
SURFACE: tuple[tuple[str, str, str, str], ...] = (
    ("mission_create", "REST", "C-03, C-01", "start a mission; ping SPM"),
    ("mission_end", "REST", "C-01, C-09", "end a mission"),
    ("surface_get", "REST", "C-04", "the heat map"),
    ("sectors_get", "REST", "C-01", "sector versions"),
    ("sectors_put", "REST", "C-09", "edit, split, merge; override"),
    ("assignments_put", "REST", "C-09", "radio to person to team to sector"),
    ("events_post", "REST", "C-09", "clue, find, message out"),
    ("push_subscribe", "push", "C-02", "live positions and alerts"),
    ("terrain_get", "REST", "C-05", "tiles, elevation, land cover"),
)
