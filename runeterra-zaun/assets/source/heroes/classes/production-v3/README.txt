Zaun mounted class action sources

These are separately painted command-hero appearances, not recruitable troops.
The four battle cohorts have 35 native 150x175 frames each. The two adventure
cohorts have 45 native 96x64 frames each: five static directions and five
eight-frame walk cycles. The two existing map-editor figures are separate
single-frame appearances and do not inherit the adventure action groups.

The local zaun_class_atlas_v4.py is an immutable snapshot of the alpha-preserving
battle atlas extractor. It performs complete-pose crop, uniform master scaling
and hoof-contact placement only. Never overwrite it when changing map tooling.

scripts/zaun_class_map_v5.py assembles the genuine adventure paintings using this
frozen extractor. Its explicit source selection preserves the original tight
Chemist East atlas and selects the genuine spacious repaint instead. Actual
returned dimensions are in generation receipts; prompt-requested sizes are not
substitutes for measurement. No alpha erasure, recolouring, mirroring, body-part
warp or duplicated idle cycle is used.

scripts/zaun_class_source_delivery_v5.py requires an explicit independent review
bound to exact cohort, comparison sheet, native frames, masters and provenance
before writing one of its six owned recipes. It preserves the blocked recipe,
refuses implicit replacement and grants no final art, runtime or rights status.
The coordinator alone converts recipes and publishes development stages.

Each master keeps its prompt, genuine built-in tool provenance and input hashes.
An undisclosed model remains null. Redistribution is unresolved; source delivery
does not grant rights to Riot intellectual property or make an installable release.
