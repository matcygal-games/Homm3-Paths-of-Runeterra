# Human motion finishing candidates

Status: **authored configuration**. Four battle definitions compiled successfully
with no converter errors. No native playback, artistic or release acceptance is
granted. The first receipt is `repair-1792525612636698700.json`.

Two actual built-in imagegen calls produced the eight-pose Legion sheets saved
in each unit's `motion-finish-v1/`. Adjacent generation receipts preserve exact
prompts, identity references, original cache paths and truthful model-not-exposed
provenance. Each sheet contains four fidget and four right-to-front half-turn
drawings. The larger raised-blade fidget pose is deliberately unselected. The
small actual wrist gestures select slots 0, 1, 1, 0 with explicit phase holds;
idle uses the same starting guard. These are not fabricated movement/attack
frames. A fixed atlas scale preserves proportions. Measured, documented rigid
contact translations align these stationary poses; no pixels were repainted or
warped, and no per-pose scale was used. The native comparison sheets show the
placed feet and same x197/y266 reference lines.

Native `ReverseAnimation` plays group 7 in the old facing, flips facing, then
plays group 8 in the new facing. Consequently source group 7 must show
right-to-front and source group 8 front-to-right; the latter becomes
front-to-left through native mirroring. Legion now selects the newly painted
front-facing turns instead of the old back-facing poses. Rose keeps its real
right-to-front group 7 and reuses those drawings in reverse order for source
group 8. This is explicit reuse of actual half-turn poses, not a claim of new
Rose generation. Earlier back-view groups and pre-edit recipes remain preserved.

The consumer references are `client/battle/BattleAnimationClasses.cpp:557-606`
and `CreatureAnimation`'s canonical-facing/mirror behavior. They were inspected
read-only. The PNG strips and lossless WebP loops reconstruct raw group 7 then
mirrored group 8 at 100 ms/frame around a fixed pivot. Actual VCMI stack-position
shifts, runtime timing, hand/weapon continuity and battlefield transition quality
still require native observation. Existing Rose offhand/outer-blade limitations
outside these groups remain pending; this report does not close them.

Reproduce with `python -B runeterra-noxus/scripts/art_human_motion_finish.py`.
The helper starts from immutable before recipes, writes versioned source frames,
pins exact source bytes and uses the real compiler for only these four battle
recipes. Earlier whole-atlas helpers refuse to replace the selected repair.
Other families, native content, game installation and VCMI checkout are untouched.
