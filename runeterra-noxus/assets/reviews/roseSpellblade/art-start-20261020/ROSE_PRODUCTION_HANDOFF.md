# Black Rose painted-art development handoff

Status: **authored configuration**. No asset is release accepted and no native gameplay was executed.

Eleven real OpenAI built-in imagegen calls produced ten base/upgrade action sheets and one four-pose directional attack sheet. Exact prompts, raw files, actual input/output checksums and the tool's unreported model-ID limitation are preserved in the two units' `painted-v1/*.generation.json` files. Existing standing masters were retained. No CLI/API fallback, original troop pixels, Demacia source pixels or synthetic idle-as-attack animation was used.

`scripts/art_rose_sources.py` extracts the controlled painted poses, retaining their alpha. One fixed scale is used across each atlas and one contact baseline across each entire atlas row. It makes no per-frame fit, distortion or generated motion. Real gait poses additionally used an assembled sheet of the unit's own six actual rig guide poses. That technical guide is not selected art.

Selected recipes now point to versioned `painted-v2` native sources. Their previous blocked recipes are preserved in each unit's `painted-v2/recipe-history-before-painted/` directory. Battle sources contain 59 unique poses and the native animation exports 60 frames, because group 22 truthfully reuses the actual final death pose. Each map exports six actual gait frames. Four rasters per unit provide large/small whole-unit recruitment icons and separately generated left/right attack actions; attack sides are not mirrors.

The selected twelve recipes compiled with **exit 0**, twelve successful recipes, zero errors and **144 compiled files**: 120 battle frames, twelve map frames, four animation JSON files and eight rasters. An immediate repeat conversion/compile preserved every compiled byte. **28/28 bounded technical checks passed**, including exact required group counts, distinct non-idle actions, final death/corpse linkage and repeat hashes. Exact observed output is in `rose-production-handoff-v1.json`; the compiler's first executed receipt is `build/reports/art-start-20261020/compiler/compile-1792512388853777800.json`.

The coordinator must refresh/select the shared manifest; this worker did not modify it or stage/publish anything. Compilation is technical candidate delivery, not the whole art closure gate or artistic acceptance.

Review [the paired animated previews](rose-motion-review.html), each unit's native contact sheet, and all selected sources before acceptance. Observed issues remain explicit:

- The turn sequences need endpoint and facing-flip continuity review; some generated endpoints return to a guard instead of finishing a clean half-turn.
- Some intermediate upgraded actions obscure or omit the small offhand dagger. Inspect or repaint continuity where required.
- A few outer atlas edges touch blade silhouettes. Preserve the sources and repaint any truncated tip before accepting that action.
- Actual motion must verify feet/pivot contact, idle-to-action scale transitions, walking cadence, map placement, teleport particle ownership and timing.
- No final comparison with original installed art, native animation/battle, ownership colors, AI or gameplay was performed. No identity review grants acceptance. Redistribution remains unresolved.

The two units retain independent hooded-base and masked/high-collar-upgrade silhouettes in the same painted material family. Their native statistics and movement mechanics were not changed.
