# Regional production handbook

This guide covers regional content, asset preparation, VCMI integration and release. Start with the component's gameplay definitions and selected asset records. Full artwork regeneration also requires its separate authoring specifications and recipes, which define the roster, era, mechanics and deliverables.

## Lore and regional identity

Use official League region pages, biographies, stories and Riot releases, supplemented by Legends of Runeterra illustrations and worldbuilding. Research notes should include the source URL, title, available author/publication details, access date, response hash, reading coverage and supported claim. Keep summaries in original wording and distinguish canon, interpretation, project fiction and balance adaptations. Explain continuity choices where legacy material, Arcane, skin stories or different eras conflict.

Recruitable troops and champions need enduring ties to the region's communities, institutions or stories. Document each champion's upbringing, community, residence/allegiance, regional role, era, evidence, availability and primary home. Check existing factions for duplicate identities and portraits. Birthplace, a visit or a shared LoR gameplay region provides context but may need stronger supporting evidence.

Scenario/unlock characters need native availability rules and reachable map access. Adaptations of unique champions, companions or scarce beings into recruitable troops need an explicit lore basis. Describe project-created units as project fiction. For festivals such as Spirit Blossom, distinguish ritual and folklore from literal history and skin roles.

Translate lore into supported game rules. Flight, teleportation, damage type and other mechanics depend on the implemented native behavior; illustration poses and LoR keywords are design references.

## Art direction

Aim for painted 2D artwork that fits original Heroes III at native size. Runeterra supplies geography, architecture, anatomy, equipment and culture; Heroes III supplies the camera, compact silhouettes, textured materials, lighting, shadows, animation rhythm and interface framing.

Build a reference board from original-game assets and official regional illustrations. Use Castle as a shared interface/rendering reference and other original towns and creatures for relevant materials, scale and movement. Record native dimensions, offsets, crops, palette, alpha and ground contact. Pin LoR set/version and card identity for retrieved illustrations.

An asset brief should identify its category, native dimensions, original-game reference, regional palette/materials, camera, lighting and ground contact. Keep accents and magical light readable at game scale. Apply the same art direction to the whole faction:

- Towns, buildings and terrain share perspective, light, atmosphere, foundations and contact shadows.
- Troops, heroes and portraits retain consistent anatomy, equipment, proportions and materials across their different views.
- Siege and adventure objects match native tile/hex scale, footprints, depth, occlusion and ground contact.
- UI, icons, puzzles and effects use the original game's stone, parchment, metal, framing and contrast.

Review native-size assets alongside original references and in assembled game scenes. Record the version, reviewer findings and remaining corrections. See [art production](art.md) for asset preparation and [regional heraldry](heraldry.md) for crest placement. Every town and all fourteen troop variants need a recognizable regional crest in the appropriate native view.

## Town composition

Begin with a complete assembled town design showing its architecture and surroundings together. Review the composition before deriving the background, building states, masks, highlights and construction icons. Existing selected masters can be reused with their silhouettes, entrances, foundations and shadows integrated into the scene.

The town scene is **800 x 374**, displayed inside the original **800 x 600** interface. Use the original game's relatively frontal three-quarter perspective, elevated horizon and painted depth. Keep architecture legible across the scene, with readable doors/windows, varied footprints and useful paths between sites. Regional scale decisions should account for both landmark readability and foreground framing.

Plan sites using complete silhouettes, including towers, roofs, stairs, foundations, contact shadows and the largest replacement-state envelope. Give buildings level support and accessible entrances. Connect stairs between landings, and account for water, shores, retaining walls and incidental background architecture. Where a rebuild retains existing buildings, preserve their painted masters and hashes while adjusting placement/coherent scale and integrating the surrounding landscape.

About sixteen ordinary land sites is a useful composition budget, with regional exceptions documented in the specification. Seven dwelling chains use seven sites; hall, guild and fortification chains also share sites. Enumerate coastal, moored-vessel and Grail states separately. Shared institution sites must preserve native prerequisites, effects, tooltips, access and progression.

Keep functional building states on their corresponding layers. Review empty, early, partial, complete, base/upgrade and coastal configurations. Derive click masks/highlights from selected visible silhouettes and test exposed click regions, overlap, z-order and tooltips.

Replacement versus simultaneous rendering follows inherited building bases and the native consumer. When a moored ship replaces the Shipyard state, its selected image includes both dock and boat; independently rendered states need compatible depth and accessible clicks.

