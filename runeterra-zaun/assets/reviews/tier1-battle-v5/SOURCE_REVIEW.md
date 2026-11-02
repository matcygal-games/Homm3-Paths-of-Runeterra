# Zaun tier-one battle sources, v5

Reviewer: Codex worker `/root/zaun_aux_art`. Scope: the two own painted battle cohorts only. This is source pixel review and technical preparation, **not** native gameplay or release acceptance.

Both Zaun Thug and Chem Punk have 52 prepared frames at 450 × 400, fixed pivot (197, 266). Their twelve groups are moving 6; fidget 4; holding 1; hit 4; defense 4; death 6; turn-left and turn-right 4 each; upward, frontal and downward melee 6 each; dead 1. The dead frame is an exact permitted copy of the last death pose. No shooting, spell, flight or multi-target group was added.

## Source and pose findings

- Each final pixel comes from a genuine built-in imagegen painting. The mannequin renders are pose guides only and remain excluded from final output. No original, Demacia or other faction pixels are used in either unit's game art.
- Six walking phases alternate the anatomical supporting leg. At frame 0 the brown foreground boot with two small buckles leads; at frame 3 that same boot trails while the darker far boot leads. Passing phases have distinct bent knees and lifted feet. This was inspected in both large source paintings and the native-size strips.
- The unarmored base has patched workwear, exposed head, a wrapped left fist and one plain short iron pipe. The upgrade retains the same ordinary human body and adds a riveted headstrap, layered rusty shoulder plate, heavier pipe collar, small green reagent vial and muted purple lining. The worker remains distinct from a royal soldier or plate-armored legionary.
- Fidgets use small actual wrist/arm poses. Hits recoil and settle. Defense raises and braces the pipe, then recovers. Half-turns show real front/side/back body and equipment views rather than mirrored pixels. Death progresses through slump, kneel and a complete sideways corpse, with the dropped pipe visible in the final pose.
- Melee groups have preparation, wind-up, one contact, follow-through and recovery. Source inspection caught an early frontal extension and two raised recovery poses. These were repaired with genuine isolated painting edits before source selection; no idle-frame transplant or limb warp was used.

## Selected and rejected attempts

Selected paintings are listed, hashed and linked to their exact returned generation provenance in each `assets/source/creatures/<unit>/painted-battle-v5/native-candidate-v5/cohort.json`.

The base uses the original five action paintings plus `melee-front-preparation-v7` for one genuinely corrected frontal preparation. The upgrade uses its five action paintings plus `melee-sequence-repairs-v7` for genuine upward recovery, frontal preparation and frontal recovery. Every selected source has one recorded uniform camera scale. All exact source rectangles, source pelvis/contact anchors and native translations are recorded per frame.

The broad base `melee-up-front-sequence-v6` repair is preserved **unselected**: it corrected the arm but enlarged several subjects and cut off a pipe and lower boots at the image edge. The original incorrect preparation/recovery cells are also unselected. Earlier failed `painted-walk-v2/v3-unselected` and retired primitive `painted-v1` history remain intact and excluded. These are saved attempts, not deliveries.

## Technical preparation and evidence

The helper performs whole-subject rectangular extraction, one uniform RGBA resample per coherent painted source and translation-only registration into the fixed native canvas. Alpha thresholds measure bounds/registration only; they never erase or replace final alpha. Uneven generated gutters are handled by whole-subject rectangles rather than grid cuts through feet. Upright rows retain painted pose bob and raised feet; falling poses retain their horizontal fall displacement and ground contact.

Evidence under `build/reports/tier1-battle-v5/`:

- `native/<unit>-all-native.png`: all 52 poses at actual game scale on gray, with fixed viewports.
- `native/<unit>-walk-2x.png` and per-group 4× GIFs: enlarged diagnostic previews. These are not native timing claims.
- `native-original-comparison.png` and its JSON: actual unscaled Castle Pikeman, Halberdier, Crusader and Monk references beside the new neutral poses. Original pixels exist only in this diagnostic comparison. New neutral alpha height is close to the original Crusader reference; the coats have a broader silhouette than the narrow pike troops.
- `source-checks.json`: complete action coverage, genuine master/provenance SHA pins, RGBA/native dimensions, whole-subject crop margins, uniform scale per painting, exact pixel replay and final corpse continuity.
- `source-tests-raw.log` and `source-tests.json`: executed regression results. Read these files for the actual test count; do not infer a broader project count from this bounded suite.

The independent coordinator source review is recorded separately in `independent.json` before recipe delivery. Its positive verdict permits **built-unreviewed** source preparation only.

The delivery gate requires a named independent reviewer with an ID distinct from the recorded painter, the exact current cohort hashes, all 52 frame-path/hash entries per unit, and the exact native board path/hash. Visual approval, final art acceptance, runtime verification and release acceptance must all explicitly remain false. Changing/re-pinning a cohort or changing even one frame invalidates that review. The executed expanded regression log is `build/reports/tier1-battle-v5/checks/20261021T151549448127Z/source-tests-raw.log`; its JSON reports 17 tests passed, including real delivery calls that reject stale/false-acceptance evidence without writing either recipe. Earlier logs are preserved.

## Still pending

The coordinator must convert and stage these sources. Actual game action timing, weapon contact, engine-generated shadows/overlays, selection, retaliation, save/reload and AI behavior remain unobserved for this cohort. Native in-game visual acceptance, full identity evidence and redistribution rights are still pending. The latest battle upgrade uses green reagents; frozen older auxiliary portraits remain unchanged and need the coordinator's later palette-coherence pass. No release gate is weakened by this source review.

Reproduction (workspace root):

```powershell
runeterra-demacia/.venv/Scripts/python.exe -B runeterra-zaun/scripts/zaun_tier1_battle_v5.py check
runeterra-demacia/.venv/Scripts/python.exe -B runeterra-zaun/scripts/zaun_tier1_source_review_v5.py
```

`compose` technically reassembles saved accepted-for-preparation source paintings without regeneration. `deliver <independent.json>` modifies only the two owned battle recipes after matching source checks and independent native-board review. Neither command publishes a stage.
