# Working with the source

Regional source lives in `runeterra-<region>/`; public contributor commands live in `dev/`. Shared production tools and the dispatcher are separate maintainer inputs excluded from a standard source checkout. Start with the region's README, design files and specifications. Its `STATUS.md` records earlier builds and tests; check their dates and source hashes when using those results.

## Protected inputs

Builds and tests use separate output directories so the original game installation, engine reference checkout and extracted reference assets remain unchanged. Keep editable masters and source records when replacing an asset. An archive should retain file checksums and a record of the original paths.

The [art guide](art.md) describes the painted 2D Heroes III direction. See [heraldry](heraldry.md) for regional crests and [production](production.md) for formats and build details.

## Scope and status

For a feature change, check the region's roster, setting, dependencies and related issues. Update configuration, descriptions, artwork selections and tests together where they describe the same feature.

The project uses four status labels:

| Label | Meaning |
| --- | --- |
| **design proposal** | Planned behavior or artwork |
| **authored configuration** | Source implementation, with testing still to complete |
| **runtime verified** | Behavior observed in a named VCMI build |
| **release accepted** | Required gameplay, visual and distribution reviews completed |

Record test results with the build and the behavior checked. Track remaining defects in `issues/`, and keep past test records with their original source hashes after an issue is closed.

## Source and release integrity

Edit `content/` directly and record design decisions with the change. Generated JSON should be deterministic, and recipes and manifests should identify the files used to build an asset. Asset regeneration requires the separate authoring inputs; path and checksum checks catch missing or changed inputs.

Use the documented CLI and pinned dependencies. Keep game data, private references, machine settings and caches in local storage. Test installation in a separate destination that preserves other mods. See [repository hygiene](../REPOSITORY_HYGIENE.md) and [release preparation](../RIGHTS_AND_RELEASE.md) before sharing files.

## Native execution

Use New Game / Single Scenario for manual playtests; `--testmap` gives control to the computer player. Test a freshly built stage in a separate profile and record the runtime version, map and source/build hashes.

Automated preview tools track the process and window they start and pause if ownership or focus changes. Keep the tested stage fixed until the run ends or reaches a safe checkpoint. `preview --stop` closes the preview's own watcher and window.

## Regional content

The regional specification defines the roster. The usual town has seven base/upgrade creature lines and fifteen ordinary skirmish heroes (`special: false`). Give each hero a clear regional role, availability, portrait, class, specialty and starting army. Document lore sources and distinguish canonical characters from project fiction or gameplay adaptations. Scenario-only characters have separate availability rules.
