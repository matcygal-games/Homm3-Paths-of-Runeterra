# Original Bandle siege art handoff

22 October 2026. Status: **authored configuration**. All outputs are **built-unreviewed**; zero final art approvals. The coordinator owns manifest integration, compilation, publication and native desktop testing.

## Implemented

The actual `faction_pipeline.required_outputs` contract expands SGBC into 32 structural images, plus `towerLarge.png` and `towerSmall.png`: **34 outputs**. All have original painted masters and exact generation metadata under this source tree, and deterministic pinned recipes in `assets/recipes/siege/`. The active output prefix is `Content/Sprites/runeterra/bandlecity/siege/`.

The structural family uses dark warm worn timber, woven living roots, mossy warm-gray stone, small amber lights and muted teal/violet cloth, matching the own town architecture. The independent woodland battlefield is 800 × 556. Walls, gate/bridge states, moat/bank, towers and front battlements are separate actual paintings. No original Castle or other faction pixels or contours were recolored or incorporated.

Original Castle full-siege and part references were viewed read-only before production. `native-geometry-v1.json` preserves 32 verified original-reference hashes and numeric canvas/attachment measurements, drawn from the existing Freljord measurement records. Only numbers were reused. Original reference art is not included here. Two too-wide initial candidates remain preserved; explicit selection uses `SGBCARCH-v2` and `SGBCMAN1-v2`, never filename recency. The source directory names identify revisions; the master itself remains `master-v1.png` inside each selected directory.

Eleven damaged wall/tower outputs reuse the exact own-intact scale and camera transform. Damage masters contain broken timber, missing spans or holes rather than renamed intact files. Gate/bridge raised, lowered and destroyed poses are separate generated variants. Foreground tower caps are separate shallow paintings for gunner occlusion. The two tower portraits derive from one independently painted headshot matching the own generic base `bandleGunner`: russet fur, brown canvas cap and work clothes, with no Tristana identity or upgrade armor.

Each master was generated through the built-in `image_gen.imagegen` tool with its exact prompt, output path, reference role and input/output SHA-256 records preserved. No CLI/API fallback or synthetic raster painting was used. Raw masters are untouched. The derivative operation uses a documented faint-alpha matte floor of 16, uniform scale, crop and transparent padding; original RGB is preserved and original game contours are never used as masks. Small tower portrait output uses its own explicit face crop.

## Executed checks

From the workspace root:

```powershell
& runeterra-demacia/.venv/Scripts/python.exe runeterra-bandlecity/scripts/bandle_siege_art.py
```

The command completed with exit 0: **34 recipes and 34 read-only planned converter outputs**, zero generated-stage writes, `art_accepted: false`. It uses the actual `faction_art_compile.create_compiler('bandlecity').plan` implementation and validates exact-source hashes and native canvases. `technical-registration-v1.json` records selections, transforms, source/recipe hashes and output hashes.

Viewed technical review artifacts are `native-parts-review-v1.png` and `native-composition-state-1-v1.png`, `native-composition-state-2-v1.png`, `native-composition-state-3-v1.png`. The part board contains actual registered PNGs; the compositions mount those own parts at coordinator-authored numeric siege coordinates. They are offline visual diagnostics, not native engine captures or signed acceptance. `masters-initial-review-v1.png` is the earlier unregistered contact sheet and includes retired first arch/keep attempts; it is not the active selection.

## Incomplete

Direct native battle inspection must assess fine/spindly timber readability, moat/wall and gate joins, ground contact, bridge states, shot visibility and foreground-cap occlusion. The coordinator viewed the own family as a suitable first development direction while explicitly retaining those questions. The part set does not establish siege interaction, movement, wall damage, tower shooting, AI or balance behavior. No game window was driven and no stage or package was published by this worker.

## Blocked acceptance

Final art, rights/redistribution and release reviews remain pending. A passing converter plan and own generated paintings confer none of those approvals. External review results must be recorded by their actual reviewers; none are fabricated by this handoff.
