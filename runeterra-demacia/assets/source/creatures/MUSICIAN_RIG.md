The current source candidate is `musician-rig-v6` for Resonance Adept and Harmonic Warden. This work prepares genuine three-dimensional motion guides. It has not produced or approved painted battle sprites and does not change any active recipe, manifest or staged mod.

Both editable Blender files contain the common fixed orthographic camera and 75 keyed physical poses, plus a corpse reference to the actual final death pose. Each character has 16 bones. The Adept has 65 weighted volumetric meshes; the Warden has 78. A shaped head uses an exact crop of its own selected `master-v2.png`. The instrument is a closed wooden resonator with separate strings, bridges, mallets and shoulder straps. The Warden adds plate, cloak and reinforced binding. The musicians remain project fiction, independent of Sona's unique etwahl.

The saved-source audit checks the actual reopened blends: vertex weights, geometric thickness, bone/prop lengths, floor penetration and final torso settling. The first versions exposed a corpse supported by an upright instrument, then a forward toe and stiff lower coat. These sources are preserved as rejected motion blocking. V6 drops the instrument beside the body, folds the arms, straightens the ankles and gives the split coat 80% waist / 20% thigh weights. Raw procedural surfaces and face projection are not finished art.

Run from the workspace root, substituting the other unit as needed:

```powershell
& .\runeterra-demacia\.venv\Scripts\python.exe .\runeterra-demacia\scripts\creature_resonance_rig.py --project .\runeterra-demacia --unit resonanceAdept --revision 6 --prepare
& .\.tools\blender45\blender-4.5.9-windows-x64\blender.exe --background --threads 4 --factory-startup --python-exit-code 2 --python .\runeterra-demacia\scripts\creature_resonance_rig.py -- --project .\runeterra-demacia --unit resonanceAdept --revision 6 --render-scope all
& .\runeterra-demacia\.venv\Scripts\python.exe .\runeterra-demacia\scripts\creature_resonance_rig.py --project .\runeterra-demacia --unit resonanceAdept --revision 6 --review
& .\runeterra-demacia\.venv\Scripts\python.exe .\runeterra-demacia\scripts\creature_resonance_atlases.py --project .\runeterra-demacia --unit resonanceAdept --revision 6
& .\.tools\blender45\blender-4.5.9-windows-x64\blender.exe --background --threads 2 --factory-startup --python-exit-code 2 --python .\runeterra-demacia\scripts\creature_resonance_source_audit.py -- --project .\runeterra-demacia --revision 6
& .\.tools\blender45\blender-4.5.9-windows-x64\blender.exe --background --threads 2 --factory-startup --python-exit-code 2 --python .\runeterra-demacia\assets\source\creatures\musician-projectile-probe-v1.py -- --project .\runeterra-demacia
```

Executed generator snapshots and own-input checksums are kept beside each blend. A changed generator must use a new explicit revision; it cannot overwrite an earlier executed snapshot. The renderer has no dependency on an image-generation service. Painted action generation is deliberately held until the native grounding review and the parent's ongoing native infantry/siege diagnostic are complete.

Each unit's `raw-action-atlases/` contains fourteen exact action atlases and fourteen padded copies. Cells retain the original 512 square camera. Padding uniformly downsamples that whole cell to 420 pixels and adds 46 transparent pixels on each side; it never crops or fits an individual figure. Layouts are 1x1 holding, 2x2 four-pose clips, 3x2 six-pose clips and 4x2 eight-pose playing clips. Actual source indices, timeline frames, full parameters, source checksums and identical ready/recovery endpoints are recorded per atlas. The corpse refers to final death frame5 instead of receiving a fabricated action atlas. Exact RGBA round trips and the actual padding transforms were checked for all 150 source cells.

The actual content uses ammunition 8 / 10 and `attackClimaxFrame: 5`. Local native source subtracts one, so the right mallet contacts the strings on zero-based index 4 of each eight-pose directional playing action. The normal physical projectile is emitted from a measured forward resonator edge; it is not a free spell. The probe records source frame, blend, camera/calibration and local engine-source hashes. Painted placement and both native facing directions still require validation before those provisional offsets can be accepted.
