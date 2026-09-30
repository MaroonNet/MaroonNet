"""The plan: sectors, assignment, radio spacing, and the call into the coverage model.

(P)MP Architecture v1.0 section 7. Sectors and assignments leave this package as C-09 events and
C-01 ``sector`` rows. Radio spacing goes to MCM (I-10). Planned-position coverage is a call into the
co-owned ``mcm.coverage.model`` interface (C-06).
"""

from pmp.planning.assignment import Assignment
from pmp.planning.sectors import Sector

__all__ = ["Assignment", "Sector"]
