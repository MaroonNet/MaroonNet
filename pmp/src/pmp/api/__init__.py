"""The web backend and API: what the screen asks the command post for.

Framework-neutral until R-03 (Flask, Django, or FastAPI) is decided by the bake-off
((P)MP Architecture v1.0 section 7.7). ``surface.py`` lists the calls as plain functions; the
chosen framework wraps them.
"""

from pmp.api.surface import SURFACE

__all__ = ["SURFACE"]