## Creature roster and balance

Provide seven base/upgrade pairs: fourteen distinct registered variants. For each line, record its lore/community basis, silhouette, equipment, battlefield role, movement, damage delivery, upgrade distinction, weakness and nearest original comparison.

Choose a regional mix of walking, ranged and obstacle-crossing roles with practical counterplay. Specify whether crossing uses native flight or verified teleportation. Shared mechanics can support distinct regional armies through equipment, doctrine and vulnerabilities.

Bases and upgrades should remain recognizably related. Show progression through armour coverage/materials, weapons, headgear, silhouette or posture while retaining coherent scale. Give each line a clear visual and tactical purpose.

Balance statistics, abilities and economy together: HP, attack/defense, damage, speed, shots, footprint, growth, recruitment/upgrade prices, stack ranges and AI/fight estimates. Compare measured original units and weekly armies; `DATA/CRTRAITS.TXT` supplies values omitted from JSON. Derive upgrade charges consistently from full prices. Check resource bottlenecks, build order, affordability and growth multipliers, and label provisional estimates.

## Animation and native resource reference

Use editable character sheets and a repeatable sprite recipe. Supply the actions required by each unit and native consumer: standing, fidget, walking/flight, hit, defense, death, turns and directional attacks, plus shooting, casting, takeoff or landing where applicable.

Walks need contact, passing and opposite-support phases with weight transfer. Attacks need preparation, contact/release and recovery. Maintain coherent anatomy, hands, equipment and costume through the sequence. Review both facings, complete loops, transition continuity, shadows and airborne clearance.

### Groups and frame indices

The current checkout uses these groups:

| Action | Group |
| --- | --- |
| DEATH | 5 |
| ATTACK_UP | 11 |
| ATTACK_FRONT | 12 |
| ATTACK_DOWN | 13 |
| Upper/front/lower shooting | 14/15/16 |
| Movement start/end | 20/21 |
| DEAD | 22 |

Verify the selected engine's enums and consumers when changing runtimes. Review the painted strike direction alongside its group assignment.

After collapse, the consumer switches from DEATH to the persistent DEAD pose. Record each unit's settled-corpse behavior. Ionia's painted revision requires group 22 to reproduce the final group-5 corpse pixels and differ from holding/alert poses; checks cover decoded RGB and alpha as well as visual review.

Native PNG frames with animation JSON are supported where the selected consumer provides them; a DEF compiler is optional. Standalone creature frame indices are zero-based and contiguous. Interface animations instead use their actual BuildingIDs/state indices. Follow the consumer's supported image/sequence layout.

### Roots, scale and framing

Keep one fixed scale and a consistent anatomical/projected ground root per battle cohort, with pose motion around that root. Document separate cameras/transforms for adventure and UI contexts. Alpha-bounds centres and lowest-toe measurements can move as a pose changes; a stable annotated root helps preserve torso position and natural stride. Metadata pivots describe placement but do not reposition PNG pixels.

Test creature-window crops with the actual preview-group selector at both installed faction-background sizes. Inspect holding/movement frames for clipped bodies/tools, root alignment and readable scale. Extended attack-preview clipping is a separate issue from clipped source artwork. Custom crop/preview extensions are explicit runtime dependencies.

Portraits use close heads, necks or upper bodies against painted regional scenery. Preserve the selected subject and scene ancestry for both sizes. Hero surfaces include **58 x 64** large and **48 x 32** small portraits where required by the consumer. Tight portrait crops can naturally omit a unit's crest when its ordinary battle view displays it.

### Turn and flight transitions

Some VCMI consumers play a first half-turn, flip/reposition the stack, then play a second half-turn. Prepare compatible boundary poses and review the complete `first half -> engine flip -> second half -> holding` sequence. A reversed genuine half-turn can serve the second phase when it matches the consumer.

Flight needs a coherent ordered downstroke/recovery loop, takeoff, hover offset and landing. Review `MOVING -> landing -> HOLDING` and takeoff at both facings. Calibrate fidget probability separately from action duration and movement speed, recording native tick quantization and observed playback.

### Adventure registration

In this checkout, `MapRenderer` maps source pixel `p` to:

```text
32 * (object anchor + (1,1)) + p - image dimensions
```

This is bottom-right canvas registration. Contacts **(80,60)** on a **96x64** adventure canvas and **(48,60)** on a **64x64** encounter canvas align. The four-pixel bottom margin is an authored convention rather than a universal anatomical pivot. Calibrate each resource role against its own native measurements and original encounter composition, documenting intentional reaction offsets.

