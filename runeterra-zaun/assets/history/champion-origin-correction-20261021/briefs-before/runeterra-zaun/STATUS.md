# Delivery status - 20 October 2026

**Zaun is an authored configuration. Nothing about it is runtime verified or release
accepted.** The strict status vocabulary applies: *design proposal*, *authored
configuration*, *runtime verified*, *release accepted*. The current evidence supports
*authored configuration* only. Twelve of the three hundred and seventy-three required
own outputs are now built from authored art and are recorded as *built-unreviewed*; the
remaining three hundred and sixty-one have no art, and no Zaun battle has been played.

## Current development stage

`3ba08e4f5e23823a32a72d9f84440dc55191bf9afdb96db5cedd24e2091db358`

One separate Zaun faction, seven dwelling chains, thirty-six building states on
**twenty independent sites**, five adventure map states, forty-eight puzzle
positions, an own siege definition, fourteen creatures, two hero classes and
eighteen heroes are authored. The creatures, classes and heroes validate against the
local VCMI per-entity schemas. Native spell books and artifacts are deliberately
empty and unregistered.

Roster, base and upgrade: Zaun Thug/Chem Punk, Chem Ravager/Mutant Berserker,
Chemtech Construct/Reinforced Construct, Chem-Baron Enforcer/Cybernetic Guard,
Chem-Baron Agent/Master Alchemist, Augmentation Veteran/Chemtech Vanguard and
Apex Predator/Perfect Mutation. Composition in both armies is one shooter line, one
walking melee line that also casts, and five further walking melee lines; there is
no flying line. The tier four is an ordinary heavy contact unit whose upgrade
adds the native three-headed fan strike, the tier six carries the native
long-tool reach over one empty hex, and the tier seven
is a two-hex lab-bred creature with native regeneration, the native KING 2 slayer
marker and, on the upgrade, the native all-adjacent grab. The final numbers are
designer estimates anchored to the measured native comparators, not native balance
observations.

## Executed evidence

- Source suite: **67 tests passed, 0 failures, 0 errors, 0 skips, exit 0**.
  [Log](build/reports/history/source-tests-1792523920724433900.log) and
  [result](build/reports/source-tests.json) are authoritative. The receipt records
  388 protected Demacia and VCMI source inputs unchanged.
- Art conversion: `scripts/runeterra.py --faction zaun art` -> exit 0, 12 own outputs
  converted, 0 errors, 397 recipes still blocked. The stage is new: the scoped
  factions had no conversion at all, because the Demacia converters
  (`runeterra-demacia/scripts/animation.py`, `raster.py`, `indexed_animation.py`)
  hardcode the Demacia namespace. `scripts/faction_artifacts.py` is that conversion
  with the namespace as a parameter, so a painted master of any faction now has a
  deterministic, resumable way into a native asset. It is file assembly only: it
  never paints, never invents artwork and never grants acceptance.
- Authored Zaun art: the tier-one pair **zaunThug** and **chemPunk** is authored and
  converted. `runeterra-zaun/scripts/zaun_creature_rig.py` builds a rigged, posed and
  rendered Zaunit subject in Blender 4.5.9 and renders every native action group;
  `zaun_art_compose.py` applies the single whole-atlas correction the art brief
  requires (one measured scale and one measured placement for the whole cohort, taken
  from the standing frame) and writes the native 450x400 frames, the 96x64 map sprite
  and the four raster masters; `zaun_art_delivery.py` pins every source digest and
  records the production route. The result is twelve own outputs - for each unit the
  52-frame battle animation, the map sprite, `large`, `small`, `attackLeft` and
  `attackRight` - with 106 animation frames in total, all `built-unreviewed` with the
  native visual review still pending. The review is a separate step: it needs a
  reviewer who can see the art, and this session had no image inspection, so no art
  is claimed as accepted.
- Native shadow contract: the creature and hero class battle recipes now declare
  `generateShadow` 1 and `generateOverlay` 1, and the adventure map cohorts declare
  0. The engine draws the shadow and the outline from the frame alpha
  (`client/render/ImageLocator.cpp`, `ShadowMode`/`OverlayMode`), so a battle sprite
  that paints its own shadow would be wrong, and the original Heroes III frames carry
  no painted shadow.
