# Demacia

The Demacia town component for Heroes of Might and Magic III: Paths of Runeterra.

## Working on this component

Gameplay definitions are in `content/`. Keep unit, hero, building and scenario identifiers consistent when changing them. Artwork and source attribution stay with the assets.

| Path | Purpose |
| --- | --- |
| `content/` | Gameplay configuration |
| `assets/source/` | Editable artwork and retained source records |
| `assets/reviews/` | Asset review records |
| `assets/compiled/` | Local compiled images, animations and audio |
| `build/` | Local stages and build output |

Run the shared contributor checks from the repository root:

```powershell
python -m dev check
```

Regenerating component assets also requires its separate authoring tools and inputs, including component scripts, recipes and design contracts. The production tools resolve installed authoring inputs automatically and report missing prerequisites. Those inputs are not part of a standard source checkout.

Inspect the local production prerequisites with:

```powershell
python scripts/runeterra.py --faction demacia doctor
```


See the [development guide](../docs/DEVELOPMENT.md), [content guide](../docs/ADDING_CONTENT.md) and [art standards](../docs/standards/art.md). Building source does not update an existing game profile; prepare a fresh profile when testing changed content.
