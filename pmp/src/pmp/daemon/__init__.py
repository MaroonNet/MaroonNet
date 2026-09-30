"""The bridge daemon (I-17): gateway I/O, packet decode, database write, push to the screen.

Group-shared code ((P)MP v1.1 section 3.6; Architecture v1.0 section 5.3): a second person from
another segment signs off before anything lands here. Proposed CODEOWNERS line:
``/pmp/src/pmp/daemon/  @heimsothe @coreybbgreene @alasdiego``.

Written as a library so that either command post shape can host it (PM-01, Open): one process
runs ``Bridge.run`` as an asyncio task beside the API; two processes run it under ``pmp daemon``.
"""

from pmp.daemon.bridge import Bridge, as_mapping, row_from_record

__all__ = ["Bridge", "as_mapping", "row_from_record"]
