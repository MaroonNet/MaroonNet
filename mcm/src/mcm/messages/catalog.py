"""The field message set: what the command post can send to the field, and what it costs.

MCM v1.1 sections 3.5 and 7. About 233 bytes per packet on a shared channel of about 1 kbit/s.
v1 uses stock messaging (text, waypoints); sector assignments and out-of-range warnings are added
only if achievable, and anything the stock app cannot show needs a custom app (section 3.6).

Each entry records what it is, whether the stock app shows it, and a size estimate, so the airtime
and battery cost of a proposed message can be computed before anyone builds it. Sizes marked
estimate are guesses to replace with measured encodings.
"""

from __future__ import annotations

from dataclasses import dataclass

from mcm.mesh.airtime import MAX_PAYLOAD_BYTES, time_on_air_s

# Meshtastic adds its own header to every packet over the air (about 16 bytes). Estimate.
MESH_HEADER_BYTES = 16


@dataclass(frozen=True)
class MessageSpec:
    name: str
    direction: str  # "cp_to_field", "field_to_cp", "both"
    portnum: str
    stock_app: bool  # shown by the stock Meshtastic apps with no custom code
    typical_bytes: int
    status: str  # Team answer | Proposed | Open
    note: str


CATALOG: tuple[MessageSpec, ...] = (
    MessageSpec(
        "text",
        "both",
        "TEXT_MESSAGE_APP",
        True,
        60,
        "Team answer",
        "Free text. v1. Size is the UTF-8 length.",
    ),
    MessageSpec(
        "waypoint",
        "cp_to_field",
        "WAYPOINT_APP",
        True,
        60,
        "Team answer",
        "A named point on the stock app map. v1. Size is an estimate.",
    ),
    MessageSpec(
        "sector_assignment",
        "cp_to_field",
        "PRIVATE_APP",
        False,
        120,
        "Open",
        "Sector id plus a simplified polygon. Needs a custom app. Size is an estimate for about "
        "twelve vertices at reduced precision.",
    ),
    MessageSpec(
        "range_warning",
        "cp_to_field",
        "PRIVATE_APP",
        False,
        12,
        "Open",
        "Out-of-range or losing-connectivity warning to one radio. Needs a custom app to show it "
        "as a warning; a plain text is the stock fallback.",
    ),
)


def fits(payload_bytes: int) -> bool:
    return payload_bytes <= MAX_PAYLOAD_BYTES


def check_text(text: str) -> str | None:
    """Return a problem with a text message, or None if it fits one packet."""
    n = len(text.encode("utf-8"))
    if n == 0:
        return "empty message"
    if not fits(n):
        return f"text is {n} bytes; one packet carries {MAX_PAYLOAD_BYTES}"
    return None


def airtime_cost_s(spec: MessageSpec, preset: str, transmissions: float = 3) -> float:
    """Channel seconds one send of this message costs, rebroadcasts included (estimate)."""
    return time_on_air_s(preset, spec.typical_bytes + MESH_HEADER_BYTES) * transmissions
