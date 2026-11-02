# Axe Reckoner action conversion — bounded handoff

Status: **authored configuration**. This pass does not establish complete battle
animations, native gameplay, visual acceptance, redistribution rights or release
acceptance. No client was launched and no balance/content dictionary was changed.

`scripts/art_axe_actions.py` owns only battle/map/attackLeft/attackRight for
`axeReckoner` and `veteranAxeReckoner`. The four portrait recipes and the two
projectile recipes are excluded and checked read-only. The coordinator's later
addition of their production-status history is acknowledged and was not reverted.
All generated masters and generation sidecars remain intact.

The clean conversion cohort contains **six manifest outputs / 18 physical files**:
two map animation JSONs, twelve map frames and four distinct attack icons. The
technical compiler reported zero errors for that selected cohort. The native-size
map/icon sheet is `native-map-attack-candidates-1792517210087049800.png`.

Both battle recipes remain `blocked-incomplete-painted-actions`; neither battle
animation JSON was selected or compiled. The helper intentionally exits **2** for
the incomplete task. Its separate clean-cohort conversion result remains explicit;
it must not be confused with completion of all required actions.

The measured partial native source inventory is:

| Unit | Source frames | Recovered/pinned groups | Remaining groups |
| --- | ---: | --- | --- |
| Axe Reckoner | 34 | 0:6, 1:4, 2:1, 3:4, 4:4, 5:6, 15:8, 22:1 | 7/8 turns, 11/12/13 melee, 14/16 diagonal shots |
| Veteran Axe Reckoner | 68 | Same groups plus 11/12/13:6 each and 14/16:8 each | 7/8 turns; recovered strikes/shots still need visual continuity review |

These are **source candidates**, not accepted actions or additional compiled
manifest outputs. `action-extraction-1792517210087049800.json` records every
source atlas/index, source hash and crop bounds, fixed scale, native hash and
native alpha bounds. Source body-height references are 81/85 pixels, with one
uniform scale for each whole sheet and no individual pose fit or stretch. Native
partial sheets for both units show exactly what was recovered.

The base combat and diagonal-shot atlases could not be partitioned into their
required numbers of distinct full subjects by the conservative alpha-island
extractor. Those cohorts were excluded, rather than selecting fragments or
replacing an action with idle. This does not prove every individual melee pose is
unusable; reliable separate-pose extraction or a corrected cohort is still needed.
The merged first-row combat deaths are not used. Death group 5 and corpse 22 use
the separately generated `death-v2-atlas`.

The reaction atlas's turn rows do not directly supply verified native flip phases.
The visual-order proposal is recorded only as a proposal: right-facing → front
quarter → front → left view; then left view → back → back quarter → right endpoint.
Source indices are listed in the receipt. Neither group 7 nor 8 is pinned from
that proposal. Exact native playback requires source/runtime verification.

Remaining source review includes the previously identified crowded/truncated
diagonal axe silhouettes and reaction endpoints. An exact-border alpha test alone
cannot establish complete weapon geometry: the softened source masks have little
or no substantial alpha at the outermost row. No assertion that those poses are
complete follows from that test. The recovered Veteran attack poses therefore
remain unaccepted despite having measurable native PNGs.

Map silhouettes and upgrade armor read clearly in the native sheet, but the
same-leading-foot gait remains unresolved. The base map source index 5 and Veteran
map source index 3 also change the apparent axe hand relative to neighboring
poses. Those six-frame map cohorts are technically compiled candidates only;
native gait/hand continuity and timing are not accepted. Attack icons are distinct
own painted poses, not mirrored copies.

The apparent brown backgrounds in several raw master previews are hidden RGB
under alpha zero; they were not mistaken for opaque pixels or keyed out. The
technical process separates actual painted alpha islands and preserves source
artwork. No further broad image-generation retry was performed in this pass.

`repeat-verification-v1.json` and its linked final extraction receipt record the
settled repeat run and exact 18-file hash map. An earlier concurrent wrapper
assertion occurred while coordinator-owned portrait/projectile metadata was being
updated; that attempt is not presented as a successful repeat. The final repeat
preserves byte-identical compiled candidates and continues to report two blocked
battles. No manifest or acceptance entry is promoted by this helper.
