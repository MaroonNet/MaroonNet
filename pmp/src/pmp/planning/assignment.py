"""Assignment: radio to person to team to sector.

(P)MP Architecture v1.0 section 7.3. The team assumes one radio per person but does not know how
SAR teams structure themselves; prepare for both: pair a radio to a named searcher and to a team
(Team answer, (P)MP v1.1 section 3.4). An assignment leaves as a C-09 ``assignment`` event with
node, team, person label, sector, and start or end. AAR Architecture v1.0 A-06 proposes no
person-name column on the ``node`` table; the label lives in the event payload. How SAR teams
assign people and radios is Research (section 13).
"""

from __future__ import annotations

from dataclasses import dataclass

from pmp.contract.events import Event


@dataclass(frozen=True)
class Assignment:
    """One radio's assignment at one time."""

    node_num: int  # Meshtastic node number
    person_label: str | None  # a name or a call sign; never a phone or email
    team: str | None
    sector_id: str | None
    start: str  # UTC ISO-8601 ending in "Z"
    end: str | None = None


def assign(assignment: Assignment) -> Event:
    """Turn one assignment into its C-09 ``assignment`` event (payload per AAR section 6.3)."""
    raise NotImplementedError("assignment event; waits on the C-09 list (section 6.4)")


def unassign(assignment: Assignment, at: str) -> Event:
    """End one assignment: the same event type with ``end`` set."""
    raise NotImplementedError("assignment event; waits on the C-09 list (section 6.4)")


def current_assignments(events: list[Event], at: str) -> list[Assignment]:
    """The assignments in force at time ``at``, replayed from the events (AAR Q-07 asks this)."""
    raise NotImplementedError("assignment replay; waits on the C-09 list (section 6.4)")
