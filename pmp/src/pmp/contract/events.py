"""The event record: what (P)MP writes to the timeline, with time.

This is (P)MP's side of contract C-09 ((P)MP Architecture v1.0 section 6.4). (P)MP writes; AAR
signs; blocked by C-01. The type list mirrors the AAR's proposal in AAR Architecture v1.0
section 6.3. Whether that list is the right set is Open; the owner answers on pull request #5.
The list is here so the daemon and the planning code have a name for each type meanwhile.

The record lines up with the C-01 draft ``event`` table (aar/src/aar/store/schema.sql): event
time, event type, optional node, optional sector, JSON payload. The AAR's insert helper
``aar.store.db.insert_event`` takes the same fields.

An override stores what the system proposed, what the commander did instead, the time, and a
short reason if given (Team answer, (P)MP v1.1 section 6.5). The time from case entry to first team
dispatch is a query over these events, from the ``mission`` started event to the first
``assignment`` event (PM-05).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

EVENT_SCHEMA = "pmp.event/0.1-draft"

# AAR Architecture v1.0 section 6.3, in its order. Open.
EVENT_TYPES = (
    "assignment",
    "edit",
    "override",
    "message",
    "clue",
    "find",
    "gap",
    "mission",
    "note",
)

# The types (P)MP writes. The daemon writes ``message`` for inbound text and ``gap`` if A-02
# chooses stored gaps. ``note`` is the AAR's, if the AAR writes at all (Open).
PMP_WRITES = ("assignment", "edit", "override", "message", "clue", "find", "mission")

MISSION_STATES = ("started", "paused", "ended")


@dataclass(frozen=True)
class Event:
    """One timeline event, in the shape of the C-01 draft ``event`` row."""

    event_type: str
    event_time: str  # UTC ISO-8601 ending in "Z"
    node_num: int | None = None
    sector_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    schema: str = EVENT_SCHEMA

    def __post_init__(self) -> None:
        if self.event_type not in EVENT_TYPES:
            raise ValueError(
                f"unknown event type {self.event_type!r}; expected one of {EVENT_TYPES}"
            )
        if self.schema != EVENT_SCHEMA:
            raise ValueError(f"schema {self.schema!r} is not {EVENT_SCHEMA!r}")

    def to_dict(self) -> dict[str, Any]:
        """The event as a JSON-safe dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Event:
        """Rebuild an event from ``to_dict`` output."""
        return cls(**data)

    def to_json(self) -> str:
        """One line of JSON, keys sorted."""
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, line: str) -> Event:
        """Parse one line written by ``to_json``."""
        return cls.from_dict(json.loads(line))


@dataclass(frozen=True)
class OverridePayload:
    """The payload of an ``override`` event ((P)MP v1.1 section 6.5)."""

    proposed: dict[str, Any]  # what the system proposed
    actual: dict[str, Any]  # what the commander did instead
    reason: str | None = None  # a short reason, if given

    def to_dict(self) -> dict[str, Any]:
        """The payload as a JSON-safe dict, for ``Event.payload``."""
        return asdict(self)


def dispatch_time_s(events: list[Event]) -> float | None:
    """Seconds from the ``mission`` started event to the first ``assignment`` event (PM-05).

    Returns None when either event is missing. The measurement the team wants ((P)MP v1.1
    section 3.8), as a query over the timeline rather than a separate log.
    """
    raise NotImplementedError("PM-05 dispatch-time query; waits on the C-09 list (section 6.4)")
