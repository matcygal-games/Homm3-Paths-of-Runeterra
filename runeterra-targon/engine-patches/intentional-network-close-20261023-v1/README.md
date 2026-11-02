Status: **authored configuration**. This is a separate, unapplied engine-source
correction candidate against official VCMI commit
`66fa496c6328a276c4eb14c0011b3a9d751dfac3`. No protected checkout, private engine
build, production stage, cache, native runtime or installed game was changed.
Only small copied-consumer C++ regression executables were compiled and run.

Problem and bounded correction
-----------------------------

Official CVCMIServer::onDisconnected logs ERROR before checking whether a game
connection remains. The authorized LobbyClientDisconnected applier first closes
the transport, then calls the existing clientDisconnected cleanup. Internal
transport close posts a disconnected callback; TCP close may cancel pending I/O.
The callback can consequently reach onDisconnected after an intentional close
and after the game connection has already been removed. The unconditional ERROR
also loses the supplied transport reason. These source behaviors are verified
against Git-blob identities in the official commit tree.

The separate patch changes exactly three files:

- `server/CVCMIServer.h`: weak shared-ownership identities for explicitly closed
  transports, plus a closeConnection method. No saved/network game-state layout
  or packet format is changed.
- `server/CVCMIServer.cpp`: closeConnection removes expired weak identities,
  records this exact transport BEFORE calling its native close method; rejected
  incoming connections use it too. onDisconnected recognizes only those recorded
  ownership identities and logs a descriptive DEBUG completion. Every other
  callback retains ERROR, now including errorMessage, followed by the unchanged
  native permission/applier/clientDisconnected cleanup route.
- `server/NetPacksLobbyServer.cpp`: the actual authorized disconnect applier calls
  closeConnection, then the existing clientDisconnected. Permission checks are
  unchanged; rejected client IDs, nonhost shutdown and dedicated-server shutdown
  requests cannot mark a transport. No broad server-state or string-match filter
  is added.

The registry uses weak control-block ownership, not a global shutdown flag, player
ID or raw address. It does not retain a transport. A later connection with the
same raw address but a different ownership block is not implicitly intentional.
Duplicate completions remain recognizable while a callback still holds the
transport. New close requests prune expired weak entries. If a transport fails
unexpectedly first, its first callback remains ERROR and performs native cleanup;
the explicit close performed during that cleanup identifies subsequent close
completions. A failure that races after an explicit close is not independently
distinguishable from close completion by the supplied API; the boundary is the
recorded per-transport close request, not a claim about network causality.

All inserted accesses are in the existing CVCMIServer network event path.
Official CVCMIServer::run delegates to NetworkHandler::run/context.run; callback
processing and authorized lobby appliers use that path. The candidate introduces
no additional thread or lock. Full engine integration must retain those existing
event-thread ownership assumptions. Its isolated tests do not establish arbitrary
concurrent calls from unrelated threads as supported behavior.

Evidence and limits
-------------------

The actual stock runtime full-calendar and focused-day2 runs both completed
naturally with correct measured stat deltas and retained the shutdown ERROR.
`observed-runtime-contexts.json` pins their raw logs/results and exact contexts.
The focused trace shows Received disconnection request, player connectionId1
disconnecting, Internal connection has been terminated, then the unconditional
server ERROR. This sequence supports the investigated lifecycle hazard. The raw
ERROR contains no transport identity, so it does not prove that the observed
callback belongs to the exact recorded request. A native replay with the applied
candidate, including an unrequested-disconnect control, is still required.
No existing runtime receipt is relabelled clean or accepted.

The historical Freljord `0001-track-requested-connection-closures.patch` was read
as a design reference. Its weak-ownership idea informs this candidate. Its
patched checkout, binaries, native conclusions and C++20 helper are not used as
compatible inputs. This candidate records intent at the actual validated close
operation and uses C++17-compatible standard containers directly; there is no new
header/CMake source-list requirement.

`provenance.json` pins fourteen exact official consumer/license files. Each
file's Git blob hash matches the parent's pinned complete official tree. The
existing immutable commit/tree receipts are inputs only; missing files were
fetched from their exact official commit URLs into this folder. Neither the
local editable vcmi-develop checkout nor Freljord is the patch's source authority.

