# pmp/web

Placeholder for the command post screen: the planning view, the live view, and the AAR replay
on one map (I-18). Empty on purpose.

What decides its contents:

- **R-10, map library.** React with MapLibre GL JS is the lean (Team answer); the comparison
  against Leaflet and OpenLayers is Research ((P)MP Architecture v1.0 section 7.8). The
  comparison covers offline vector tiles, a large raster overlay, time-filtered layers, and
  polygon editing.
- **A-05 (PM-06), where the replay UI lives.** Architecture v1.0 section 5.1 puts `pmp/web/` and
  `aar/web/` in one frontend build with the build config here. A route group in this app, or an
  `aar/web/` folder this build includes, is open with Corey.
- **The command shell.** Browser tab served by the backend is the lean; Electron stays in the
  comparison; Tauri is out (Team answer, (P)MP v1.1 section 3.7).

Until R-10 is decided, no framework, no package manager file, and no build tool is added here.
