# Demacia adventure-map candidates

Five original town masters were generated with the built-in imagegen tool from
private original-game style references and the project's Demacian architectural
references. Each state directory preserves `master-v1.png` and its exact prompt
in `generation-v1.json`. These are **generated, unreviewed production candidates**.
They are not accepted release artwork or evidence of an in-game Demacia town.

Rebuild the native candidates from the workspace root:

```powershell
& "runeterra-demacia/.venv/Scripts/python.exe" -B "runeterra-demacia/assets/source/town/adventure/compile.py"
```

The recipe writes five 192x192 PNGs, five ownership sidecars and five group0/frame0
animation definitions under `assets/source/Sprites/runeterra/demacia/town/map/`. A static group0 is
intentional for these town objects. It does not satisfy any creature animation
requirement. `native-v1.png` beside each master preserves the native review copy.
It also derives eight town-state icons at 58x64 and 48x32 under `town/icons/`, using
the project's generated terrain background. The built variants have an original
red cross indicating that the day's construction allowance was spent.

`recipe-v1.json` records source/output hashes, dimensions, crop rectangles,
resampling, frame groups and every output path. Original Castle images are kept
only in the private comparison sheet
`references/demacia-adventure-native-comparison-v1.png`; they are not copied into
the new sprite outputs. `compile.py` never changes the global asset manifest,
staging, installed runtime or licensed game files.

It registers five `vcmi_animation` recipes and eight `raster` recipes under
`assets/recipes/adventure-*.json`. The normal `assets --resume` command can
reproduce/stage all 23 resources as unreviewed candidates: five animations,
five frames, five owner overlays and eight icons. Required missing assets and
visual review still block the overall assets/release commands.

The measured original map canvases are 192x192. Their alpha bounds are
`avccast0:(10,42,192,192)`, `avccasx0:(17,50,192,192)` and
`avccasz0:(17,44,192,192)`. The new candidates preserve aspect ratio and fit within
178x150 pixels, bottom-aligned to192; they do not claim identical silhouettes or
the same empty margins. Alpha16 determines each source crop rectangle because
the generated masters contain faint outside dust; retained pixels keep their
original alpha. Some source ground outlines touch the generated canvas edge.
Scaling cannot restore any clipped source ground and does not constitute a
ground-contact acceptance pass.

Required review/corrections remain:

- Compare the smoother, brighter new masonry and slightly frontal camera against
  original sprites at native scale; the village currently has a shorter skyline.
- Check contact shadows, grass footprint and terrain overlap in the engine.
- Confirm the visible gate/path meets the current template's visit tile and all
  approach/block rules. Pixel placement alone does not prove movement works.
- Keep the verified owner-mask boundaries attached to these exact native frame
  hashes. Changing the artwork requires remeasuring the cloth masks.
- Verify both town types and both daily construction states in large/small UI
  contexts, including a native original-town side-by-side comparison.

No candidate was approved or installed into the user's game by this recipe.
Complete Demacia gameplay acceptance remains blocked by the creature/faction
asset set. The separate art-resource diagnostic below executes actual rendering.

## Native owner-color implementation

`ownership-mask-v1.json` explicitly selects the two front cloth panels in each
native frame. The blue-only filter inside those polygons preserves gold emblems
and stone edges. Roofs and other decorative cloth lie outside the selection.
`scripts/owner_overlay.py` exports grayscale RGB with cloth alpha, without baking
any player color. The animation assembler copies it beside the corresponding
frame as `g00-f000-OVERLAY.png`. Its hash is a separate output and part of the
animation frame-review hash collection. Changed or undeclared stale overlays
cannot silently pass assembly/review.

The selected engine's [RenderHandler at commit66fa496](https://github.com/vcmi/vcmi/blob/66fa496c6328a276c4eb14c0011b3a9d751dfac3/clientsdl2/render/RenderHandler.cpp)
loads that sidecar for `ONLY_FLAG_COLOR` when `generateOverlay=0`.
Its [ScalableImage implementation](https://github.com/vcmi/vcmi/blob/66fa496c6328a276c4eb14c0011b3a9d751dfac3/clientsdl2/render/ScalableImage.cpp)
multiplies the overlay by the current owner color. Original indexed DEF flags
instead use special palette index5; general player-palette indices224..255 are
a different mechanism. Ordinary blue RGBA pixels are not a flag mask.
`generateOverlay=1` requests an outline and is not used for these owner panels.

## Executed art diagnostic

Run the isolated probe, which copies the portable runtime and reads the licensed
inputs without changing the original installation:

```powershell
& "runeterra-demacia/.venv/Scripts/python.exe" -B "runeterra-demacia/assets/source/town/adventure/probe.py" --capture
```

It registers one new scoped native flaggable object with five subtypes and zero
income/bonuses. Fifteen instances display the five states in red, blue and
neutral rows. Two original Castle towns keep the original factions visible.
This is an art/resource integration scenario, not an implemented Demacia town
construction/combat test. Town instances reselect their faction appearance
during initialization, so overriding a Castle map-instance template would not
have tested the new artwork correctly.

The successful run is recorded under
`build/reports/runtime/adventure-ownership-probe-v10/`. Its native whole-map export
is `references/in-game/demacia-adventure-ownership-atlas-v1.png` at 1152x768,
SHA256 `e7d0c58a767808e36abcf519705816e699ccbe30356c2c749be42b4c45a4158b`.
Both normal client capture and native Shift+F3 map export were inspected without
resizing. Pixel comparisons found exactly 93/49/101/96/93 changed pixels per
state for red-to-blue and blue-to-neutral, with **zero changes outside the
authored cloth masks** in every comparison. Roofs, masonry and gold stay intact.

The probe exposed clipping with the old 5-column/3-row visibility mask. Its
corrected 6-column/5-row mask is
`["VVVVVV","VVVVVV","VVVVVV","VVBBBV","VBBABB"]`, which preserves the original
blocked/visit offsets while exposing all painted pixels. Actual town approaches
and construction appearance changes still require Demacia gameplay tests.

The loader reports `OK` for the diagnostic mod and no missing image resources.
Two native `Cannot answer question -1!` errors remain in the successful run;
strict clean-AI acceptance was not granted. Native `controlai red` paused the
EmptyAI progression for stable review. All owned processes were closed and all
original archive hashes stayed unchanged. Earlier failed/window-capture attempts
remain qualified in their separate reports; black PrintWindow captures are not
visual evidence. This rendering check does not grant final visual approval.