- Native schema validation: `runeterra-demacia/.venv/Scripts/python.exe -B -W ignore
  scripts/noxus_schema_check.py runeterra-zaun/content` -> `schema check passed for
  1 content root(s)`, exit 0.
- Source build: `scripts/runeterra.py --faction zaun build` -> exit 2, scope
  `incomplete-source-only-development`, staged true, runnable false, stage hash as
  above, **zero source-validation errors**. The build report carries 2619 errors:
  the 2617 art-gate errors of the asset closure plus the pipeline's own two
  bounded-scope notices, that only the source configuration and the converted own
  assets were staged so the mod is not loadable and no native loader acceptance
  exists, and that the demonstration map is staged as a source fixture only and has
  never been loaded by the client. The exit code is the honest art gate, not a
  failure of the configuration.
- Asset closure: 373 required own outputs, **361 missing**, 12 built. The 409 recipe
  files on disk are the 373 required outputs plus the 36 intermediate town
  construction icons that the indexed building icon sheet consumes; 12 of them are
  delivered and 397 are still blocked on their missing painted master. The read-only
  asset check reports zero missing recipes, zero duplicate producers and zero
  namespace violations; its 2617 errors are all art-gate classes, counted from the
  report and not assumed: 1498 missing painted sources, 397 blocked recipes, 361
  missing authored or generated sources and 361 assets with a missing or placeholder
  status. The manifest is generated deterministically from the dictionaries by
  `scripts/zaun_asset_manifest.py`, and `--check` is green against the current
  dictionaries.
- Production contracts: `runeterra-zaun/scripts/art_recipes.py --check` is green.
  The recipes carry the native geometry that was measured in this session: the
  creature battle canvas 450x400 with pivot 197,266, the hero class battle frame
  150x175 in the five `EHeroAnimType` groups with the native frame counts
  1/4/11/11/8, the hero class adventure frame 96x64 in the ten groups the engine
  reads (1/1/1/1/1/8/8/8/8/8), the building icon sheet indexed by the native
  building id and the 32 own siege images at the measured native sizes. The
  creature map sprite is **not** a measured native size: the native creature map
  frames measure 64x64, and the recipe deliberately uses the Demacia house
  contract of 96x64 with pivot 64,63 and a single standing frame. The hero editor
  animation was not extracted and measured in this session.
- Map fixture: `scripts/zaun_maps.py` builds the Zaun acceptance map
  as a source fixture: 36x36, four towns, the six ordinary champions in front of
  the construction town and the twelve scenario-only champions in neutral prisons
  on a bounded grid. The Noxus builder places its prisons at x = 4 + prisons * 4
  and leaves the 36 wide map from the ninth prison onwards; the Zaun builder
  checks every object against the map bounds before it writes. The fixture is
  deterministic and it has never been loaded by the client.
- Packaging: `scripts/runeterra.py --faction zaun package` -> exit 2, no archive created,
  not installable, and the release gate explicitly withheld. The eleven package
  errors are the ten acceptance categories, all `not_run`, plus the withheld
  release gate.
- Runtime: no Zaun runtime, no installation and no native loader run has been started.

## Corrections in this snapshot

- The scoped factions had no production conversion at all. The Demacia converters
  hardcode the Demacia namespace, so a painted master of another faction had no
  reproducible way into a native asset, and the pipeline could only validate.
  `scripts/faction_artifacts.py` is that conversion with the namespace as a
  parameter, and `scripts/runeterra.py --faction <faction> art` is the new stage
  that runs it. It converts only recipes that declare `production_status
  "delivered"`, it pins every source it reads, it refuses to change an accepted
  output, it is deterministic and resumable, and it records the result as
  *built-unreviewed*. The build stage now stages the converted own assets next to
  the source configuration, and says so.
- The battle sprites declared `generateShadow` 0 and `generateOverlay` 0. The engine
  draws the shadow and the outline from the frame alpha
  (`client/render/ImageLocator.cpp`), and the original Heroes III battle frames
  carry no painted shadow, so a Zaun creature would have stood on the battlefield
  without a shadow. The creature and hero class battle recipes now declare 1 and 1,
  the adventure map cohorts stay at 0 and 0.
