# Draklorn Inquisitor painted action packet

Status: **authored configuration**. Visual approval, native motion verification and release acceptance remain pending. This is a report-only production packet; the coordinator owns selection and staging.

Selected identity: `../standing-v2.png`, SHA256 `b85568fc540936217e1fb8e683200591ebda8064b3668bb68d6efa317c342bcb`. All original standing alternatives and their request files are preserved. The white-fur, hooded living Frostguard screening warrior carries one bifurcated two-horn polearm. The small three-prong gear mark is a project adaptation, not an official national emblem. No spells, shooting or free Thralls are authored.

Each action source is an independently painted built-in imagegen pose. Exact prompts are in `../prompts-v1/`; raw sources and failed repairs remain in `../actions-v1/`. Private tool receipts and read-only reference comparisons are in `build/reports/painted-draklorn-inquisitor-actions-20261024-v1/private/`. The selected compact final collapse uses `death-fall-v3` and `death-rest-v4`; older straight-legged and unsuccessful repair candidates are unselected history.

`assemble_packet.py` applies one exact .100 battle pixel scale, 4x sampled affine conversion and manual anatomical ground registration to native root193,266 on450x400. Source-ground contacts are recorded in `fixed-conversion-v1.json`, including repaired fall810 and rest750; generator placement differed from the requested raw y860/900, so translation maps actual contacts to the same native ground. There is no per-pose opaque-bound fitting or scale adjustment. Body pixels and technical alpha-derived shadows are stored separately.

The sixphase walk alternates the near chevron-plated leg and far narrow boot. Group2 is one static standing frame. Group1 is an occasional nine-tick fidget at native10FPS. Each sixframe melee has true painted contact at zero-based index3, matching `currentFrame*2 >= totalFrames`. The retained pose returns are timing holds rather than additional source poses. Native motion is still pending.

Adventure images use two genuine compact upright-polearm poses, one common .046 scale and64x64 root48,60. The left attack uses actual Pillow inverse mirror coefficient97, preserving discrete root48 rather than moving it to15. Portraits are58x64 and32x32 crops from the selected standing master.

Reproduction from workspace root:

```powershell
runeterra-demacia/.venv/Scripts/python.exe runeterra-freljord/assets/source/creatures/painted-20261024/draklornInquisitor/technical-v1/assemble_packet.py
runeterra-demacia/.venv/Scripts/python.exe runeterra-freljord/assets/source/creatures/painted-20261024/draklornInquisitor/technical-v1/compare_and_audit.py
```

The first command exercises the real shared strict compiler plan twice per canonical recipe and writes only the new report's compiled subtree. The second verifies actual output checksums and creates fixed native1x comparisons, the root impulse proof, anatomy/gait observations and the coordinator handoff. Neither command stages or selects content. Original HoMM3 references are private read-only inputs and must not be redistributed.

The coordinator template requires: "Original HoMM3 is the visual authority; League/LoR supplies regional subjects and motifs." It also states: "Code may perform technical conversion, cropping, palette/alpha processing, fixed roots, masks, frame assembly and validation; artistic content must come from coherent painted 2D sources."
