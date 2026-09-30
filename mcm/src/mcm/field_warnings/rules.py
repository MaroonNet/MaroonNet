"""Field warnings: the three candidates from MCM v1.1 section 3.7, as testable rules.

Anything beyond what the stock app shows needs a custom app (section 3.6), so in v1 these rules can
only run at the command post, on the daemon's live feed, and reach the field as a text. Which ones
ship, and how they reach the searcher, is Open (section 9 Q8).

    outside_sector      the radio's last position is outside its assigned sector
    losing_connectivity the coverage model puts the radio at marginal or shadow, or the spacing
                        rule is broken (needs the co-owned coverage model and (P)MP's spacing)
    buffer_overwrite    the radio has been quiet long enough that its position buffer is about to
                        overwrite (about twenty minutes, MCM v1.1 section 6.8; Research)

Only buffer_overwrite can be evaluated today; the other two wait on sectors ((P)MP) and on the
coverage split. They are listed so the interface exists.
"""

from __future__ import annotations

from dataclasses import dataclass

from mcm.mesh.gaps import Gap

BUFFER_MINUTES = 20.0  # MCM v1.1 section 6.8, "about twenty minutes"; verify against firmware
WARN_BEFORE_MINUTES = 5.0  # Proposed


@dataclass(frozen=True)
class FieldWarning:
    kind: str  # outside_sector | losing_connectivity | buffer_overwrite
    node: int
    detail: str


RULES = ("outside_sector", "losing_connectivity", "buffer_overwrite")


def buffer_overwrite(quiet: list[Gap]) -> list[FieldWarning]:
    """Warn for radios quiet long enough that their buffer will soon overwrite."""
    limit_s = (BUFFER_MINUTES - WARN_BEFORE_MINUTES) * 60
    return [
        FieldWarning(
            "buffer_overwrite",
            g.node,
            f"quiet {g.seconds / 60:.0f} min since {g.last_heard}; "
            f"buffer holds ~{BUFFER_MINUTES:.0f} min",
        )
        for g in quiet
        if g.seconds >= limit_s
    ]


def outside_sector(*_args: object) -> list[FieldWarning]:
    """Waits on sector geometry from (P)MP."""
    raise NotImplementedError("needs sector polygons from (P)MP (MCM v1.1 section 3.7)")


def losing_connectivity(*_args: object) -> list[FieldWarning]:
    """Waits on the coverage-model split and the spacing rule."""
    raise NotImplementedError("needs the co-owned coverage model and the spacing rule")
