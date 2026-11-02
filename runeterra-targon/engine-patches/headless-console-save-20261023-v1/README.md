# Headless console save correction candidate

Status: **authored configuration**. This is an isolated GPL engine patch against
official VCMI commit `66fa496c6328a276c4eb14c0011b3a9d751dfac3`. It is not selected,
linked into the active runtime, **runtime verified**, or **release accepted**.
The protected checkout, active private engine build and town stage are unchanged.

The template requires: "Use native behavior before optional engine work." The
existing supported client console command is the repair target. The compiled Lua
registry has no save API, and AI-only play does not create a human interface or
run human-driven autosaves. No new Lua hook, test packet, polling autosave or
scenario-specific save trigger is introduced.

## Selected correction

Use `0003-make-console-save-use-owned-headless-player.patch`,
`patched-v3/client/ClientCommandManager.cpp`, `source-provenance-v4.json` and
`selected-manifest.json`. Older patches, intermediate copied outputs and raw
receipts are historical evidence outside the selected handoff.

Upstream `handleSaveCommand` tests only `GAME->server().client`, then dereferences
`GAME->interface()->cb`. Headless play has no `CPlayerInterface`, so that path
cannot safely create a native save. It also prints "Game saved as" immediately
after submitting a request, before the server attempts serialization.

The candidate changes one production file:

- Validate one nonempty relative resource filename; reject extra arguments,
  traversal/absolute paths, forbidden filename characters and embedded controls.
  Preserve accepted UTF-8 bytes and native SaveGame filename handling.
- Keep normal human `CCallback::save(filename,false)`. Both actual command callers
  are workers: the terminal console loop and the detached in-game command worker.
  Serialize their GUI route under existing `ENGINE->interfaceMutex`, following
  `handleControlaiCommand`'s precedent. This route does not enqueue the save on
  the SDL task queue. Existing in-game chat output still uses its existing queue;
  its wake ordering is not repaired or accepted here.
- With no graphical engine, post the value-only save task on the existing
  `INetworkHandler::getContext()` using actual `boost::asio::post`. Reacquire
  current game/client/connection/replay state inside the network task. Capture
  no interface, client, callback or command-manager pointer.
- Select only a valid, live player with a nonnull locally registered adventure
  interface and actual local network ownership. Never choose neutral, spectator,
  eliminated or foreign players. Human callback ownership and exact interface
  registration are checked too.
- Hold existing `CGameState::mutex` exclusively during headless player selection
  and submission. Actual selected Nullkiller2 request producers hold its shared
  side and release it while waiting for replies. This prevents the added producer
  racing their plain request counter. Submit with `waitTillRealize=false`: the
  network thread must remain available to receive acknowledgments.
- Emit only "Save request submitted" after submission. Rejected/blocked requests,
  serializer failures and dropped/stopped queues do not establish a save.

The existing `SaveGame` fields, serialization, callback, local-player selection
authority, transport, server activity blocking, save chunks and loading protocol
are unchanged. There is no bypass for an active visit, question or battle.
The server may reject a request while the current activity blocks packets.

## Source and protocol authority

`source-provenance-v4.json` pins38 exact official source inputs by SHA-256, Git
blob identity and official commit URL. The copied complete official tree is
SHA-256 `775085011d61128840a881fd065938deebba81650e2af6cad0c6876da95b5182`.
The active private build contains another owner's turn patch: its changed files
were not adopted as official input. Authenticated original Client/NK2 files are
kept in this candidate's own `upstream/`.

Key consumers are the console entry/callers, `GameEngine`/SDL input handlers,
`CServerHandler` network context/state/lifetime, `Client` request/ownership setup,
`CGameState`/`UnlockGuard` and NK2 shared-lock/wait discipline,
`CCallback::save`, native `SaveGame`, `GameConnection::sendPack`,
`ApplyGhNetPackVisitor::visitSaveGame`, `CGameHandler::save` and activity blocking.
`GameConnection::sendPack` already serializes transport writes under its write
mutex. This is source identity and consumer analysis, not publisher attestation
that the stock executable was built reproducibly from these files.

## Executed component checks

The final `raw-receipts/v3/result.json` records actual MSVC compilation of verbatim
console consumers, native SaveGame definition and `CCallback::save` against small
dependency fixtures:

- Patched consumer: **26 cases, zero failures**.
- Upstream human control: one failure exposing unsynchronized command submission.
  The known headless null dereference was not executed as an access violation.
- Six independently damaged candidates fail: observer bypass, foreign ownership,
  missing AI lock, missing GUI lock, false saved message and disabled headless
  route. Each compiles; the consumer controls detect each mutation.
- `git apply --check` passes against the authenticated copied inputs.

Controls cover native request fields and callback routing, GUI mutex ownership,
headless owner-thread dispatch, a competing AI reader and held shared-lock
release/resumption, absent game/client/connection/state, disconnect and replay
changes after enqueue, spectator/neutral/foreign/null/eliminated player cases,
finite filename validation and preserved valid filename bytes.

These are **compiled copied-consumer controls**. The queue/client/player fixtures
are not a real VCMI socket, AI plugin, SDL lifecycle, serializer, server activity,
save file or gameplay. No full engine configure/build/link, selected runtime
change, game launch, stdin command, Data copy or desktop operation was performed
by this owner. Raw paths/compiler commands/artifacts stay under `raw-receipts/`
and are excluded from the portable selected manifest. `consumer-verification.json`
contains the public summary and raw-receipt hash without host paths.

## Portable reproduction and integration boundary

The selected source handoff is GPL-2.0-or-later; see `LICENSE.md`, upstream full
license and author notices. It contains no game Data, executable, object file,
private host path or generated test build. Apply only after coordinator and
independent review. This owner has no authority to change the active private
checkout or integrate with the other owner's in-progress build.

From this directory, with Python and Git available:

```
python -B prepare_patch.py --official-source upstream
python -B run_regression.py --vcvars <VCVARS64.BAT> --revision v4
git -C upstream apply --check ../0003-make-console-save-use-owned-headless-player.patch
```

Every new execution needs a new raw-receipt revision. `prepare_patch.py` rejects
changed preserved outputs and authenticates every copied source against the
fixed official tree. Build outputs remain separate from selected inputs.

## Exact unresolved limits

The new producer's lock is justified for the selected NK2 shared-lock discipline.
This is not a repair of every arbitrary AI plugin or all existing client request
counter concurrency. Native startup, shutdown, global console lifetime, plugin
lock behavior and actual scheduler execution still need complete-runtime testing.
The headless task checks current state at execution; it does not promise an exact
calendar checkpoint from the instant terminal input was read. The operator must
observe and bind the actual saved date/state to its acceptance fixture.

The server visitor unconditionally prints "Game has been saved as" and reports
success even if `CGameHandler::save` caught a serializer exception. Therefore
neither that message nor PackageApplied(true) is acceptance. Require the internal
"Game has been successfully saved!" line after `save.write`, no strict save
ERROR, an immutable actual save with size/hash, and successful native readback
under a distinct guarded run. Creation of an empty/truncated placeholder is not
a save. Save/reload, calendar persistence, multiplayer, human UI and release
acceptance remain unverified. No native result is fabricated in this source
handoff.
