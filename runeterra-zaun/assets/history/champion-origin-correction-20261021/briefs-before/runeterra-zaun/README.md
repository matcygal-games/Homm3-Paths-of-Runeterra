# Runeterra: Zaun

An additional Zaun town for VCMI, built in the Runeterra workspace with Demacia's
production and validation lessons but with its own roster, its own art contract and
its own namespace. It is a *third* faction, not a fork of Demacia: the Demacia and
Noxus sources, stages and release gates are untouched by everything in this
directory.

## What exists today

| Area | State |
| --- | --- |
| Faction, town, creatures, hero classes, heroes | authored configuration |
| Design ledgers (roster, balance, identity, town, lore, champions) | authored configuration |
| Native VCMI schema validation | passing |
| Scoped source build and source tests | passing, source-only, 67 tests |
| Own artwork | tier one authored and converted: 12 of 373 outputs, built-unreviewed |
| Native load, gameplay, siege, AI, save/reload | not run |
| Release packaging and installation | not run, blocked |

The strict status vocabulary is *design proposal*, *authored configuration*,
*runtime verified*, *release accepted*. Nothing here is above *authored
configuration*: the tier-one art is built but the native visual review is still
owed, and no Zaun battle has been played.

## Layout

```
runeterra-zaun/
  mod.json                    mod metadata; disabled by default
  content/                    native VCMI dictionaries (factions, creatures, heroClasses, heroes, spells, artifacts)
  design/                     decision ledgers (roster, balance, identity, town, lore, champions)
  assets/
    manifest.json             the required-output inventory, generated from the dictionaries
    recipes/                  production recipes; 12 delivered, 397 blocked on missing painted masters
    source/                   editable painted-master sources; the tier-one cohort is authored
    generated/                the native assets the conversion stage produced
  scripts/                    faction-local helpers (art recipes, art rig, composition, delivery, source tests, source rules, map fixture)
  tests/                      the scoped source test suite
  build/                      staged output and executed reports
```

## Commands

Run from the workspace root. The scoped pipeline needs the project environment
because it validates against the local VCMI schemas:

```powershell
.\runeterra-demacia\.venv\Scripts\python.exe -B scripts\runeterra.py --faction zaun doctor
.\runeterra-demacia\.venv\Scripts\python.exe -B scripts\runeterra.py --faction zaun art
.\runeterra-demacia\.venv\Scripts\python.exe -B scripts\runeterra.py --faction zaun build
.\runeterra-demacia\.venv\Scripts\python.exe -B scripts\runeterra.py --faction zaun validate
.\runeterra-demacia\.venv\Scripts\python.exe -B scripts\runeterra.py --faction zaun test
.\runeterra-demacia\.venv\Scripts\python.exe -B scripts\runeterra.py --faction zaun assets
.\runeterra-demacia\.venv\Scripts\python.exe -B scripts\runeterra.py --faction zaun package
```

The default faction is Demacia and its behaviour is unchanged. `--faction zaun`
selects the scoped development pipeline. These additional helpers exist:

```powershell
# native schema validation - needs the project environment (jsonschema)
.\runeterra-demacia\.venv\Scripts\python.exe -B -W ignore scripts\noxus_schema_check.py runeterra-zaun\content
python -B scripts\zaun_asset_manifest.py                          # regenerate the required-output inventory
python -B scripts\zaun_asset_manifest.py --check
python -B runeterra-zaun\scripts\art_recipes.py                   # regenerate the production recipes
python -B runeterra-zaun\scripts\art_recipes.py --check
```

The art production path is a separate, explicit chain. The rig renders the
authored subject, the composition applies the one whole-atlas correction and
writes the native canvases, the delivery pins every digest into the recipe and
the conversion stage turns a delivered recipe into a native asset:

```powershell
# author and render the tier-one cohort (needs Blender 4.5.9)
.\.tools\blender45\blender-4.5.9-windows-x64\blender.exe -b --factory-startup `
    --python runeterra-zaun\scripts\zaun_creature_rig.py -- `
    --project $PWD\runeterra-zaun --unit zaunThug --revision v1

python -B runeterra-zaun\scripts\zaun_art_compose.py --unit zaunThug   # native canvases
python -B runeterra-zaun\scripts\zaun_art_delivery.py --unit zaunThug  # pin the recipe
.\runeterra-demacia\.venv\Scripts\python.exe -B scripts\runeterra.py --faction zaun art
```

## The roster

Seven lines, base and upgrade, with the same movement and range category in both
variants:

| Tier | Line | Category | Identity |
| --- | --- | --- | --- |
| 1 | Zaun Thug / Chem Punk | walking melee | cheap street infantry, the cheap half of the town |
| 2 | Chem Ravager / Mutant Berserker | walking melee | shimmer-mutated brawler, native top-creature regeneration |
| 3 | Chemtech Construct / Reinforced Construct | ranged | pressure-nozzle shooter with finite ammunition |
| 4 | Chem-Baron Enforcer / Cybernetic Guard | walking melee | ordinary heavy contact unit; the upgrade adds the native three-headed fan strike |
| 5 | Chem-Baron Agent / Master Alchemist | walking melee, casts | one native Weakness charge, three-round duration |
| 6 | Augmentation Veteran / Chemtech Vanguard | walking melee | augmented veteran with the native long-tool reach over one empty hex |
| 7 | Apex Predator / Perfect Mutation | walking melee, two hex | lab-bred apex beast, native regeneration 10/15, KING 2, and an all-adjacent grab on the upgrade |

