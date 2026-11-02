# VCMI engine patches

These local VCMI engine patches fix how the computer opponent handles turns and
replans after losing a hero. They also add optional creature preview animations.

Each patch family includes editable changes, regression tests, preparation and
build helpers, upstream identifiers and exact file hashes. Keep these inputs in
Git; exclude extracted source trees and compiler output directories.

## Source chain

The recorded upstream VCMI commit is
`725ae80c42929ebbf6ccd620b38bd45ac32644c2` from
<https://github.com/vcmi/vcmi>. Its pinned submodules are:

| Submodule | Commit |
| --- | --- |
| `dependencies` | `68f3f22614a3b17c80aa603b0c013181db845048` |
| `test/googletest` | `b514bdc898e2951020cbdca1304b75f5950d1f59` |

Apply the three patches listed in
[`../../runeterra-freljord/engine-patches/patch-series.json`](../../runeterra-freljord/engine-patches/patch-series.json)
from the workspace's `runeterra-freljord/engine-patches/` directory, then the
Bandle families in this order:

1. `ai-turn-lifecycle/0004-ai-turn-lifecycle.patch` — turn ownership and expected
   movement cancellations, with server and opponent regression fixtures.
2. `hero-loss-replanning/0005-hero-loss-replanning.patch` — explicit cancellation
   and replanning after the moving hero is defeated.
3. `creature-previews/0006-creature-preview-animation.patch`, then
   `creature-previews/0007-preview-legacy-crop.patch` — the preview extensions.
4. `../../installer/manual/engine-patches/0008-invalidate-cached-task-batch.patch`
   — cached task invalidation, included in the later packaged runtime's recorded patch set.
5. `../../installer/manual/engine-patches/0009-preserve-hero-last-stack.patch`
   — the last-stack safeguard recovered by comparing the retained binary-build source tree.

The family `changes.json`, `baseline.json` where present, `provenance.json` and
`source-export-files.json` identify the exact reviewed inputs. The overlays are
exact source files, and the export manifests bind their bytes. Changing a pinned
overlay requires an updated source contract and a new run of the relevant checks.

## Reconstruct an isolated source tree

For a fresh public checkout, Python and Git can fetch the exact public VCMI
commit and its two pinned source submodules, then apply all nine hash-checked
patches without requiring any private source archive:

```powershell
python -m dev.engine_source --output build/engine-source
```

This command requires network access to the pinned official GitHub repositories.
Use a new directory under this checkout's `build/`. The tool refuses existing
destinations and redirected paths, preserves the upstream
license and notices, and writes `PATHS-SOURCE.json` recording the commits,
patches and changed-source hashes. A failed attempt retains an explicit
`PATHS-SOURCE-INCOMPLETE.json` marker and must not be treated as reconstructed
source. It neither compiles nor starts an engine or reads original game data.

The public route applies the reviewed diffs using LF line endings. It does not
alter the checked-in patches or historical CRLF source archives. The result is
editable patched source, not a claim of byte-identical reconstruction of a
historical source ZIP or of any distributed executable. Only the dependencies
and GoogleTest submodules are initialized, matching the documented local
client/server/test configuration with the launcher and Discord disabled.

The retained older preparation scripts offer a separate, historical exact-byte
route using the already-patched first-three-patch corresponding-source archive:

```text
vcmi-725ae80-patched-source-a168a7b34aef.zip
SHA-256: ecf04d296dcd02fc26219eae26749165fb2890022e4ae7454beb032945751346
```

From the workspace root, with that separately supplied exact archive:

```powershell
python runeterra-bandlecity/engine-patches/ai-turn-lifecycle/prepare_source.py --zip "<archive>" --destination src
python runeterra-bandlecity/engine-patches/hero-loss-replanning/prepare_source.py --zip "<archive>" --destination src --with-preview
```

Each helper refuses an existing destination and validates the archive, its
embedded source inventory, and the incremental before/after hashes before
writing a new source child. The first command reconstructs the fourth patch;
the second applies the fourth, fifth and declared preview overlay chain. They
are alternatives for the source family being investigated, not commands to
apply repeatedly over the same destination.

The archive and its download/source availability are prerequisites for these
older helpers; they do not fetch it. A generic upstream ZIP is not an
interchangeable input. The public route above is independent of that archive.

## Build and test

The existing Windows helpers expect the dependency/toolchain layout described
in the family READMEs and `runeterra-freljord/engine-patches/README.md`: MSVC
14.51, Windows SDK, CMake, Ninja and the pinned Conan dependencies. Their current
defaults refer to this development machine's toolchain and private test-data
paths; supplying only Python is insufficient.

Once those prerequisites are prepared, the fifth-family route is:

```powershell
python runeterra-bandlecity/engine-patches/hero-loss-replanning/build_candidate.py configure
python runeterra-bandlecity/engine-patches/hero-loss-replanning/build_candidate.py build --jobs 2
python runeterra-bandlecity/engine-patches/hero-loss-replanning/build_candidate.py test --filter "HeroLossReplanning.*:CreaturePreview.*"
```

These commands build local engine candidates and run native tests. They do not
install or select a game runtime. Each family README records test coverage and
the gameplay checks that remain pending.

## What belongs in the repository

Keep the compact patches, overlays, tests, exact source/build contracts and
licenses. `source-export-files.json` is the family's explicit compact export
allowlist; the Bandle source-export tests check that generated source copies,
builds, binaries and licensed game data stay excluded.

Exclude `b/`, `src/`, `src-reproduced-*`, Python caches and private test Data/user
directories. Preserve existing local working trees until their historical source
and build receipts have been accounted for. A patch bundle alone is not a
statement that a binary release satisfies corresponding-source obligations:
the distributed version also needs its matching upstream/dependency source,
build material and required notices. VCMI code retains its own GPL terms.