A two-column template mask stamps only the rightmost **64 pixels**. A **96-wide** sprite therefore needs either a transparent first column or a compatible three-column visible mask. Check source pixels, visitability and obstacle footprints together. Mirror the actor around its root so both facings retain registration. Compact adventure poses help keep wings, weapons, capes and feet within the available canvas.

The checked-out Castle encounter binding is:

| Selector | Resource | Visible facing |
| --- | --- | --- |
| mapAttackFromRight | AvWattak frame 0 | Left |
| mapAttackFromLeft | AvWattak frame 1 | Right |

Use explicit visual-facing labels in recipes and tests.

### Projectiles

Calibrate release/climax from the shooter pose, camera and native left/right formulas. The current one-based `attackClimaxFrame=4` selects zero-based source frame **3**. Align the painted release and measured muzzle/grip with that frame while preserving windup, recoil and recovery.

Check upper, level and lower shots where supported, orientation, offsets, ammunition, range, walls and melee blocking. Observe both native facings. Damage type follows implementation, including for magical-looking physical missiles.

## Buildings, heroes and mechanics

Provide halls, fortifications, tavern, marketplace, blacksmith, resource production, mage access, seven dwelling chains, recruitment/upgrades, siege and required services. Preserve canonical building keys/library defaults, costs, ownership and reachable dependencies. Explain coastal restrictions, guild ceiling, special states, rare-resource choice and regional omissions.

A small set of regional institutions, usually around five, can express faction mechanics. Define each institution's costs, prerequisites, descriptions, owner/visitor rules, limits and executable effects. Account for inherited bonuses such as Grail growth and maintain an acyclic dependency graph.

Use a mechanics matrix with intended behavior, bounded rule, actual API/consumer, implementation, AI use, save/capture semantics and test. Native entities, bonuses and rewardable behavior are the first integration options, followed by documented Lua and essential isolated engine changes.

Specify stacking/strongest-only groups, caps, friendly-spell effects, durations, charges, action costs and exclusions. Spell failure, damage reduction, immunity and control prevention have distinct semantics. Training/resource services need cross-hero, split-stack, multi-town, capture and save/reload behavior. Check capacity before consuming claims, retain rewards after failed transfers/full armies, and provide AI-compatible events for automatic town-entry services.

Use registered might/magic classes with skill chances, primary progression, recruitment weights, starting armies/skills/spells and balanced specialties. Record each champion's eligibility, availability, specialty, implementation, approximation and behavioral test. Maps and recruitment respect the native limit of eight active heroes.

Portraits and specialty icons should communicate the selected champion and shipped mechanic at each consumer size. Implement spells/artifacts with costs, targeting, duration, effects, icons, tooltips, availability and AI behavior. Document reused native spells; register implemented nonempty collections.

## Asset inventory and provenance

The regional inventory covers:

- Town terrain, building states/layers, masks/highlights, construction icons, HALL/guild/service interfaces and selection/ownership states.
- Adventure-town fortification states, flags, entrances and visit/block masks.
- Fourteen creature battle/adventure sets, reaction facings, portraits, projectiles and effects.
- Champion portraits, specialty icons and compatible adventure appearances.
- Town icons, recruitment backgrounds and forty-eight puzzle pieces with native prefix, positions and reveal order where required.
- Siege background, wall/gate damage states, towers, moat/battlements, effects and configured tower shooter.
- Supported creature/spell/building sounds and a looping theme.

Derived assets must agree with their configured source, including the actual `towerShooter`. A replaced unit or champion also affects portraits, icons, armies, dwellings, maps, audio and package selections.

Separate editable sources, private references, selected recipes, generated cache, staging, reports and `dist/`. Track ID, entity/role, provenance, recipe, dimensions, groups/frames, root/scale, palette/alpha/shadows, output paths, dependencies, checksums, reviews and redistribution status. Pin selected masters by path and SHA-256, with one producer per output and matching recipe/manifest/selected/generated/staged bytes. Animation reviews bind every PNG through `frame_sha256`.

Resolve live dependency paths, including nested generation metadata, from the project root. Preserve raw provider receipts and historical comparisons. The provenance resolver distinguishes checksum-verified archive records from live inputs; live references still expand even when the same file also has an archival role.

