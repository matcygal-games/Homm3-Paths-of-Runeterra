# Zaun town and chemtech revision — 21 October 2026

The user requested a fuller, more immersive town layout, larger nearby buildings,
and visible chemtech in neon chemical green, purple and brown. The selected
source paintings replace the former rigid rows and amber-dominant scene.

![Town before and after](../assets/reviews/town/chemtech-v5-organic/before-after-complete-buildings.png)

The town keeps twenty independent sites and thirty-six construction states.
Winding streets connect irregular districts. Foreground workshops, the pub,
market and forge occupy more canvas; civic buildings and fortifications recede
behind them. Base dwellings are simpler and occupy less of their shared site
than their upgrades. The native construction menu remains separate from this
physical town layout.

Green light comes from reagent glass, pressure cells, connected pipes and
chemical runoff. Purple appears in cloth, glass and atmospheric depth; brown
brick, leather, timber, rust and copper retain their painted material texture.
Furnaces still emit amber heat. Civilian services retain recognizable equipment
and silhouettes instead of all becoming reactors.

The source policy states: “A new background alone does not complete the town
revision.” Accordingly, the selection includes the building layers, click masks,
outlines, construction icons, five four-frame adventure appearances and eight
town-state icons. The exact sources and placement limits are pinned in
[selection.json](../assets/source/town/chemtech-v4-buildings/selection.json).

All thirty-six state/construction boards and the overall composition were
inspected. Source geometry checks compare actual alpha-derived areas/outlines
and exposed click anchors after higher layers overlap. They are advisory source
checks; actual mouse hit testing and construction in VCMI remain pending.

The same palette applies to appropriate unit equipment. Dosing ampoules,
construct tanks, prosthetic cells and alchemists' reagents carry chemical green;
purple cloth and brown industrial materials support it. Ordinary workers keep
cheap equipment, living skin remains natural, and the laboratory predator stays
organic. Champion identity colors are preserved. Complete painted action cohorts
and matching auxiliary images are reviewed separately before selection.

The authoritative current policy is
[chemtech-art-direction.json](../design/chemtech-art-direction.json).
Some historical recipes preserve earlier embedded art prose because their
delivery receipts bind the exact bytes. That prose does not override the new
policy or the selected genuine painting/provenance. Future recipe generation
uses the new palette; it must preserve delivered work and strict action contracts.

Conversion and the disabled development stage are recorded in the latest
checkpoint under
`build/reports/art-implementation/20261021-chemtech-town-revision/`.
Use its actual child exit codes, file hashes and test receipt. This revision is
**authored configuration**, with assets **built-unreviewed**. It grants no
native gameplay, final art, installation or release acceptance.
