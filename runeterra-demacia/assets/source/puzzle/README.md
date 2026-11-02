# Demacian puzzle cover production

`map-master-v2.png` is the current own-art candidate, generated with the built-in image tool. `prompt-v1.txt`, `prompt-v2.txt` and both generation-result records preserve the exact requests and provenance. Version 1 remains as the earlier, more naturalistic draft; version 2 strengthens ink contours and matte shape groups after comparison with the original Castle cover.

The geography is project fiction inspired by Demacia. It does not claim to be a canonical capital map or mark the scenario's Grail location. VCMI draws these pieces over the actual scenario puzzle view and removes them as obelisks reveal the underlying map.

The native conversion recipe is `assets/recipes/puzzle/map-native.json`. Its preserved 592×544 result, `map-native-v2.png`, is the checksum-bound input for the 48 tile recipes `piece00.json` through `piece47.json`. There are eight 74-pixel columns, five 91-pixel rows and a final 89-pixel row. Each tile is a direct crop with no rescaling or invented edge pixels.

Run from the mod project directory:

```powershell
& .venv/Scripts/python.exe -B scripts/runeterra.py assets --resume
& .venv/Scripts/python.exe -B assets/source/puzzle/check_puzzle.py
```

The normal asset command processes the recorded raster recipes; other incomplete asset categories can still fail the overall asset stage. The focused checker validates actual exported PNGs, their recipe/source hashes, reveal order, crop pixels, placement and complete reconstruction. It passed for all 48 tiles and all 322,048 pixels, with coverage exactly once per pixel. Per-tile resume conversion also reproduced identical hashes.

`CPuzzleWindow` places each piece at configured x plus one, with the underlying view starting at (8,8). Configured positions (7 + 74×column, 8 + 91×row) therefore cover the viewport exactly. Filename numbering follows array position; the separate `index` field is reveal order. The current faction's reveal order covers 1–48 once.

`production.json`, `assembly-check.json`, `tile-exports.json` and `review/review.json` record the current files and results. `review/reconstructed-native.png` contains own art only. Original-game comparison excerpts remain under private `references/hero-comparisons/` and are excluded from this source-art directory. Actual obelisk UI rendering and reveal animation remain untested; no final visual approval is granted.
