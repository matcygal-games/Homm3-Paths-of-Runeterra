# Turn lifecycle repair candidate

Status: **authored configuration**. The selected Targon stage/runtime is unchanged.
This directory contains an isolated engine source patch, provenance and consumer
regressions. It is not a verified game runtime or a release.

The official GitHub commit API resolved
`66fa496c6328a276c4eb14c0011b3a9d751dfac3`, matching the selected runtime's
reported source revision. Exact source files were fetched through official raw
commit URLs. This does not establish a reproducible binary match with that runtime.
The protected local engine checkout differs and was not patched.

## Correction

The upstream AI uses one `havingTurn` boolean. A successful EndTurn acknowledgement
can arrive after the same AI receives its next turn, clearing the new turn. Its
retry loop can also submit another EndTurn after a newer turn opens.

The candidate records each EndTurn request's local turn generation under the
existing status mutex. Only an accepted acknowledgement belonging to the current
generation clears that turn. A prechecked generation-specific loop prevents the
old task retrying or first submitting after a turn replacement during cleanup.
Request callbacks are registered before transport can deliver a reply.

`PackageApplied.result == false` retains the turn and permits a retry. This is
specifically the acknowledgement payload rule: upstream CGameHandler incorrectly
reports success for some applier rejections. Activity-block rejection emits false,
but the non-activity branch calls `sendPackageResponse(true)` even after an applier
returns false. That separate server defect is documented, not silently repaired
or covered by the false-acknowledgement claim.

The existing invariant ERROR remains. No map, army, timeout, RNG, packet format,
serialized game state or authoritative server legality rule changes. Request
ownership records are erased after accepted or rejected matched acknowledgements;
unknown and duplicate acknowledgements do not clear a newer turn. Existing AI
finish/task cleanup remains intact.

## Executed component checks

- Pinned upstream consumers: 15 cases, seven failures.
- Patched consumers: the same 15 cases, zero failures.
- Three negative mutations were all detected: unscoped acknowledgements,
  unscoped retries and late request registration.
- `git apply --check` passes against the pinned fetched sources.

These compile verbatim selected actual AI/client methods and the AIStatus
declaration against minimal dependency fixtures. They do not reproduce complete
TBB scheduling, sockets, UI callbacks or native AI gameplay. Question-answer
methods are fixture dependencies, not executed native question semantics.
Initial fixture compile/link failures and the first candidate remain in `history/`.

`tests/native/TurnGenerationTest.cpp` supplies seven additional tests using the
actual AIStatus class for the complete isolated engine build. Their execution is
pending until an exact native receipt exists.

Reproduce component checks from the workspace root:

```powershell
runeterra-demacia/.venv/Scripts/python.exe -B runeterra-targon/engine-patches/turn-lifecycle-20261023-v1/prepare_regression.py
runeterra-demacia/.venv/Scripts/python.exe -B runeterra-targon/engine-patches/turn-lifecycle-20261023-v1/run_regression.py
runeterra-demacia/.venv/Scripts/python.exe -B runeterra-targon/engine-patches/turn-lifecycle-20261023-v1/run_mutations.py
```

## Native build boundary

The isolated build root is
`D:/runeterra-work/targon-engine-66fa-turn-20261023-v1/`. Its recorded limits are
12 GiB cumulative growth, a 9 GiB D reserve, a 9 GiB C reserve, parallelism two,
bounded logs/time and owned process-job cleanup. Keep the selected runtime and
production stage unchanged. Existing Freljord source/build objects, engine import
libraries and DLLs must not be mixed into the new candidate.

Existing third-party dependency/generated-toolchain inputs can be read after
inventorying their exact hashes. Do not regenerate Conan inputs or write to the
shared cache. Their official dependency gitlink matches the pinned source.
The complete source, required gitlinks and every source blob must be verified
before applying the patch in the private checkout.

`build_native_candidate.py prepare` records these boundaries and configures the
fresh Release SDL3 client/server/core/Lua/AI/native-test build. Its expensive
`build` step follows independent preflight review. GTest discovery uses PRE_TEST
so linking does not launch binaries. Native unit execution requires isolated
five-directory configuration and an isolated native session. Game/client/server
launches and runtime selection are separate validation steps.

The separate ordinary-close network ERROR has a source path through unconditional
server logging after an explicitly requested disconnect. The matched original-only
controls did not reproduce that ERROR. This candidate makes no shutdown logging
change and does not establish the Targon callback identity or resolve the separate
hero-exchange diagnostics.
