# World Systems

The World Systems adventure-map component for Heroes of Might and Magic III: Paths of Runeterra.

The component supplies random-map placement weights for 21 Living World sites,
including regional encounters, drake roosts and visitor locations. Placement
depends on the selected template's treasure ranges and the site's permitted
terrain, so a particular site is not guaranteed on every map. Wild Magic Lines
and Black Mist Hollow remain hand-placed fields. These rules add Runeterra sites;
they do not remove the original game's random-map objects or replace terrain.

## Working on this component

Gameplay definitions are in `content/`. Keep unit, hero, building and scenario identifiers consistent when changing them. Artwork and source attribution stay with the assets.

| Path | Purpose |
| --- | --- |
| `content/` | Gameplay configuration |
| `build/` | Local stages and build output |

Run the shared contributor checks from the repository root:

```powershell
python -m dev check
```

Regenerating component assets also requires its separate authoring tools and inputs, including component scripts, recipes and design contracts. The production tools resolve installed authoring inputs automatically and report missing prerequisites. Those inputs are not part of a standard source checkout.

See the [development guide](../docs/DEVELOPMENT.md), [content guide](../docs/ADDING_CONTENT.md) and [art standards](../docs/standards/art.md). Building source does not update an existing game profile; prepare a fresh profile when testing changed content.
