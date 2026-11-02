# Piltover painted siege source

Status: **authored configuration**. Production metadata is `painted-master-complete-unapproved`. Native gameplay, visual acceptance and redistribution rights remain unapproved.

The selected candidate is `compiled-candidate-v3/`: 32 own SGPI siege surfaces plus `towerLarge.png` (58 × 64) and `towerSmall.png` (32 × 32), derived from the actual own Warden Rifleman portrait. `candidate-recipes-v3/` contains the matching generic SDK recipes. These are candidate recipes under editable source, not active production selection.

Run `runeterra-demacia/.venv/Scripts/python.exe runeterra-piltover/assets/source/siege/painted-v1/assemble-v3.py` from the workspace root to reproduce the source crops, uniform resampling, placement and actual `create_compiler('piltover').plan()` conversion. It writes only this candidate source namespace and the assigned siege reports. It never stages, publishes or installs a mod.

Masters and exact built-in imagegen requests remain in their family directories. `generation-ledger.json` records selected versions and tool output identifiers. The tool did not expose its model identifier. No Blender, alternate 3D renderer, generated actors, code-built walls or code-fractured damage was used. Every structural damage state is painted in a genuine cohort master. Original Castle images supplied private geometry, camera, canvas and pivot references only; their pixels are not bundled here.

The candidate follows the protected native `BattleSiegeController` suffix and draw rules: 12 curtain states, two keep states and cap, two states and cap for each side tower, four drawbridge states, two static connectors, gate arch, background wall, background, dry moat and bank. Legacy extracted MNBR/MNOK images are unused by that consumer and are excluded.

The two static connectors use `master-v2.png`, which replaces their excessive long curtain portions with painted broken stubs. This fixes their earlier overdraw of destructible walls. The arch also uses v2: its dark recessed passage supports the native closed/blocked route, which draws no separate drawbridge image. The lower drawbridge, broken drawbridge and front chain are separate painted states. The keep cap crop excludes a neighboring ruined-state spill from the cohort master. Earlier masters, scripts, recipes and receipts remain history, and are not selected by v3.

The native-size closed/open and damaged/destroyed composites are 2D registration inspections, not gameplay screenshots. They show continuous intact wall joins and visible destroyed breaches against a new Piltovan dry courtyard. They contain no creature stand-ins. Tower shooter body placement, shots, front-cap occlusion, moat damage, siege targeting, every real gate transition and actual native crops still require current-build execution. Human art approval and rights review stay separate.

The generation references are private read-only inputs. Do not ship original Castle sheets or the official reference crest as raw redistributed art. The own painted Piltovan crest treatment remains subject to the project's explicit rights gate.
