# Rebuilding the turn-lifecycle engine candidate

Status: **authored configuration**. This handoff contains corresponding engine
patch/source/tests, selected SDK pins, a portable Windows build recipe and GPL
license text. It does not select a runtime, install a town or approve a release.

The original local execution records remain outside this public handoff. Their
private paths are not required by this recipe. All output goes to the explicitly
supplied new candidate directory. Existing dependencies are read-only.

## Inputs

- Windows x64, Python, Git and the pinned MSVC 14.51 / CMake / Ninja tools recorded
  in `public-provenance.json`. Supply the BuildTools installation root explicitly.
- The official VCMI dependency archive linked in that provenance file, with its
  recorded SHA-256. It remains an external dependency, not bundled engine content.
- Network access to the official VCMI repository and its two pinned gitlinks.
- At least 12 GiB capacity for the operation plus a 9 GiB free-space reserve.

The official archive stores packages using Conan's archive folder names. The SDK
preparation command matches exact package manifests and verifies every selected
payload before assigning the relative names used by the pinned CMake metadata.
It invokes no Conan process and never modifies an existing cache.

```powershell
python -I -B portable/prepare_sdk.py --archive "<official-sdk.txz>" --check-only
python -I -B portable/prepare_sdk.py --archive "<official-sdk.txz>" --output-root "<new-sdk-directory>"
```

The read-only archive check was executed: 22 exact packages, 16,306 payload files,
194,420,854 bytes all matched. Fresh extraction and a complete second engine
rebuild using this portable wrapper have not been claimed.

The 166 included dependency metadata text files use `<SDK_ROOT>` tokens. Their
canonical hashes bind the original metadata after only path-prefix and line-ending
normalization. The build recipe creates a relocated metadata derivative inside
the new candidate. Source package payload hashes remain exact byte hashes.
`selected-sdk-inputs.json` uses a directory table and compact records to preserve
all 16,472 selected payload/metadata pins without opaque compression.

## Source check and build

Run from the directory containing this handoff's `portable/` folder:

```powershell
python -I -B portable/native_build.py check --candidate-root "<new-build-directory>" --dependency-root "<sdk-directory>" --visual-studio-root "<BuildTools-directory>"
python -I -B portable/native_build.py prepare --candidate-root "<new-build-directory>" --dependency-root "<sdk-directory>" --visual-studio-root "<BuildTools-directory>"
python -I -B portable/native_build.py build --candidate-root "<new-build-directory>" --dependency-root "<sdk-directory>" --visual-studio-root "<BuildTools-directory>"
```

The process-free `check` was executed with isolated Python. It verifies the exact
sibling ownership helper, source tree, patch and tool hashes. Metadata relocation
was separately checked; it removed the old dependency prefix in all 166 files.

Preparation fetches the exact official commit, verifies all 3,592 source blobs
using Git's tracked line-ending rules, checks the two required gitlinks, applies
the turn patch and adds seven real AIStatus GoogleTests to the private test target.
The recipe builds coherent Release client, server, core, Lua, Nullkiller2, battle
AI and native tests, using parallelism two. It preserves a 9 GiB system/candidate
reserve, caps owned growth at 12 GiB and owns child processes through Windows jobs.
Linking does not execute tests because discovery uses PRE_TEST.

For a coordinator-approved combined candidate, append each additional isolated
patch explicitly using repeated `--additional-patch "<patch>"` arguments during
`prepare`. The order and hashes are recorded. This turn-only handoff does not
silently include a network or console correction from another patch family.

Run native tests only after configuring the five owned user directories and
legitimate resource inputs, coordinating with any existing native operator.
The build recipe deliberately does not launch a game or choose a runtime.

## Behavior and limits

EndTurn acknowledgements are associated with their submitting turn generation.
An old accepted reply cannot clear a newer turn; duplicate/unknown replies do not
change it. The old task stops retrying when its generation changes. Request
registration occurs before transport can deliver a reply. The invariant ERROR
remains enabled.

Retrying a rejection means an actual `PackageApplied.result == false` payload.
The official server reports true for some applier rejections in its non-activity
branch; this separate defect is not fixed by the turn patch.

The copied-consumer checks executed 15 cases: the unmodified source failed seven,
the candidate passed all fifteen, and three negative mutations were detected.
These fixtures are distinct from full native AI/gameplay tests. The included seven
GoogleTests exercise the actual AIStatus class when built with the real engine.
Use the current build receipt for their observed result; source presence alone
does not prove execution.

No map, army statistic, timeout, serialized state, packet format or authoritative
server rule is changed. Matching source revision is not a bit-for-bit publisher
binary attestation. Art, gameplay, rights and redistribution acceptance remain
separate requirements. Engine-derived source uses the included GPL license.
