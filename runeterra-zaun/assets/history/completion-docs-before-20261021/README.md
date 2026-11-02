# Runeterra: Zaun

A separate additional VCMI town, `runeterra-zaun:zaun`. Original towns, Demacia,
Noxus and Freljord remain independent. **Status: authored configuration.** No
Zaun feature is claimed runtime verified or release accepted.

## Current checkpoint - 21 October 2026

- Fourteen creatures, two shared hero classes, eleven local champions, 36 town
  construction states on twenty sites, five adventure town states and own siege.
- **335 of 345 required outputs compiled, all built-unreviewed; 10 missing.**
  The 381 recipes include 36 intermediate construction icons: 371 delivered,
  10 blocked. Genuine action painting continues; no missing action is replaced
  with an idle pose or an old rig prototype.
- **120 source tests passed**, zero failures/errors/skips. Native schema and
  deterministic conversion checks pass. The tested 388 protected Demacia/VCMI
  inputs were unchanged. These are bounded source checks, not game acceptance.
- Disabled development stage: `e17e117b95fbc96c422870a04a9fcadd2cd85e40d37aba4ac79701433e65d8f1`.
  All 1,073 generated physical files match staging exactly. Build and validation
  intentionally return 2 while art/review/runtime prerequisites remain incomplete.
- Ordinary release packaging was executed and refused. No installable Zaun
  release, native loader, gameplay, siege, AI or save/reload acceptance exists.

[STATUS.md](STATUS.md) and the [executed checkpoint](build/reports/art-implementation/20261021-chemtech-town-revision/checkpoint-1792611860217845200/checkpoint.json)
record the evidence and its limits. Current reports supersede these dated totals.

## Local champions only

Both a Zaun formative origin and an established local narrative are required.
Residence or a guest scenario alone is insufficient.

- Tavern: **Blitzcrank, Jinx, Dr. Mundo, Ekko**.
- Scenario-only: **Viktor, Warwick, Twitch, Zac, Zeri, Renata Glasc, Vi**.

Vi's established Zaun upbringing is retained alongside her later Piltover
Warden service. Singed, Urgot, Ziggs, Caitlyn, Corki and Heimerdinger are excluded
as foreign-origin/guest candidates. Janna is deferred because her emergence
location is unresolved under the strict origin-proof rule; she is not relabeled
as a foreign migrant. Prior definitions, 28 recipes and 28 generated portraits
are preserved outside live production. No portrait is reassigned to another hero.

Read the [origin policy](design/champion-origin.json),
[correction notes](docs/CHAMPION_ORIGINS_20261021.md) and
[current portrait board](assets/reviews/heroes/native-origin-selection-20261021/eleven-local-champions.png).
Historical eighteen-candidate lore reviews remain valid research receipts;
they are not the active hero list.

## Production

Run from the workspace root with the project environment:

```powershell
& "runeterra-demacia/.venv/Scripts/python.exe" -B scripts/runeterra.py --faction zaun doctor
& "runeterra-demacia/.venv/Scripts/python.exe" -B scripts/runeterra.py --faction zaun art --resume
& "runeterra-demacia/.venv/Scripts/python.exe" -B scripts/runeterra.py --faction zaun build
& "runeterra-demacia/.venv/Scripts/python.exe" -B scripts/runeterra.py --faction zaun test
& "runeterra-demacia/.venv/Scripts/python.exe" -B scripts/runeterra.py --faction zaun validate
& "runeterra-demacia/.venv/Scripts/python.exe" -B scripts/runeterra.py --faction zaun package
```

Sources are in `content/`, `design/`, `assets/source/` and `assets/recipes/`.
The manifest derives the required inventory from current source dictionaries.
`art` assembles delivered paintings into PNG/native animation JSON; it does not
paint or accept art. `--check` helpers validate current inventory/recipe contracts.
Preserve delivered recipes; never force-regenerate hand-edited source.

The old tier-one rig output was rejected as final art. Its 106 generated files
are quarantined in `assets/history/tier1-rig-prototype-retired-20261021/`;
`zaun_art_delivery.py` refuses to promote them. Versioned sources and exact
previous README/STATUS/briefs remain under `assets/history/`.

The default CLI faction remains Demacia. No original files are patched, no
original/other-faction pixels are copied into Zaun, and original resources are
referenced only where deliberately documented. Artwork redistribution clearance
and final native art review remain unresolved.

## Chemtech town revision - 21 October 2026

The new town is compiled with winding streets, larger foreground buildings and
green reagent glass, purple accents and brown industrial materials. All 36
building states, their masks/outlines, construction icons, adventure states and
town icons are selected together. Appropriate unit palette/action revisions are
also compiled for tiers one, two, three, five and seven; the four tier-four/six
battles and six class animations remain incomplete. Auxiliary palette matching
continues separately. No native game or final art acceptance is claimed.

See the [before/after and source review](docs/CHEMTECH_ART_REVISION_20261021.md).
The preceding origin-selection checkpoint is preserved as historical evidence.
