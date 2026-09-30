"""The mission input record: what the commander enters, as one typed record SPM accepts.

This is (P)MP's draft of contract C-03 ((P)MP Architecture v1.0 section 6.1, item PM-03),
co-written with SPM. The field list is a Team answer ((P)MP v1.1 section 3.3). The subject
category values are Open (R-07); the raised identifiers ride along as flags until the set is agreed.

The no-known-position case is required, not optional. It is the only way to get an answer from the
model, so the record must be able to say "no position, N hours elapsed" (Team answer).

Coordinates are WGS84 decimal degrees, (lat, lon), floats (CLAUDE.md). SPM's ``Case`` uses
``LonLat``; the mapping in ``to_case_fields`` swaps the order.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

INPUT_SCHEMA = "pmp.mission_input/0.1-draft"

# SPM's ipp_type terms (spm/src/spm/schema.py): point last seen, last known point, route, unknown.
LKP_KINDS = ("pls", "lkp", "route", "unknown")

# Raised on September 17, 2026 as identifiers beyond child and adult. Whether they are categories
# or flags is Open (R-07, I-04).
SUBJECT_IDENTIFIERS = ("group", "disabled", "infirm", "dog")


@dataclass(frozen=True)
class LatLon:
    """WGS84 latitude and longitude in decimal degrees."""

    lat: float
    lon: float


@dataclass(frozen=True)
class MissionInput:
    """One submission of the mission input form."""

    mission_id: str
    entered_at: str  # host clock, UTC ISO-8601 ending in "Z"
    no_known_position: bool
    elapsed_h: float | None  # hours since the person was last known; required when no position
    subject_category: str | None  # one value from the agreed set (R-07); None until agreed
    team_size: int | None  # searchers; drives radio spacing (section 7.4)
    lkp: LatLon | None = None  # None in the no-known-position case
    lkp_time: str | None = None  # UTC ISO-8601 ending in "Z"
    lkp_kind: str = "unknown"
    subject_identifiers: tuple[str, ...] = ()
    radio_count: int | None = None
    conditions: str | None = None  # weather and hazards; stretch with SPM
    schema: str = INPUT_SCHEMA

    def __post_init__(self) -> None:
        if self.lkp_kind not in LKP_KINDS:
            raise ValueError(f"unknown lkp_kind {self.lkp_kind!r}; expected one of {LKP_KINDS}")
        if self.no_known_position and self.lkp is not None:
            raise ValueError("no_known_position is set but lkp is not None")
        if not self.no_known_position and self.lkp is None:
            raise ValueError("lkp is None but no_known_position is not set")
        if self.no_known_position and self.elapsed_h is None:
            raise ValueError(
                "no_known_position needs elapsed_h; it is the only input the model gets"
            )
        unknown = [i for i in self.subject_identifiers if i not in SUBJECT_IDENTIFIERS]
        if unknown:
            raise ValueError(
                f"unknown subject identifiers {unknown}; raised set {SUBJECT_IDENTIFIERS}"
            )
        if self.schema != INPUT_SCHEMA:
            raise ValueError(f"schema {self.schema!r} is not {INPUT_SCHEMA!r}")

    def to_dict(self) -> dict[str, Any]:
        """The record as a JSON-safe dict."""
        data = asdict(self)
        data["subject_identifiers"] = list(self.subject_identifiers)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MissionInput:
        """Rebuild a record from ``to_dict`` output."""
        data = dict(data)
        if data.get("lkp") is not None:
            data["lkp"] = LatLon(**data["lkp"])
        data["subject_identifiers"] = tuple(data.get("subject_identifiers", ()))
        return cls(**data)

    def to_json(self) -> str:
        """One line of JSON, keys sorted."""
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, line: str) -> MissionInput:
        """Parse one line written by ``to_json``."""
        return cls.from_dict(json.loads(line))

    def to_case_fields(self) -> dict[str, Any]:
        """The keyword arguments for ``spm.schema.Case`` (I-01).

        Proposed mapping, for JJ to confirm: ``lkp`` -> ``ipp`` as ``LonLat(lon, lat)`` (None for
        no known position); ``lkp_kind`` -> ``ipp_type``; ``subject_category`` -> ``category``;
        ``elapsed_h`` -> ``elapsed_h``; the ``group`` identifier may map to ``party_size``. Whether
        ``team_size`` is a model input is section 11 question 13.
        """
        raise NotImplementedError("C-03 mapping to spm.schema.Case; waits on R-07 and JJ (PM-03)")
