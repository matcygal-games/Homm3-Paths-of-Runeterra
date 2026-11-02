# Art guide

The visual target is the painted 2D look of original Heroes III: compact silhouettes, textured materials, restrained highlights and clear detail at the game's native resolution. Runeterra supplies the subjects, architecture, equipment and regional colours.

## References and style

Compare artwork with original Heroes III assets at the size players will see it. Look at perspective, lighting, anatomy, equipment, contact shadows and how each material reads against its background. Use League and Legends of Runeterra references for regional identity, and give base and upgraded troops distinct equipment and silhouettes.

## Creatures and animation

Start with an editable character sheet and a consistent scale and ground anchor. Each unit needs standing, fidget, movement, hit, defense, death, turning and directional attack poses. Add shooting, casting, takeoff and landing sequences where its abilities need them.

Check complete sequences at both facings. Follow the weight of the body, foot contact, equipment and shadows through the motion, including the return to idle. Preview portrait and recruitment crops separately from battle sprites.

## Towns and scenery

Design the complete town at 800 × 374 before separating its background and building layers. Buildings, roads, terraces and shorelines should share the same perspective and lighting. Reserve space for full silhouettes, foundations, entrances and upgraded states, then check empty, partial and fully built views.

## Files and review

Keep editable masters in `assets/source/`. Conversion recipes belong to the separate authoring inputs. The pipeline handles cropping, frame assembly, palette and alpha processing, masks and format conversion. Update the selected inputs, recipes and manifest together when artwork changes.

Include source credits, redistribution terms and native-size previews with an art contribution. Review the converted result in its town, adventure, battle or interface context. Conversion checks cover file correctness; in-game review covers appearance and motion.

See [production](production.md) for native formats, [heraldry](heraldry.md) for regional crests and [workspace requirements](workspace.md) for source handling.