Source exports include the minimal production/helper/test closure and reproduction steps. Validate portability from an extracted archive in an isolated interpreter without checkout imports or `sys.path` fallback. Check metadata, layered artwork, animation projects and ledgers for private paths; preserve raw receipts privately and verify pixels, layers, timing and dependencies after metadata cleanup. Path validation covers traversal, reparse escapes, Windows-ambiguous components and case collisions.

### Audio and rights

Check every audio mapping, decoding through EOF, theme restart/loop and audible native event playback. Preview formats such as WebM require actual game support.

Document deliberate references to installed original UI/audio, boats/moats and compatible shared hero appearances. Distributions exclude licensed archives, extracted frames/music, Riot/LoR illustrations, full stories and private boards. Retain credits, contributor terms, generation provenance and permission records. Access to a tool or API is separate from redistribution permission.

## VCMI integration and tools

Use scoped entities and globally namespaced resources:

```text
build/Mods/runeterra-<region>/
Content/{Sprites,Music,Sounds}/runeterra/<region>/
runeterra/<region>/creatures/<id>/{battle.json,map.json,large.png,small.png,attackLeft.png,attackRight.png}
```

Shared projectiles can use declared faction paths. Check global resource names as well as mod-folder names so original towns and other factions remain intact.

Register implemented collections in `mod.json` with actual dependency versions. Consult local `docs/modders/`, `config/schemas/`, original faction/creature examples and `config/buildingsLibrary.json`, including entity, animation, file, bonus, rewardable and Lua references. Native validation checks identifier/resource resolution beyond JSON schemas.

Use an existing compatible runtime where possible. Record client/server, DLL, configuration, Lua and essential-mod inventories; modified executables are distinct dependencies even when version strings match. Keep engine changes as separate patches outside the read-only `vcmi-develop/` reference checkout, with source revision, recipe, serialization/network compatibility and relevant regressions.

Engine build provenance includes the approved plan and pinned source/header/generated/tool/module/object/library dependencies before configure, compile and link. Account for generated bytes, response-file encoding/newlines and output-volume capacity. Runtime receipts identify the resulting binary and dependency inventory.

Forecast/asynchronous changes need consumer and lifetime tests: intended battle environment, stable unit identity/order through nested states, living/dead/enemy support, ammunition once per physical strike and live actor reacquisition after callbacks. Verify authoritative rewards and ledger changes for rejected/no-op/full-capacity outcomes, visitor changes, multiple towns, calendar reset and save/reload.

Useful tool capabilities:

| Tool | Scope |
| --- | --- |
| MMArchiveCLI | Archive listing/extraction, DEF extraction/testing and WebP previews; verify counts, palettes, shadows and PCX channels. |
| homm3data | DEF/LOD/PCX inspection with Pillow/NumPy; PNG-to-DEF compilation needs a separate compiler. |
| homm3-unpacker | JavaScript extraction and inspection. |
| mmarch | Archive, sound and checksum operations using its provisioned binary. |
| GrayFace/H3DefTool | Optional DEF compilation; keep generated HDL/archive writes in staging. |
| homm3tools | Map/campaign tooling. |

Inspect help, dependencies and side effects for the selected version. Sound matchers that rewrite creature JSON should operate on generated copies. Pin and export shared/out-of-tree helpers used by the production recipe.

## Build and package workflow

The shared production dispatcher is a separate maintainer tool excluded from a standard source checkout. Consult its installed help for registered faction selectors and adapter support. Demacia has a bespoke default backend. New slugs need dispatcher, manifest, rules, map and production integration.

The public prerequisite entry point is `python -m dev doctor --faction <registered-slug>`; it requires the separate production tools and reports an explicit error when they are unavailable. With those tools installed, run their documented commands from the workspace root in the pinned project environment, selecting the faction explicitly.

Production operations include `references`, `assets --resume`, `assets --check-built`, `build`, `validate`, `test`, `test --runtime`, `preview`, `preview --stop`, `package --source`, `package --development`, `package`, `install --vcmi-user-dir "<destination>"` and `all`. Adapter coverage varies; check installed help and handlers for the selected faction. A standard source checkout supports public contributor checks and source export; full production authoring requires the separate tools and inputs.

Builds convert deterministic selected inputs, validate dependency closure and atomically publish complete stages. Production signatures cover content, design, selections, sources, recipes, shared helpers and semantic dependencies. Changes to these inputs require refreshed signatures and affected observations. Runtime/package receipts bind the exact publication, map and runtime; store acceptance observations separately from production fingerprints.

