# Ionia IL4 implementation candidate

Status: **authored configuration**. Ready for coordinator integration/review of
this bounded town source. No canonical, stage, launcher or native process was changed.

The approved full PNG is unchanged, including exact PNG bytes. There are 35 native
construction states, sixteen ordinary land sites, one optional coast and one
separate Grail site; all seven creature-tier plots remain distinct. Actual compiled
layers plus backdrop reproduce the approved full exactly. All 155 town recipe
candidates produced 235 configured outputs. The five existing painted adventure-map
producers are preserved byte-for-byte; this task does not replace siege or creatures.

`integration-packet.json` pins the actual source inventory, reports, recipe guards,
35 drawing-only x/y/z patches, proposed town design and expected manifest outputs.
Apply only those drawing fields to the current faction source; do not replace a
newer faction dictionary with the private fixture candidate. Check every before
hash first. Root alone integrates canonical recipes/design, rebuilds the real manifest
through the production CLI, stages and launches a production-fresh native instance.
The design keeps exactly sixteen ordinary `sites`; Coast/Grail are `special_sites`.

Reproduce from workspace root using the project Python, in this order:

```powershell
$townCandidate = 'runeterra-ionia/assets/source/town/complete-town-20261028-v1/approved-implementation-v2'
runeterra-demacia/.venv/Scripts/python.exe -B "$townCandidate/convert_repairs.py"
runeterra-demacia/.venv/Scripts/python.exe -B "$townCandidate/assemble.py"
runeterra-demacia/.venv/Scripts/python.exe -B "$townCandidate/compile_candidates.py"
runeterra-demacia/.venv/Scripts/python.exe -B "$townCandidate/physical_baseline.py"
runeterra-demacia/.venv/Scripts/python.exe -B "$townCandidate/verify_construction.py"
```

The current receipts are already executed, not a promised command list:
`physical-baseline-receipt.json`, `physical-negatives-v3/receipt.json`,
`source-replay-v2/receipt.json`, `construction-receipt.json` and
`compiler-receipt.json`, under the matching report subtree.
Use a fresh unique label/output directory for another replay/negative run;
never overwrite historical evidence. Do not run a producer over a released cohort
after edits: copy to a new version or re-establish all source/report pins first.

For inspection use `views/empty.png` and `views/full.png` (all sixty views are
pinned in the source inventory), per-state absence views, the genuine repair-native
studies, `physical-baseline/public-path-native-overlay.png`, exact projection cases,
and the source-role partition. Flat references include genuine painted hidden/rear
sources, executed prompts, technical mattes and producer scripts. The source replay
starts without prepared/runtime PNGs and matches the real collector closure.

The old approved-implementation-v1 packet, all 184 old source PNGs and 235 old
compiled outputs are preserved and checked by the seal. Its physical HOLD remains
historical. Current engineering passes do not grant independent art acceptance,
native click/gameplay acceptance or redistribution rights. Those checks belong to
the coordinator and the assigned independent reviewer.
