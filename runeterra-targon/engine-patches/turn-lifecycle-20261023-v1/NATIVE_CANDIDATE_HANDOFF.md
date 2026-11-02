# Native candidate handoff, 23 October 2026

Status: **authored configuration**. This is a locally compiled, patched candidate,
not the selected production runtime or a release acceptance result.

The isolated build uses official VCMI commit
`66fa496c6328a276c4eb14c0011b3a9d751dfac3`, all 3,592 verified source blobs and
the exact dependency/googletest gitlinks. Its ordered patch series contains the
turn-generation fix, independently reviewed intentional-close v2 fix and
independently reviewed headless-save 0003 fix. No protected checkout was edited.

The initial coherent build passed in 1,431.866 seconds, the network incremental
build in 40.179 seconds and the console incremental build in 16.880 seconds.
Every command used an owned job and completed cleanup. The build used parallelism
two and stayed within the recorded disk limits. All 22,990 enumerated
read-only dependency cache and generated-toolchain inputs matched their original
hashes after the builds; no Conan operation or old engine object/DLL/import-library
reuse was performed.

Seven filtered `TurnGenerationLifecycle.*` GoogleTests passed against the actual
native `vcmitest.exe`, with zero failures or disabled cases and exit 0. These
exercise the real compiled AIStatus consumer. The test executable statically
embeds core/AI objects; its 37 observed process modules are recorded separately.
The tests do not establish adventure AI, transport, battle, intentional-shutdown
or save/reload acceptance. False-acknowledgement handling means an actual
`PackageApplied.result == false`, not every server applier rejection.

The full candidate runtime is
`D:/runeterra-work/targon-engine-66fa-turn-20261023-v1/build/bin/`.
The four executable/DLL copies under historical candidate snapshots are not a
complete runtime. The post-build runtime inventory contains 831 files, including
the restored five-directory isolation configuration. Seventeen licensed Data
copies remain separate under the owned unit profile and are not redistribution
payload. All runtime files, nine modified/overlay source pins and those Data
copies were unchanged after the native tests. No game, GUI or listener was
launched and no runtime was selected.

The authoritative local handoff receipt is
`D:/runeterra-work/targon-engine-66fa-turn-20261023-v1/candidate-v3-turn-network-console/final-handoff.json`,
SHA-256 `7b93dd06d79426d88c7e60424964e24102acf46661f61de049bc4f57d9df7321`.
The native test receipt is
`D:/runeterra-work/targon-engine-66fa-turn-20261023-v1/native-unit-turn-generation-v1/result.json`,
SHA-256 `3415ea881f70d3958f1d9460ecc0c455583cd52990545849df84904db4901687`.
Raw commands, compiler output, module hashes, failed preparation history, original
candidate snapshots and dependency inventories are preserved in that private
root. `native-candidate-final-pointer.json` binds this source family to the receipt.

The compact portable corresponding-source export remains an explicit 257-file
manifest, SHA-256
`11211430f14e6e4c1f69694bbe6fe395ca1d8bd6616c0540272ae4b09cbfb87e`.
It contains the exact patch, official/patched sources, test sources, standalone
build/process/SDK recipes, selected dependency pins, canonical metadata and GPL
license. A full second build using the portable recipe has not been executed.
Original local operation drivers and private historical receipts are preserved
outside that public export.

The turn and intentional-close fixes still need controlled gameplay confirmation,
along with actual save-file creation and successful reload. These engine tests
do not establish full Targon gameplay, visual, audio or release acceptance.