Use the freshness controller to verify the complete unique source/stage/sandbox inventory at native and packaging boundaries. Incomplete conversions, changed generated bytes, sandbox mismatches and extra active files fail freshness checks. Keep the publication stable during a native test session.

Command results have specific scopes: `doctor` can exit zero while reporting missing prerequisites, and `assets --check-built` checks technical outputs. Required-stage failures propagate through validation, native checks and release packaging.

| Output | Requirements |
| --- | --- |
| Source archive | Editable, noninstallable sources, recipes, semantic JSON, helpers, pins and reproduction steps; verified dependency closure; private/local paths, licensed references, binaries and caches excluded. |
| Development archive | Fresh exact stage and matching clean full-loader evidence; local-development label; verified members, CRCs, hashes and layout. |
| Release package | All current release gates, approved art, redistribution/contributor clearance and matching scenario/interactive evidence. |
| Installation | Separate command with a named destination; preserve unrelated mods, original-game files and running sandboxes. |

## Maps and native testing

Provide compact showcase/construction access, resources, upgrades, legal sequential access to eligible/scenario heroes, an original-town opponent, siege and reachable victory. Extend valid maps and add focused mechanic scenarios where useful.

Validate object IDs, unique native decimal-suffix instance names where required, footprints, masks, roads, entrances, starts and objectives. Each player needs legal heroes and starting bonuses; artifacts need recipients. Check prisoner access and the eight-active-hero limit. Bound supplies, waves and events, including one-time versus weekly rewards, completed-day/deadline ordering and conjunctive objectives.

Inspect executable help before selecting probes. Supported examples include:

```text
<server> --version
<server> --help
<server> --dummy-run
<server> --creature-values
<client> --testmap "<registered-own-map>" --headless
```

Use isolated sandboxes and `mods.validation full`. Record runtime inventory, original/sandbox archive hashes, active mod/content-finalization evidence, map/publication hashes, checksummed raw logs, exit codes, timeouts and observed outcomes.

Sandbox directory bindings and environment apply from the first invocation, including version/help probes; include `userSavePath`. Keep original game files and reference inputs read-only. Snapshot private settings before launch and retain native-written settings afterward: VCMI may persist defaults, add core to a preset and store validated-mod checksums. Investigate unexpected source/runtime changes separately from expected private settings.

For human-player checks, start through New Game / Single Scenario; `--testmap` assigns AI control. Review full motion and actual interactions on the publication being tested. Capture results with matching stage/runtime details. Errors, crashes or timeouts make the diagnostic fail even after a victory result. Original-only controls help separate engine/harness defects from faction regressions.

## Acceptance and delivery

Track the faction's complete acceptance inventory in `tests/acceptance-evidence.json` or its configured equivalent. Record tested scope, stage, outcome, reviewer and remaining work. Technical validation, native behavior, visual review and rights clearance each contribute distinct evidence.

Release verification covers:

- Launcher/editor recognition, original and existing-town selection, unchanged resources/entities and documented save compatibility.
- Reachable building construction, correct prices/effects/ownership, art, masks, clicks, tooltips and replacement/coexistence, including coast/Grail.
- Recruitment/upgrades for all fourteen variants; complete actions, scale, roots, facings, timing, portraits, projectiles and tower shooter.
- Movement/crossing, obstacles/walls, ammunition/penalties, retaliation, targeting and AI behavior.
- Champion identities, portraits, classes, armies, specialties, availability and documented adaptations.
- Spell/service costs, caps/stacking, durations, full-capacity outcomes, weekly/capture and save/reload behavior.
- Siege damage, gates, moat, towers, shooting and graphics.
- AI building/recruitment/development, reachable map victory and clean shutdown.
- Native town/HALL, adventure, battle, recruitment and hero views; regional identity, readable upgrades and heraldry.
- Audible sound triggers and theme looping.
- Reproducible archives, clean install/removal, independent final art/evidence review, credits and contributor/redistribution clearance.

Use focused boundary, mutation, consumer, reproducibility and native tests appropriate to changed behavior. Refresh affected checks when inputs change. Keep unobserved categories pending.

Delivery includes the accepted installable mod with checksum/inventory; editable sources and reusable tools; regional/corrected specifications and lore decisions; mechanics/economy and champion documentation; runtime/reproduction guide; playable maps and results; native comparisons/screenshots; installation, compatibility, credits and rights documentation; and an accurate backlog/status.