Executed regressions
--------------------

`regression-result-v2.json`: both variants compiled with MSVC19.51, C++17.
The unchanged official bodies passed6/14 and failed8/14; patched bodies passed
14/14. Cases cover accepted requests, late/duplicate completions, synchronous
close-before-removal, first unexpected loss with authoritative player cleanup,
unknown loss after shutdown, rejected permissions, both two-peer completion
orders, rejected incoming connection, weak lifetime, raw-address/control-block
separation, valid host shutdown and actual InternalConnection queued completion.

Actual method bodies are extracted unchanged by `prepare_regression.py`:
onNewConnection/findConnection/onDisconnected/handleReceivedPack/clientDisconnected,
the real permission checker and authorized applier, the new close method and all
seven InternalConnection methods. The surrounding dependency fixtures replace
the game/library/logger/Asio scheduling infrastructure. Source assert conditions
are retained but the test fixture converts assert failures to caught exceptions
to avoid a CRT dialog. This is actual copied-consumer execution with controlled
dependencies, not a full C++ engine build, TCP/internal gameplay, networking
acceptance or proof that the observed native callback identity is fixed.

`mutation-results.json`: two compiled adverse changes were rejected: a broad
SHUTDOWN-state suppression hides unknown errors, and recording intent after close
breaks synchronous close ordering. `patch-apply-check-v2.json`: git apply --check
and application succeeded in an isolated three-file copy; resulting bytes match
all supplied patched files exactly with core.autocrlf=false.

Historical failures stay separate: initial wrong source filename enumeration;
first harness compilation's constexpr lambda capture error in tests/ and
regression-result.json; initial apply-check used global auto-CRLF and applied
successfully but failed exact byte equality. Final tests-v2 and apply-check-v2
preserve the original failures and do not overwrite their receipts.

Integration after independent review
------------------------------------

1. Keep the turn-lifecycle worker's current private source/build untouched until
   it reaches its coordinator-approved checkpoint. This candidate does not edit
   its AI/Nullkiller2 or client/Client.cpp changes. Coordinate a new combined
   source identity; do not reuse an old binary's attestation for new source.
2. Check exact source prerequisites in patch-inputs.json against official66fa.
   Apply `0001-track-explicit-server-connection-close-ownership.patch` only to a
   separately authorized engine source candidate after `git -c core.autocrlf=false
   apply --check <absolute patch>` succeeds. Preserve official LF input bytes.
   Do not apply to vcmi-develop, original installs or an in-progress worker build.
3. Reproduce copied-consumer tests using the supplied recipes in a fresh owned
   report revision. Recipes intentionally refuse existing result/output fixtures;
   preserve historical receipts. Build the full combined engine using the turn
   worker's reviewed native build closure only after coordinator authorization.
   This folder supplies no separate full engine pipeline or runtime override.
4. Bind actual client/server/library hashes and dependency inventory to the new
   official commit + both exact patch hashes. Re-run unchanged production loader,
   original-only and Targon natural-completion routes with raw diagnostics, plus
   a separately controlled unexpected peer-loss case. An unknown/unrequested loss
   must remain ERROR and preserve authoritative cleanup. Retain both peer-order
   controls where supported; never filter ERROR lines or weaken acceptance.
5. Acceptance requires actual intentional-close completion to identify its recorded
   connection and reach native clean shutdown, while unexpected errors remain
   visible. Source tests cannot close multiplayer, save/reload, full AI, human UI,
   art or release gates. Source/GPL and third-party redistribution obligations
   remain the coordinator's separate release review.

Reproduction commands used (workspace project Python)
-----------------------------------------------------

```
python fetch_inputs.py
python author_patch.py
python prepare_regression.py
python run_regression.py
python run_mutations.py
python check_patch.py
```

The commands operate below this assigned folder. Do not copy executables, object
files, disposable .git directories or private runtime receipts into a source
package. `handoff-files.json` is the explicit compact source/report allowlist with
hashes; workspace-only historical evidence remains preserved here.
