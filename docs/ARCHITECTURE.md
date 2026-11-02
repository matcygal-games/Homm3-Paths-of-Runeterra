# Project architecture

Each region has its own gameplay configuration and artwork. Shared tools assemble the available inputs into VCMI mods and combined play profiles.

## Component boundaries

| Component | Responsibility |
| --- | --- |
| `runeterra-<region>/` | A faction's gameplay configuration and artwork |
| `runeterra-world/` | Shared adventure-map content |
| `runeterra-world-systems/` | World systems and their source |
| `paths-of-runeterra/` | Shared mod and scenario configuration |
| `dev/` | Common contributor commands: checks, prerequisite inventory, launch and audit |
| `installer/` | Windows installer source and payload verification |
| `vendor/homm3data/` | Pinned MIT-licensed Heroes III asset decoder source |

Within a region, common directories are:

```text
content/          VCMI configuration
assets/source/    Editable masters and selected asset provenance
assets/compiled/  Compiled images, animations and audio; local output
build/            Generated stages and reports; local output
```

Directory details vary by component; check its README first. Build checks use file paths and hashes, so moving files also requires updating the tools, recipes and source exports that read them.

## Entry points

`python -m dev` provides public checks, publication audits, source exports and an existing-profile launcher. Its `doctor` command uses the separate maintainer dispatcher when installed and reports an explicit error when it is unavailable. Select a region with `--faction` or inspect the world pipeline with `--world`; the default faction is Demacia.

The shared `docs/standards/` describe content and build requirements. The production dispatcher, shared production helpers, detailed specifications, recipes, component tools and component test suites are separate maintainer authoring inputs. Missing required inputs stop the affected operation. A standard source checkout supports the public contributor commands; full production authoring requires the separate tools and inputs.

## Source, build and runtime

Building a component creates a stage containing its configuration and selected assets. A combined play profile adds the VCMI runtime and game data from the player's own Heroes III installation. Editing source files does not update an existing play profile; rebuild and assemble it again.

Check source files, in-game behavior and visual quality separately, using the same build when recording results.

Use [local development](DEVELOPMENT.md) for commands, [adding content](ADDING_CONTENT.md) for content changes and [repository hygiene](REPOSITORY_HYGIENE.md) for files to keep out of Git.
