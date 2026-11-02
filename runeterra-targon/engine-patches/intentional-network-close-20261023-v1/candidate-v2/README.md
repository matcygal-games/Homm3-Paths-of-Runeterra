Status: **authored configuration**. This revised candidate supersedes the
unsynchronized sibling v1 candidate, which remains preserved as history.
Official base: VCMI66fa496c6328a276c4eb14c0011b3a9d751dfac3.

The original correction records a transport's weak ownership identity before
explicit server close and recognizes only that identity in onDisconnected.
Unexpected and unknown connection failures retain ERROR with their reason and
the original permission/applier/clientDisconnected cleanup. Rejected commands
cannot mark intent. Both actual authorized disconnect and rejected incoming
connection close use the same closeConnection method.

Independent review found that the initial event-thread assumption was incomplete:
NetworkHandler::createInternalConnection calls NetworkServer::receiveInternalConnection
synchronously, while client ServerThreadRunner can already be running the server
event loop. A non-lobby rejection can therefore reach the close registry from a
different thread. Official NetworkServer.cpp and client/ServerRunner.cpp are now
included among the sixteen Git-blob-verified consumer inputs.

This revision protects EVERY weak-registry prune, erase, insertion and lookup
with requestedConnectionClosuresMutex. Each scoped lock is released before the
transport's close(), completion logging, permission application or other cleanup.
A synchronous onDisconnected callback therefore cannot deadlock on the registry.
The candidate does not promise that all other server fields or arbitrary lobby
operations are thread-safe; only the introduced registry is synchronized. Weak
ownership identity, lifetime and unexpected-error semantics are unchanged.

The standalone patch applies directly to the same official three source files:
server/CVCMIServer.h, server/CVCMIServer.cpp, server/NetPacksLobbyServer.cpp.
It replaces v1; do not stack both network patches. No new CMake entry or source
header is required. No saved game or network packet representation changes.
This source was not applied to the turn worker's private source/build. No full
engine build, native VCMI launch, cache edit, Data copy or stage change occurred.

Executed copied-consumer regressions are in regression-result-v3.json. The
patched actual method bodies passed16/16. The unchanged official baseline ran
the original fourteen cases: six passed, eight failed. The two new mutex-specific
cases are not applicable to its missing mutex and are explicitly not counted.
One new case concurrently prunes/inserts and looks up known transport completions;
another verifies both writer and reader block behind the held registry mutex.
The original reentrant, unexpected-loss, duplicate, two-peer ordering, permission,
weak-lifetime/control-block and actual InternalConnection queued cases remain.
Test logger writes use their own mutex, close counters are atomic, transport
instances are per-thread, and the fixture's task queue is never accessed concurrently.

These compile extracted real consumer bodies against controlled dependencies.
They are not a full engine build, native TCP, native AI or gameplay acceptance.
Source assert conditions become caught test exceptions to avoid CRT dialogs.
The copied source files are CRLF on Windows; extracted-consumers-v3 records an
LF-normalized generation hash, while public summaries record actual raw bytes.
The previous v2 runner receipt erroneously counted two uncompiled baseline test
names as empty successes; that receipt is preserved, and v3 verifies a PASS row
for each requested case and excludes nonapplicable baseline cases.

Three compiled synchronization mutations are rejected: missing writer lock,
missing reader lock, and holding the lock across reentrant close. The last uses
a bounded isolated test and rejects the detected recursive-lock deadlock; its
three-second timeout also kills/waits only the regression child if needed.
The v1 broad-shutdown/late-intent mutations remain historical controls. Exact
git apply --check and applied-byte equality are recorded in patch-apply-check-v2.

The two stock-runtime shutdown observations retain their raw ERRORs in the
parent folder's observed-runtime-contexts.json. Their request/callback identity
association remains inferred: those ERROR lines contain no exact transport ID.
No old run is relabelled clean. Actual candidate native replay and an unexpected
peer-loss control remain required before any gameplay promotion.

After independent review, the coordinator may check this patch against a separately
authorized official66fa source candidate, combine it with the reviewed turn patch
at a safe build checkpoint, and use that worker's existing build closure. Do not
modify an in-progress private build, protected vcmi-develop source or installed
runtime. Bind new client/server/library hashes and both patch hashes to native
loader, natural-completion and unexpected-loss controls with all raw diagnostics.
Never filter errors or weaken acceptance. Save/network/release gates stay open.

Reproduction uses the project Python on prepare_regression.py, run_regression.py,
run_mutations.py and check_patch.py in a fresh report revision. Exact upstream
files plus the patch regenerate candidate source using git with core.autocrlf=false.
The scripts refuse historical result/apply-check outputs. Public source export
must use this revision's explicit manifest, preserving v1 evidence in the workspace.
GPL source/license obligations remain subject to separate release review.
