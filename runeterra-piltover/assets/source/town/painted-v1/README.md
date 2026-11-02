# Piltover painted town candidate

Status: **authored configuration**. These sources have not received final art,
redistribution, native graphical or release acceptance.

All35 building masters, the empty landscape and the optional harbor gangway were
created using genuine OpenAI built-in image generation as painted2D artwork.
No Blender, 3D renderer, rendered underpainting, copied Castle architecture or
cropped Legends of Runeterra illustration is used as final artwork. The imagegen
skill was read before production. Original Castle background/building assets were
privately inspected at their actual native sizes for rendering-language reference;
licensed reference bytes are excluded from this portable source tree.

The selected source candidate uses `layout-plan-v3.json`: sixteen ordinary land
sites, one shared site per troop tier, an optional over-water harbor and an optional
independent Grail site. The coordinator approved a bounded coast-only extension
and the genuinely painted gangway connecting the dock to the existing dry city
promenade. Every ordinary building preserves its full roof, material silhouette,
entrance steps and contact shadow inside its planned envelope. Technical land-mask
evidence is a planning proxy; actual terrain/footing pixels were also inspected.

The palette is warm aged stone, brown timber, weathered bronze, navy/teal cloth and
restrained blue hextech. Physical banners and architectural ornaments use the
actual Piltover crest shape, inspired by the official region icon rather than a
generic cog or Demacian wing. Compressed city geography, several civic institutions,
recruitment buildings, upgrades and the Progress Orrery are project adaptations.

`buildings/<state>/master-v1.png` preserves each genuine painted master.
`source-generation.json` and the saved exact prompt pin its real output and
lineage. Padded edit references are technical whole-image translations of the
preceding own master; additions and removals were painted by imagegen. The
unregistered opaque Cargo Exchange attempts are retained privately as failed
outputs; the successful third attempt has genuine transparent alpha. No global
white/chroma key was applied through ivory walls, windows or building interiors.

Reproduce technical exports from the workspace root:

```powershell
.\runeterra-demacia\.venv\Scripts\python.exe -B runeterra-piltover/assets/source/town/painted-v1/assemble.py
```

The native landscape reproduces by whole-image RGBA LANCZOS reduction of
`landscape/master-v2.png` to800x374; its existing native output is provided and
pinned. `assemble.py` uniformly scales/translates complete own paintings into
800x374 transparent frames. Entrance/source-density calibration is explicit in
the producer and `placement-calibration-v1.json`; states at each physical site
share a doorway scale instead of being independently stretched to fill boxes.
Coastal building contact is anchored at101,179; the separate painted gangway exits
onto the existing dry promenade around114,191. Its complete footprint fits the
coordinator-approved121x85 coastal envelope. One layer, one complete state per site
is composited at a time. The `ship` state contains dock, moored vessel and gangway.

The exact production candidate is `candidate-recipes.json`: **142 required
recipes**, comprising35 building animation/area/border/campaign sets, one background
and one real native-ID-indexed `town/buildingIcons.json`. Its35 construction frames
are150x70, use actual IDs from the readonly native building library, and preserve
ID gaps. Per-state `construction.png` images remain source files, not extra
unconfigured game outputs. Earlier standalone construction recipes are unselected
history and are deliberately absent from the142-entry selection list.

Technical exports include full-canvas independent layers, visible-alpha click
areas, restrained silhouette highlight borders,58x64 campaign icons,150x70
construction source images and matching native animation JSON recipes. Complete
source dependencies are pinned in `source-inputs.json`; the actual geometry and
all35 frame checksums are in `layout-acceptance-contract-v1.json`.

The uniquely named report `build/reports/piltover-implementation-20261025-v1/town/assembled-v3/`
contains actual800x374 empty/early/partial/base/upgraded/coastal/Grail/full source
compositions and all35 layers at native scale. The configured SDK compiler planned
all142 required recipes/212 native output files successfully. Its actual geometry
inspector passed against a bounded isolated fixture containing real compiled JSON
and frame bytes. Active generated assets, development staging and the desktop were
not changed by this worker. The coordinator inspected the V3 composition and gave
source-direction approval; final native visual, construction-click, siege, sound,
AI, save/reload, human art and redistribution acceptance remain separate.

Rights: project-directed generated artwork contains Riot-derived faction subjects
and insignia. Attribution is documented; permission to redistribute is unresolved.
No source review or successful technical conversion grants that permission.
