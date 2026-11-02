# Local development

Use Windows and PowerShell for the full build workflow. CI uses Python 3.12. The quick checks need only Python's standard library. Component builds require separate maintainer production tools and authoring inputs, plus their pinned dependencies and external tools.

## Check a source checkout

From the repository root:

```powershell
python -m dev check
python -m dev --help
```

These commands check the shared developer tools without starting VCMI or reading game data. Build and test individual factions separately.

## Work with artwork

Artwork and audio use Git LFS through `.gitattributes`. Install Git LFS and run `git lfs install --local` before adding or changing assets. Use `git lfs pull` to download asset objects when the repository provides them. Code-only contributors can run the quick checks without artwork. Older repository history has not been converted to LFS; see [repository hygiene](REPOSITORY_HYGIENE.md) before publishing it.

## Prepare the production environment

Arrange the separate production tools and authoring inputs with the maintainers before building. They are excluded from a standard source checkout. When installed, their prerequisite inventory is available through:

```powershell
python -m dev doctor
python -m dev doctor --faction noxus
python -m dev doctor --world
```

`doctor` lists prerequisites and missing inputs; Demacia is the default faction. If the production tools are unavailable, it exits with an explicit error. Use the installed maintainer dispatcher's documented `build` command to compile a component.

Regenerating town and World assets requires separate authoring inputs and tools: production recipes, design contracts, component scripts and test suites. Local production commands resolve installed inputs automatically. These inputs are excluded from a standard source checkout; missing requirements stop the affected operation. Shared contributor checks remain available without them. Some regions also require external tools or references; inspect their README and doctor output before building.

The asset decoder is included in `vendor/homm3data/` under the MIT license. If you update it, keep the license and update the component checks that pin its file hashes.

For engine changes, reconstruct the editable patched source from pinned public upstream inputs:

```powershell
python -m dev.engine_source --output build/engine-source
```

This fetches the pinned engine and submodules, verifies seven patches, and applies them in order to a new directory. See the [engine source guide](../runeterra-bandlecity/engine-patches/README.md) for dependencies and build instructions. Reproducing a distributed executable still needs a separate binary comparison.

## Edit and verify a component

1. Locate its authored `content/` and `assets/source/` files. Arrange the separate authoring inputs with the maintainers if the change requires artwork regeneration.
2. Make the source change and update related identifiers, descriptions, references and credits together.
3. Run the component's documented source tests, asset checks and build command.
4. If the change affects gameplay or appearance, test the freshly built stage in an isolated VCMI profile and record what was observed.

The installed maintainer dispatcher exposes component `build` and `validate` operations. Select the component using its documented faction or world options. Include the commands, results and any remaining problems in your PR. See the [content guide](ADDING_CONTENT.md) and [shared standards](standards/workspace.md) for more detail.

## Run an existing game profile

Launch an existing installed or sealed profile with:

```powershell
python -m dev play --profile "<Paths of Runeterra profile directory>"
```

Set `PATHS_OF_RUNETERRA_PROFILE` to omit `--profile`. On Windows, the launcher also checks the default per-user installation directory. Sealed profiles use their own launcher and integrity checks. This command opens an existing profile; it does not build one or download game data.

## Prepare a combined development profile

Runtime work needs compatible VCMI binaries and your own compatible Heroes III data. Keep the original game installation read-only and use a separate output directory.

After preparing the required regional and World stages, use the separate maintainer profile-preparation tool. It requires explicit runtime, original-game input and separate output paths. Its `--help` describes stage and scenario options. You can set `HOMM3_PATH` instead of passing `--game-root`. Keep the resulting profile out of Git and public downloads: it may contain files from your game installation.

The full source-to-game build and installation still need testing on a clean machine. Rebuild existing profiles after changing source.

## Source and installer packaging

For public source, use `python -m dev source plan` to inspect the current tree and `python -m dev source export --output "<new directory>"` to export admitted files. These commands exclude private tooling and do not create an installable mod or a complete production authoring environment. The separate maintainer tooling also provides component-specific source packaging.

Use [repository hygiene](REPOSITORY_HYGIENE.md) before publishing source and [Windows installer](WINDOWS_INSTALLER.md) for packaging. Check [redistribution rights](RIGHTS_AND_RELEASE.md) for both.
