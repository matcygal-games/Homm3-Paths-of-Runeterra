# Shurima puzzle cover candidate

This is a complete own painted cover candidate, **complete-unapproved**. The built-in imagegen tool generated the retained `generated-master.png` from the exact `prompt.txt`; no reference image was uploaded to the generation call. `generation.json` pins the prompt, original painting, conversion and native cover. `scripts/shurima_surface_art.py` reproducibly converts it to opaque RGBA and cuts forty-eight pieces. It does not publish or stage a build.

The native `CPuzzleWindow` draws a real `PuzzleMapView` at `(8,8)` with size `592x544`, then places each cover piece at `(x+1,y)` and removes pieces according to `whenUncovered`. The native cover is decorative regional scenery hiding the real grail terrain. This painting is not an adventure-map replacement or an invented terrain-location clue.

`CTownHandler::loadPuzzle` assigns filenames from array order, independently of uncover order: `piece00` through `piece47`. The current authored grid has eight columns and six rows. Each regular piece is `74x91`; the last row is `74x89`, exactly covering `592x544` with no extra bottom pixels. Positions and the existing uncover-order permutation remain unchanged. Compiler-plan checks reconstruct the entire source pixel-for-pixel.

Private originals were inspected in place, without copying their pixels into any output:

| Native reference | Measured canvas | SHA-256 |
| --- | --- | --- |
| `runeterra-demacia/references/hero-comparisons/original-castle-puzzle-native.png` | `592x544` | `d5fedfd017b1f2d1bdca7479f636e4ad186145c40658a2bbfbcf36f8fb22e2ee` |
| `runeterra-demacia/references/images/tpcascas.pcx.png` | `100x120` | `0590aac9a56597c683e5576c096bbb4ce7fde82b2ff193adb8c5dfb99920dd7e` |
| `runeterra-demacia/references/images/crbkgcas.pcx.png` | `100x130` | `bc0279fa9549b58831cf052947529bd302a6c644c8f0faa0a8bb8abc0f1bcb8d` |

The full LoR illustrations previously inspected for the regional subject vocabulary are pinned in `design/lore-decisions.json`: `04SH090` Grumpy Rockbear, `04SH055` Ruin Runner and `04SH046` Sandstone Chimera. In particular, the pack mount uses an original tall feathered biped silhouette rather than a horse, camel or reptile. The cover depicts an original local oasis scene, not an authenticated canonical street map, champion or illustration copy.

Conversion report: `build/reports/surface-art-20261023T062029027254Z.json`. Read-only production-compiler verification: `build/reports/surface-art-compiler-plans-20261023T062155880291Z.json`. The earlier failed harness report preserves an intentional source-hash rejection whose configured exception class was initially caught incorrectly; the corrected bounded run passes all fifty own recipes and both rejection controls.

The native cover and both small backdrops were viewed at actual pixel size. This is a scoped production observation, **not** independent native reveal/framing acceptance, final artistic approval or redistribution clearance. No gameplay/native process was launched. Root owns output compilation, manifest refresh and staging.
