# Legion map gait repair and contact review

The two Legion families remain **authored configuration** with compiled painted
art candidates. No native runtime, art, licensing or release acceptance is claimed.

The selected map cohort is now the independently generated `map-atlas-v3.png` in
each unit's `painted-v1/` directory. These were generated from the six actual own
rig walk poses arranged three columns by two rows, with the standing painting used
only for identity. Compared with the old row of similarly leading feet, the new
poses include narrow passing stances, opposite wider contacts and a raised-knee
phase. The worn Recruit equipment and heavier masked Veteran equipment remain
distinct. No individual image was warped or stretched. One uniform scale per unit
and row layout baseline produce the six 96 × 64 native frames.

Raw generated outputs, original prompts and actual-tool disclosure are retained
in the adjacent generation sidecars. Earlier v1/v2 map atlases and their native
source frames remain intact. The previous compiled map JSON, six PNGs, recipe and
checksums for each unit are additionally preserved in
`painted-v1/compiled-map-before-v3/`. Current canonical native map outputs select
the new `painted-v1/map-v3/` source frames. Battle frames did not change.

`native-map-old-vs-guide-v3.png` shows the old and new cohorts at actual native
size. `map-gait-comparison-preview-v3.gif` is a six-frame technical motion preview
at an arbitrary 150 ms per frame; it is explicitly not engine timing evidence.

The executed fixed-contact audit measured **90 living-action frames in 20 groups**
across both units. It reads the actual compiled PNGs, pins every hash, and draws
the same native x197/y266 reference lines on every pose. The lowest painted boot
contact row ranges from y264–266 for Recruit and y263–266 for Veteran. Death and
corpse poses are excluded from this upright-ground measurement.

The stationary fidget exposes remaining variation: Recruit contact-band center
spans **4.5 native pixels**, with boot-band width **33–38 pixels**; Veteran center
spans **7.5 pixels**, with width **47–50 pixels**. Each fidget's vertical contact
span is one pixel. Contact-band centers in walking and striking groups include
intended stride and lean and are not a measured skeleton-root trajectory. A
single constant translation of the entire family cannot remove the changing
frame-relative offsets. Aligning one toe would still leave the different painted
foot widths. No per-pose translation, fit or warp has been applied to conceal
this gap. A later constrained painted fidget cohort, or explicitly reviewed rigid
placement correction, is still needed before final animation acceptance.

Audit receipt: `battle-contact-audit-1792513356531276400.json`, with the two exact
native contact sheets named in that receipt. Reproduce without changing art:

```powershell
.\runeterra-demacia\.venv\Scripts\python.exe -B runeterra-noxus/scripts/art_human_contact_audit.py
```

The final technical conversion selected **12 manifest outputs / 128 physical
files**, with zero conversion errors and exit zero. Repeating conversion preserved
every output byte, including all 104 unchanged battle poses. The final conversion
receipt is `../legion-painted-action-v1/conversion-1792513470889624900.json`;
`repeat-build-verification-v3.json` records the exact 128-file hash map.

The stable production helper is `scripts/art_human_legion.py`. It remains scoped
to these two units, selects the v3 gait, preserves prior cohorts and writes
technical candidates only. Remaining acceptance includes stationary fidget
placement, loop/turn transitions, native timing and mirrored use, final native
scale/style comparison, source rights, and all gameplay/runtime categories.
