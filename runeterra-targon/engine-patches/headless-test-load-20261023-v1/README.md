# Headless test-save startup source handoff

Status: **authored configuration**. Official VCMI commit
`66fa496c6328a276c4eb14c0011b3a9d751dfac3`; GPL-2.0-or-later source notice/license
is retained at `upstream/license.txt`. Apply this fifth patch after the four
ordered project patches in `docs/ENGINE_BUILD.md`, in a fresh source copy.
Before `client/CServerHandler.cpp` is `973ddc90f8992454203e5ca58266e1d907aca0669e94f0ffbdddbf8265deb879`;
after is `4d85ca526a909d579bd4a8a7f38fc1995e84b32b3f626e6e6b738b1669b3c164`.

The patch avoids a LobbySetPlayer request for the non-player sentinel when the
test-save route already has no local human seat. Valid human unseating and the
unchanged native rejection of invalid/eliminated human seats remain. No packet,
serialization layout/version, map, town or ordinary human startup is changed.

`python -B run_controls.py --check-only` verifies the exact compact manifest,
re-extracts actual methods from the included complete support sources and checks
all fixture includes. In a fresh SHORT writable copy, run
`python -B run_controls.py --vcvars "<supplied-vcvars64.bat>" --revision v1`.
The actual explicit compiler environment is initialized there; no private
workspace, engine build or pre-existing compiler-environment receipt is required.
Compiler selection is recorded, not silently claimed to match another compiler.
Compile/run bounds are 60/10 seconds, output128MiB, reserve9GiB. Revisions are new
and old results are never overwritten. The fixture executes15 copied-consumer
controls and detects3 mutants. It substitutes bounded lobby/network/game-state
adapters and omits the documented unrelated legacy receiver tail after its
connection assignment. It does not execute VCMI transport or deserialize saves.

The immutable source-repair audit manifest deliberately also records private
inputs, objects, executable and raw logs. It is NOT this export selection. This
new compact selection contains text/source/notices only, with exact public
provenance. Source metadata and isolated controls do not establish authentic
reload, complete build, gameplay or release acceptance. Project artwork and
contributor/redistribution decisions remain separate.
