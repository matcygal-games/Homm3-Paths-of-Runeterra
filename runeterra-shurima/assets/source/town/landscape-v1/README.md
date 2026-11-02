# Own empty-town terrain candidate

Status: built-unreviewed; **no final art, native runtime or release acceptance**.
This directory contains a real builtin-generated raster master and one targeted
geometry edit. The first pass remains preserved. No original Heroes III or Riot
pixels were supplied to either generation call; private native/LoR references
were inspected to inform the written art direction.

- `prompt.txt`: complete first-pass prompt.
- `generated-master.png`: first-pass 1834 × 858 source.
- `normalize.py`, `conversion.json`, `terrain-native-800x374.png`: first-pass
  conversion and native comparison.
- `geometry-edit-prompt.txt`: complete targeted edit prompt using the authored
  `design/town-visuals.json` geometry. It corrects dry foreground space and water.
- `geometry-adjusted-master.png`: retained edited 1833 × 858 source.
- `convert-master.py`, `master-conversion.json`, `master.png`: deterministic
  integer centre crop, RGB conversion and Pillow LANCZOS downsample to 800 × 374.
- `generation-v1.json`, `generation-v2.json`: provenance and scope records.

Reproduce the current native candidate from the workspace root:

```powershell
& runeterra-demacia/.venv/Scripts/python.exe runeterra-shurima/assets/source/town/landscape-v1/convert-master.py
```

The terrain contains no functional hall, fort, dwelling, market, guild or Sun
Disc. Retaining edges, paths and irrigation are scenery. Town-state layers must
still be authored and integrated. Exact support of every building footprint,
coast state, click mask and native visual fit remains pending. This raster is an
own editable source candidate, not a layered/rigged 3D scene or a completed town.
