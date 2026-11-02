PATHS PRIVATE CREATURE PREVIEWS - 27 OCTOBER 2026

Status: authored configuration. Native UI observation is pending.

Producer: scripts/paths_unit_previews.py
API: build_previews() returns a dictionary of nine namespaced Piltover creature
patches containing ONLY graphics.animationPreview. The coordinator merges these
into the existing private addon patches. This helper never writes regional
creatures, battle frames, projectile origins, maps, timing or publication files.

Source: the current selected genuine painted 2D regional frame cohorts. One
uniform camera per unit covers normal holding, moving, fidget and transition
poses. No per-frame fitting, limb deformation, invented/repeated poses or new
3D artwork. Hit, defend, front attack and special frames remain genuine and keep
their native group/order. Extended attack overswings do not determine body scale;
their viewport losses are separately recorded. Extra symmetric transparent canvas
preserves the complete transformed pose and existing own shadow sidecars while
the engine center-crops its actual 100x120/130 viewport. The battle camera remains
unchanged.

Runtime requirement: the existing coherent BC6 client/library and optional
generic graphics.animationPreview schema/consumer. This is not a stock VCMI
claim. The helper checks the actual BC6 schema and binary consumer symbols.
An actual official-46f2e15 schema-negative control rejects that unsupported
runtime. Root's full-loader and visible native-UI test remain necessary.

selected-production.json binds source SHA256 values, fixed camera parameters,
each derived frame, exact resource selectors and runtime capability evidence.
latest-checks.json points at executed repeat and negative-control checks plus
native-size software projections. They are not in-game screenshots.

The executed checks cover 9 units, 202 genuine frame slots, 281 source pins,
zero ordinary-cohort body loss in both viewports, and 18 real-pixel displacement
negatives. Those negatives preserve all source alpha on the complete preview
canvas before the viewport check fails. Two real producer runs reproduced the
same patches/receipts/derivatives. Thirteen extended attack frames have separate
viewport overswing loss; source body pixels and battle frames remain intact.

Source snapshots and derivative namespaces are keyed by exact selected inputs
and producer SHA256. Earlier technical candidates remain as versioned history;
only paths returned by the latest producer run are selected by the addon.
Nothing here establishes final art, full gameplay, rights or release acceptance.
