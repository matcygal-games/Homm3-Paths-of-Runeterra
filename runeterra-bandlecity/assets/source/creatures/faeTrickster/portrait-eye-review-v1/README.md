# Unselected Fae Portrait Experiment

The final candidate is **padded-v2**. It uses own registered source ROI `[18,0,52,37)` pasted unchanged at `(4,4)` on transparent42x46, then the frozen existing Bandle compiler converts to58x64. `padded-v2/large-draft.recipe.json` is a draft inside this experiment, not an active recipe. `small-diagnostic.recipe.json` produces only an unselected32x32 comparison; keep the selected small/adventure/battle/preview untouched.

Measured eye core: source `(43,24)`, RGBA `(26,129,90,252)`; full measured cluster `[42,21,45,25)`. No recolor, paint, new pose, new light or changed troop identity is introduced. This remains a generic leaf-wing seedpod, not Pix or another unique character. Human visual review, controlled native context and rights remain pending.

Execute from an existing workspace or an extracted source archive:

```powershell
python -B runeterra-bandlecity/assets/source/creatures/faeTrickster/portrait-eye-review-v1/replay.py --replay
```

Requires Python and Pillow12.3.0. No other tool/library or global compiler call is required. Frozen compiler code is byte-identical to the actual shared source; its supported factory configures the Bandle namespace in separately named scratch project roots. Output is jailed to the owned experiment reports. `--replay` never loads active selections or live sources. The live capture mode without flags is for this exact workspace snapshot only and fails on changed protected receipts or conflicting existing experiment bytes.

The original two-pixel-padding attempt in this folder/report parent is preserved as failed evidence (15/16; filter tails on large edge). It is not the final candidate. Final reports, actual PNGs, raw RGBA/alpha metrics, two independent compiler receipts, fourteen-field candidate manifest, source archive and extracted replay proof are under `build/reports/five-town-audit-20261022/art-portrait-fix/padded-v2/`.
