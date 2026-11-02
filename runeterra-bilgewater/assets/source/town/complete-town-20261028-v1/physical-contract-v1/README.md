# Bilgewater physical town contract

Status: **design proposal** until the source owner releases the complete frame and background cohort and the actual public consumer passes.

This folder owns technical physical annotations and their reproducible consumer checks only. Painted masters, selected building frames, recipe payloads, canonical content/design, shared helpers, generated canonical assets and stages remain under their assigned owners.

The shared town template requires:

> Before repainting a background, make a complete placement plan using the selected buildings' actual full silhouettes, roofs, towers, stairs, foundations and contact shadows.

> Rear buildings need level landings supporting their complete root, foundation and contact-shadow profiles. Stairs may connect landings between buildings or form a deliberate front entrance; they must not run beneath a building body or substitute for its level foundation.

The intended physical contract uses the existing unchanged `scripts/faction_town_layout.py` `silhouette-v2` consumer:

- All thirty-five actual states are assigned once to sixteen ordinary sites and explicit optional `coast` and `grail` sites.
- Actual all-state alpha-8 unions define site silhouettes; actual alpha-128 pixels define solid bodies. Envelopes are measured from those selected frames, not substitute rectangle geometry.
- Foundations trace semantic level contacts in the actual painted buildings. Doors and supported approaches reach one connected visible street network. Public stairs and external water stay separately annotated; they cannot be relabeled as level land to bless a bad placement.
- Static supported timber wharfs may be dry land infrastructure where the empty painting visibly contains the deck and support. External water remains water. Only explicit coastal deck/piling or moored-hull contacts use the native consumer's bounded marine exception.
- The native `config/buildingsLibrary.json` supplies `ship.upgrades: shipyard`; `CCastleBuildings::recreate()` groups states by their native base and selects the greatest upgrade distance. This replacement means the selected ship image must retain the complete dock-plus-boat state. The separate `structures.ship.builds: shipyard` field sets its click/buildable target in `CTownHandler::loadStructure()`. No ordinary service depends on the optional coastal site.
- Full, base, early, partial, coast, Grail and foreground-absent source assemblies must use the actual selected layers and drawing depths. A supported rear non-access footing may be projected behind a lower terrace only with the exact bounded mask, distinct physical levels and all required source evidence; doors and approaches are never waived.

After a valid complete baseline, meaningful controls will move a real selected building and its physical masks together onto fixed stairs, water and unsupported terrain; selected generated pixels and contract hashes will be updated with the mutation so failure cannot be attributed merely to stale pins. A disconnected/blocked route and protected entry control will exercise the actual consumer. Every attempt preserves raw results and restores the baseline exactly.

The isolated physical source collector and actual town compiler may be exercised without claiming a fresh complete faction stage. Missing legacy creature sources remain a separate full-mod admission prerequisite. No 3D source restoration, native process, stage publication or acceptance waiver is permitted here.
