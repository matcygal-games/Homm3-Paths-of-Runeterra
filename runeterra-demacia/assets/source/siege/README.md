# Demacian siege source set

This is an owned artwork **development candidate**, not final visual/runtime acceptance. All32 SGDE exports have selected source masters, exact built-in imagegen prompts/input hashes, and native raster recipes. The opaque battlefield is separate from31 transparent fortification/water/bridge fragments. No Castle pixels are copied by the conversion process; licensed original reference images stay private under `references/`.

`layout-guide/master-v1.png` is the common material/camera production study. It is not the release battlefield or a substitute for layered buildings. Each `SGDE.../generation-vN.json` records the default generated original, preserved source, inputs, prompt and output checksums. V1 candidates superseded by corrections remain preserved. Explicit selected versions and current registered origins live in `production-plan-v1.json`.

Run these project-owned commands from the project root:

```powershell
.venv/Scripts/python.exe scripts/prepare_siege_art.py plan
.venv/Scripts/python.exe scripts/prepare_siege_art.py convert
.venv/Scripts/python.exe scripts/prepare_siege_art.py preview
.venv/Scripts/python.exe scripts/prepare_siege_art.py verify
```

`plan` preserves existing master/prompt bytes and explicit version selections. `convert` generates only siege raster recipes/exports. The helper does not change the global manifest, staged mod, faction or compatibility policy. `preview` writes private native assembly/contact sheets and an offline own Ranger turret diagnostic using the source renderer's whole450pixel horizontal mirror and232pixel height crop. It is not a runtime test. `verify` checks dimensions, nonempty true alpha, selected source/provenance/recipe hashes, and distinct wall states; it grants no acceptance.

The completed conversion was independently repeated in an isolated temporary project: all32 output hashes matched, and planning preserved source/prompt bytes and selected versions. Evidence and current source inventory are under `references/siege-production/` in `source-verification-v1.json`, `reproducibility-v1.json` and `handoff-v1.json`.

Real VCMI review must still cover the development proxy shooter appearance, all tower/wall destruction, gate lowering/raising/destruction, unit crossings, moat contact, foreground depth order, and fort/citadel/castle states. The below-gate breach is partly occluded by static arch/supports and needs particular crossing/depth review. All assets remain unapproved.