Composition in both armies: one shooter line, one walking melee line that also
casts, five further walking melee lines, no flying line. The tier seven is a
two-hex lab-bred creature and a
**declared project-fiction adaptation**: the official material does not describe a
canonical Zaun apex predator, so the creature belongs to this project's fiction and
is never presented as a Riot claim.

## The town

Thirty-six building states on **twenty independent sites** - one more site than the
native pattern, because the Fighting Pit is its own building and not a state of the
tier-seven dwelling:

| Site | Buildings | States |
| --- | --- | --- |
| Foundry Hall | villageHall, townHall, cityHall, capitol | 4 |
| Sump Rampart | fort, citadel, castle | 3 |
| Shimmer Institute | mageGuild1..mageGuild4 | 4 |
| Thug Quarter, Ravager Pens, Construct Workshop, Enforcer Yard, Reagent Store, Augmentation Rows, Labyrinth Hollow | dwellingLvl1..dwellingLvl7 and their upgrades | 14 |
| The Grog, Scrap Exchange, Ammo Foundry, Shimmer Factory, Sump Dock, Code of Progress | tavern, marketplace, blacksmith, resourceSilo, shipyard and ship, grail | 7 |
| Augmentation Workshop, Augmentation Clinic, The Sump, Fighting Pit | special1..special4 | 4 |

The five special buildings are audited: the Shimmer Factory produces one sulfur a
day, the Augmentation Workshop gates the tier-six upgrade, the Augmentation Clinic
gives every visiting hero ten mana once a week, The Sump grants one point of
Defence, and the Fighting Pit produces one hundred gold a day. The four hall
states carry four different names - Sumpgate Hall, Foundry Hall, Castboard Hall
and Chancellor's Hall - so the hall site is never one building relabelled four
times.

## The design and production briefs

The workspace root carries the end-to-end contract and the four production
briefs. They are part of the delivery, not notes:

| Document | Content |
| --- | --- |
| `RUNETERRA_ZAUN_PROJECT_PROMPT.txt` | the ten-section end-to-end implementation contract |
| `RUNETERRA_ZAUN_LORE_AND_ROSTER.md` | the lore synthesis, the evidence tiers, the canon/fiction boundary, the units, the champions and the measured distinctiveness analysis |
| `RUNETERRA_ZAUN_CREATURE_PROMPT.txt` | the fourteen unit briefs, the geometry and the action-group contract |
| `RUNETERRA_ZAUN_CHAMPION_PROMPT.txt` | the eighteen champion briefs, the two classes and the specialty contract |
| `RUNETERRA_ZAUN_TOWN_PROMPT.txt` | the twenty sites, the puzzle master and the own siege set |
| `RUNETERRA_ZAUN_IMAGE_ART_PROMPT.txt` | the umbrella art brief over the 373 required outputs and the 409 recipes |

## Rules this directory follows

- Everything Zaun owns lives under `runeterra/zaun/` and `Content/.../runeterra/zaun/`.
  A manifest entry outside that namespace is a readiness failure.
- No original Heroes III pixel is copied, renamed, recoloured or traced into a
  Zaun asset. Only the measured layout and rendering language are referenced.
- No Demacia or Noxus artwork, rig, pixel or compiled output is reused. The
  shared pipeline, the shared native mechanism vocabulary and the shared geometry
  contracts are reused by design; only the painted art has to be own work.
- The creature map sprite contract is 96x64 with pivot 64,63 and one standing
  frame. That is the Demacia house contract, not a measured native size: the
  native creature map frames measure 64x64. The creature battle canvas 450x400
  with pivot 197,266 and the hero class frames 150x175 and 96x64 were measured
  from the extracted original frames.
- A missing asset or a placeholder fails readiness. A rig render on its own is
  not art acceptance either: the pipeline exits 2 while art is missing and never
  stages a runnable mod, and a converted output stays *built-unreviewed* until a
  reviewer has seen it at native scale.
- Source tests, schema validation and loader-shaped checks are not gameplay,
  art or release acceptance.

## Blockers

1. **Most of the art is still missing.** Twelve of the 373 required outputs are
   built from authored art and recorded as *built-unreviewed*; the other 361 are
   missing and their 397 recipes are blocked on the missing painted master. The
   recipes on disk describe exactly what an artist has to paint, down to the
   native frame counts and canvases. The tier-one pair still owes the native
   visual review.
2. **No runtime evidence.** No Zaun battle, siege, construction, AI, save/reload
   or clean-install run has been executed. The desktop operator slot is reserved
   for the runtime agent; no Zaun window has been started.
3. **Unmeasured town footprints and an unexecuted map.** The town masks and
   adventure map states are authored from the measured native layout, but the own
   town art has to supply the final masks. The Zaun acceptance map exists as a
   source fixture with the Noxus prison bounds defect corrected, and the client
   has never loaded it.
4. **No release.** Packaging and installation are blocked by the art gate and by the
   ten acceptance categories that are still `not_run`.
