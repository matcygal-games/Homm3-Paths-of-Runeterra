# Additive headless save ownership correction

Status: **authored configuration**. This is a source-only candidate for console
revision v4, based on the currently executed console revision v3. The report's
candidate-v3/0003 names are local preparation revisions. The earlier public
headless-console-save family, its51-file selected manifest and native failures
remain unchanged. No private D source/build/cache, production, stage, native
process, stdin or original Data was changed by this work. No hero-exchange change
is included.

Apply the **incremental** `0003-select-connection-owned-headless-players.patch`,
SHA-256 `f341e785a793887eb8ebaacd7e809096ce802cd266aea7a85b96336dc92a9eba`,
to exact before-v3/client/ClientCommandManager.cpp SHA-256
`10d7a983e62d9e41bf20ab2f1402a87f40c89e5b30ab4a598c26ba137ed61062`.
Expected resulting complete file SHA-256:
`b552b406f8f00c01ee082eeafa42726811b45f0fe98d0d62744aeb9d55fff1ee`.
This small patch is not applied to the unmodified official66fa console source.
The coordinator owns composition/publication and must reject a differing baseline.

## Actual refusal and exact cause

The actual guarded run consumed one native stdin command after both real Pantheon
battle-completion markers. Its stdout SHA-256 is
`f385a59341137dedbe8705da044c885c952d907511c658cbad94b049337eb875`.
Line29696 contains the untrimmed refusal
`No owned player interface can save this gamePERFORMANCE: NK2 makeTurn took 2176 ms`.
No active save file, submitted request or serializer after-write success was
observed. This is a native command rejection, not a missing stdin delivery.
native-refusal-evidence-v1.json preserves selected original rows and exact parent
receipt/result hashes. It is evidence from the earlier operator run, not a new run.

The flawed rule is the headless loop's `server.isMyColor(player)`. Actual
CServerHandler::isMyColor delegates LobbyInfo::isClientColor, which recognizes
connected human player IDs. PlayerSettings::isControlledByAI means its connected
ID set is empty. Consequently a normal host-managed AI color is excluded even
though its adventure interface is local. `--testmap` removes the connected human
color through debugStartTest, while EntryPoint enables onlyai. The actual stdout
shows connection1 assigned neutral/red/blue and red/blue Nullkiller2 interfaces.

Native interface startup instead uses `getAllClientPlayers(connectionID)`. Its
actual implementation includes host-managed AI colors plus directly connected
colors, and neutral for the host. CVCMIServer::hasPlayerAt uses this same set.
The original36-case baseline fixture now compiles those real methods and exposes
five failures, including the actual host-AI save rejection. The old earlier
console fixture supplied an oversimplified owned set, which missed this distinction.
No per-predicate values were logged in the actual refusal, so exact executed
branch/value observations are not manufactured from the source diagnosis.

## Smallest corrected boundary

Only headless selection changes. Inside the existing exclusive CGameState::mutex
scope, reacquire a local current logicConnection and its public getConnection()
transport snapshot; reject the native INVALID connection ID and an expired weak
transport. Use the native getAllClientPlayers(current connectionID) set to filter
the already installed interfaces. Continue requiring a valid player color,
nonnull registered interface and actual live INGAME player state. Neutral,
spectator, foreign guest AI, absent or eliminated players remain ineligible.
Host ownership and connected-ID changes before dispatch are rechecked.

GameConnection::getConnection only locks the existing weak transport. Its presence
does **not** prove an open socket or physical liveness. The network-thread
execution/lifecycle ordering and native send path remain responsible for I/O.
The local strong snapshot prevents expiry during this bounded submission; it
does not redesign the connection or catch transport errors as success.

The human isMyColor/callback path, observer/replay and GAMEPLAY/context checks,
filename validation, GUI interfaceMutex, headless asio queue, exclusive state
mutex, request-counter synchronization against known NK2 shared-lock producers,
native SaveGame(filename,false), wait=false and "Save request submitted" wording
remain. No selection is captured before enqueue, no neutral impersonation and
no native serializer or network protocol change is introduced.

Server authorization must be stated narrowly: CVCMIServer::hasPlayerAt establishes
the engine's connection-owned set, but visitSaveGame itself does **not** call the
wrong-player/active-player checks. It invokes gh.save, unconditionally logs its
visitor success text and returns true. Native activity gating remains unchanged.
Therefore neither ACK, visitor text nor this local submission message proves a
saved file. Actual acceptance still requires CSaveFile's after-close written-byte
line, CGameHandler's inner after-write success, strict unchanged diagnostic logs,
new stable authentic file inspection/hash, actual reload and post-load resave.

## Exact source and controls

source-provenance-v5.json authenticates official66fa consumer files and records
read-only comparisons showing the actual current startup/ownership/getter bodies
match them. Current CClient::sendRequest deliberately differs from official: its
requestSent registration precedes transport send under the already approved
turn-lifecycle repair. A copied actual fragment matches that preserved repaired
body exactly; it is not mislabeled official. The earlier failed equality attempt
is retained with an authored failure note. This ownership patch leaves it intact.

run_consumers_v3.py compiles the complete copied save-command method alongside
actual PlayerSettings, LobbyInfo, CServerHandler::isMyColor,
CVCMIServer::hasPlayerAt, GameConnection::getConnection, native connection enums,
SaveGame and CCallback::save. Surrounding transport/request/thread dependencies
are bounded fixtures; no actual socket, native serialization or C++ full-client
build runs. The server-set fixture check does not pretend visitSaveGame itself
performs that authorization.

raw-consumer-controls/v2/result.json records36/36 candidate cases passing, five
baseline failures and eight compiled mutations detected. Cases retain the prior
26 command controls and add actual host-vs-human ownership, guest direct colors,
foreign mappings, host/connection revocation after enqueue, neutral exclusion,
INVALID IDs and expired weak transport. Original shared-lock and GUI-mutex
controls still execute. The first successful34-case receipt and all earlier
candidate/source drafts remain separate historical evidence.

Run project Python with `-B`, `run_consumers_v3.py --vcvars <supplied vcvars64.bat>
--revision vN` in a fresh reviewer-owned copy. All mandatory local source inputs
are included; no old private report/native log or D source is needed to compile
these controls. An installed compiler/developer environment is an explicit input.
Use a fresh revision; never overwrite these raw receipts. Selected manifest
contains source/recipes/license only; executables, objects, raw logs and earlier
drafts remain outside selection.

Next steps are independent source review, coordinator source export of this
explicit fourth family, a separately authorized coherent incremental build and
fresh loader/runtime binding to the newest published stage. This work does not
authorize a D build or native run and does not close actual save/load, champion,
services, UI, AI, art or release acceptance.

All copied VCMI sources retain their GNU GPL v2-or-later notices and exact source
provenance. The full license is official66fa/license.txt. The fixture and replay
recipe are project test sources accompanying these copied consumers.