- The tier-one art is authored and converted. The rig, the composition and the
  delivery live in `runeterra-zaun/scripts/zaun_creature_rig.py`,
  `zaun_art_compose.py` and `zaun_art_delivery.py`. The composition applies one
  measured scale and one measured placement to the whole cohort, so no frame is
  stretched on its own, and the cohort manifest is the master an animation recipe
  pins. The delivered state is *built-unreviewed*: this session cannot inspect
  images, so the native visual review is still owed and no art is claimed as
  accepted.
- The 2026-10-20 lore and roster correction pass was applied to the authored
  sources. The deep primary-source review and the cross-faction distinctiveness
  audit are in `review/`; where an active ledger disagreed with them, the active
  ledger was corrected and the dated review receipts were left unchanged. The
  corrections are: three mechanic collisions with the peer factions were
  resolved (the tier-four `ENEMY_DEFENCE_REDUCTION` armour cutter, the tier-six
  `DEFENSIVE_STANCE` defender and the upgraded tier-seven `TWO_HEX_ATTACK_BREATH`
  rear-hex strike) and the three lines were rebuilt around native bonuses that
  neither peer faction uses, the native `THREE_HEADED_ATTACK`, `LONG_WEAPON` and
  `ATTACKS_ALL_ADJACENT`; the champion biographies were corrected against the
  verified dossiers, including the Corki, Renata Glasc, Zeri, Janna, Singed and
  Blitzcrank affiliations; and the `KING 2` marker was restated as a slayer
  counterplay classification instead of immunity to damage. The mechanics are
  source-inspected, not executed, and the statistics are uncalibrated design
  numbers: no art, runtime or balance acceptance follows from this pass.
- The town hall slots were wrong: the Fighting Pit was merged with the tier-seven
  dwelling, so twenty independent sites fitted into nineteen slots. The Fighting Pit
  is now its own slot in the last hall row, and a source contract enforces the
  twenty-site, five-row, four-slot layout.
- The building icon sheet was indexed by the position in the authored building list.
  The native town screen reads a building icon by its native building id
  (`CAnimImage(buildingsIcons, building.getNum())` in
  `client/windows/CCastleInterface.cpp` and `client/windows/GUIClasses.cpp`), so the
  sheet is now indexed by the ids of the engine's building library, and a source
  contract compares the generator's map with `config/buildingsLibrary.json`.
- The hero class animation contract was guessed. The native class battle animation
  is 150x175 in five groups with the frame counts 1/4/11/11/8, and the class
  adventure animation is 96x64 in ten groups with the frame counts
  1/1/1/1/1/8/8/8/8/8; both were measured from the extracted original frames and are
  now pinned by a source contract.
- The creature map sprite was a guessed eight-frame walk loop. The native creature
  map sprite is a single standing frame; the recipe now matches, with the Demacia
  map pivot.
- Blitzcrank's specialty text claimed the Armorer-grade bonus reduces every damage
  source. The native damage calculator applies it to attack damage only, so the text
  now says melee and ranged attack damage and explicitly excludes spell damage.
- Ziggs' specialty text claimed shooters attack walls. `NO_WALL_PENALTY` removes the
  wall penalty for a shot at a defender behind the walls; it does not let a shooter
  attack walls. The text, the champion ledger and the balance ledger now say so.
- The claim that a catapult specialty would be inert in Zaun was wrong. The native
  siege catapult is a war machine that carries the native `CATAPULT` ability, and
  the native Ballistics skill grants the same bonus subtype, so the bonus is
  reachable. The ledger now records that the roster leaves it out because Ziggs
  already carries native Ballistics, not because it would not work.

- The tier-four roster ledger still claimed the armour-piercing rule had no native
  bonus type and was an open scripted mechanic, while the content already carried
  the native `ENEMY_DEFENCE_REDUCTION` bonus and the same ledger's own non-goal
  entry said the opposite. The roster entry now states the native route, the
  audited 10/20 percent values and the fact that the value premium is still
  unmeasured.
- The lore review had recorded two drifts in the active source: the Viktor
  biography carried the story title with an extra "The", and the lore ledger
  named the retired tier-three id `reinforcedChemtechConstruct` instead of the
  real `reinforcedConstruct`. Both are corrected in the active source; the
  historical review receipt is unchanged.
- The source suite asserted that nothing is accepted and that every recipe is
  blocked. Those were snapshot facts, not durable contracts, and they would have
  failed the first real painting. The suite now asserts internal consistency of
  every manifest entry and recipe, accepts a valid delivered state, and checks
  that a delivered entry names a file that exists with a matching hash. The
  delivery snapshot stays a dated statement in this file.
- The delivery-state checks were still written for the all-blocked snapshot and
  would have failed or crashed on a real delivery. The manifest check now
  understands the vocabulary the scoped pipeline enforces (`missing`,
  `built-unreviewed`, `accepted`) and only demands a passed native review and a
  cleared redistribution for `accepted`; a built-but-unreviewed file is a legal
  intermediate state. The recipe check is now type-aware: a raster recipe has no
  `frames` list and the indexed building sheet has no top-level `source_sha256`,
  so the old delivered branch would have raised a `KeyError` on the first real
  painting. Two new source contracts exercise the delivered path with synthetic
  raster, animation and indexed recipes instead of relying on the current empty
  state. The blocked check now also refuses a delivered output file on disk.
- The recipe generator refused to overwrite only a recipe whose
  `production_status` was not the blocked template. A malformed recipe file and
  a partially filled blocked recipe were both treated as regenerable and were
  silently destroyed. The generator now reports an unreadable recipe instead of
  replacing it, preserves any recipe that carries production work, and
  `--check` compares the CONTRACT of a delivered recipe - output path, canvas,
  pivot, action groups and frame counts - with the contract derived from the
  dictionaries, so a delivered recipe cannot drift away from the content
  unnoticed. The success message no longer claims that every recipe matches
  when some were preserved.
- The recipe generator overwrote every recipe unconditionally, so re-running it
  after a delivery would have destroyed the delivered work. It now refuses to
  overwrite a recipe that already carries delivered state, reports it, and
  requires an explicit `--force` to overwrite it.
- The shared manifest helper resolved an unknown output prefix to the last
  folder of its prefix table, so an unmatched output would have planned its
  recipe in the wrong directory. It now falls back to the recipe root.
- The Zaun rules crashed on a malformed tier-four bonus list and did not require
  the tier-five line to cast at all. Both are reported as errors now.
- The shared pipeline fell back to a `common.zip_bytes` helper that does not
  exist when a faction map module has no container builder of its own. The
  fallback now builds a deterministic archive directly, so a map module can
  never crash the build stage.

## Design and production documents

The design basis and the production briefs live at the workspace root and are
part of the delivery:

- `RUNETERRA_ZAUN_PROJECT_PROMPT.txt` - the end-to-end implementation contract,
  rewritten to the ten-section structure of the Demacia contract.
- `RUNETERRA_ZAUN_LORE_AND_ROSTER.md` - the lore synthesis, the three evidence
  tiers, the canon/fiction boundary, the fourteen units, the champion set and
  the measured cross-faction distinctiveness analysis.
- `RUNETERRA_ZAUN_CREATURE_PROMPT.txt` - the fourteen unit briefs, the geometry
  and the action-group contract.
- `RUNETERRA_ZAUN_CHAMPION_PROMPT.txt` - the eighteen champion briefs, the two
  classes, the specialty contract and the portrait rules.
- `RUNETERRA_ZAUN_TOWN_PROMPT.txt` - the twenty sites, the puzzle master and the
  own siege set.
- `RUNETERRA_ZAUN_IMAGE_ART_PROMPT.txt` - the umbrella art brief over the 373
  required outputs and the 409 recipes.

## Blockers

1. **Most of the art is still missing.** Twelve of the 373 required outputs are built
   from authored art and recorded as *built-unreviewed*; the other 361 are missing and
   their 397 recipes are blocked on the missing painted master. The recipes describe
   what has to be painted, at the native sizes and frame counts. The two units that
   exist still need the native visual review, and the rig-rendered frames have not
   been compared with the original rendering language by a reviewer.
2. **No runtime evidence.** No Zaun battle, siege, construction, AI, save/reload or
   clean-install run has been executed. The desktop operator slot is reserved for the
   runtime agent; no Zaun window has been started.
3. **The map fixture is authored but never executed.** The Zaun acceptance map
   exists as a source fixture with the Noxus bounds defect corrected, but no Zaun
   map has been loaded by the client, no footprint is measured and the map is not
   a playability claim.
4. **No release.** Packaging and installation are blocked by the art gate and by the
   ten acceptance categories that are still `not_run`.
