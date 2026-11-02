# Isolated VCMI lifecycle and AI corrections

These three local VCMI patches correct connection shutdown, computer opponent
movement and networking for local games. Native regression results are recorded in
[VALIDATION.md](VALIDATION.md); Freljord gameplay and release acceptance remain
pending. The build uses a separate source tree and leaves `vcmi-develop/`, the
installed game, selected runtime and mod stages unchanged.

The frozen diagnosis is
`build/reports/crash-review/frontier-requested-disconnect-1792542435953043200/REVIEW.md`.
The completed game legitimately requested a protocol disconnect. The server removed
the application connection, then its queued transport callback unconditionally emitted
ERROR. The strict runner correctly refused the otherwise completed run.

`0001-track-requested-connection-closures.patch` applies to official VCMI commit
`725ae80c42929ebbf6ccd620b38bd45ac32644c2`. It records connection ownership before an
authorized disconnection packet or a rejected incoming connection closes its transport.
Queued callbacks for those exact owners remain identifiable, including duplicate
completion callbacks. Weak ownership does not prolong transport lifetime or mistake
another connection at the same raw address for the old connection. Expired entries are
reaped on later close requests.

Unexpected active loss and unknown connection loss still emit ERROR, including their
transport reason. Active-loss cleanup still runs once; a denied protocol request cannot
authorize a close. The expected callback remains visible at DEBUG. No log filtering,
test-runner whitelist, threshold change, network packet or save serialization change is
part of this patch. All state is local to the server network thread.

## Reproduce the isolated build

Run commands from the workspace root. All downloads, Conan cache and compiler outputs
belong under `runeterra-freljord/.tools/engine-shutdown-fix/`.

1. Clone `https://github.com/vcmi/vcmi.git` there as `source`, check out the exact commit
   above, and initialize only `dependencies` and `test/googletest`. Their pinned commits
   are `68f3f22614a3b17c80aa603b0c013181db845048` and
   `b514bdc898e2951020cbdca1304b75f5950d1f59`.
2. Apply all files in `patch-series.json` order with `git apply`. Mark the new
   source files visible to the unstaged diff/export using
   `git add --intent-to-add server/ExpectedConnectionClosures.h test/server/ConnectionShutdownTest.cpp test/server/LocalServerDiscoveryTest.cpp`.
   This records intent only; the modified tracked source remains unstaged.
   Create the isolated `venv`, then install
   `engine-patches/requirements-tools.lock.txt` (Conan 2.33.0). No global Python package or setting
   is required.
3. Download the official
   [2026-10-13 Windows x64 dependency archive](https://github.com/vcmi/vcmi-dependencies/releases/download/2026-10-13/dependencies-windows-x64.txz).
   It is 98,360,212 bytes with SHA-256
   `e9146cd47352d58092cf6ede1bfdf06824e290f6034c5779494c2f10f9e6df91`.
   Set process-local `CONAN_HOME` to the owned `conan-home`, run `conan profile detect`,
   then `conan cache restore` for this archive.
4. From the owned `source`, run the isolated Conan executable:

   ```text
   ../venv/Scripts/conan.exe install . --output-folder=../conan-generated --build=never --profile=dependencies/conan_profiles/msvc-x64 -s &:compiler.version=195 -c tools.cmake.cmaketoolchain:generator=Ninja -c tools.microsoft.msbuild:vs_version=18 -o &:target_pre_windows10=True -o &:with_onnxruntime=False -o &:with_discord_presence=False
   ```

   Quote arguments containing `&` in PowerShell. The package profile consumes upstream
   v142 x64 binaries; only the application compiler is overridden to installed MSVC
   19.51.36256 / Visual Studio Build Tools 2026, installed under toolset directory
   `14.51.36231`. The compiler executable reports its own later build number. The initial offline attempt preserved
   in `conan-install.log` failed on a missing recipe; the subsequent online install
   fetched recipe metadata and succeeded without compiling dependencies.
5. From the workspace root:

   ```text
   runeterra-freljord/.tools/engine-shutdown-fix/venv/Scripts/python.exe runeterra-freljord/engine-patches/build_isolated.py configure
   runeterra-freljord/.tools/engine-shutdown-fix/venv/Scripts/python.exe runeterra-freljord/engine-patches/build_isolated.py build
   runeterra-freljord/.tools/engine-shutdown-fix/venv/Scripts/python.exe runeterra-freljord/engine-patches/build_isolated.py test
   ```

The helper captures MSVC's environment only for its subprocesses and uses the installed
CMake/Ninja tools by exact path. It builds client, server and tests with two jobs.
Launcher, editor, Discord and experimental MMAI are disabled; BattleAI, Nullkiller2,
Lua and the SDL3 client remain enabled. It writes immutable command/log/result receipts
under new `build/reports/engine-shutdown/{phase}-{timestamp}/` directories.

The shutdown GTests exercise actual `CVCMIServer` protocol/callback methods with controlled
transports and an in-memory network logger. They cover requested internal-style closure,
repeated TCP-style completion, callback during close, unexpected active loss, unrelated
unknown loss, denied requests, another player's failure, rejected incoming connections,
weak lifetime and raw-address/ownership separation. Controlled transport reasons do not
constitute end-to-end TCP or internal transport gameplay tests. Native mod completion
must still run against the newly built binary hashes and current staged content.

The helper does not install or select candidate binaries. Before testing a candidate
in-game, review its executed test results and record its complete dependency
inventory, source commit and patch checksum alongside the observations. The upstream
version string alone does not distinguish a patched binary from the official build.

After a successful native test receipt, `prepare_handoff.py --test-receipt <result.json>`
creates a new custom-runtime app directory, full file/binary inventories, copied upstream
dependency notices and an exact patched-engine source ZIP under the owned tools root.
It refuses mismatched patch/source bytes or failing tests. Its app excludes original
archives, test fixtures, user paths and unrelated executables. Microsoft CRT DLLs come
from the installed compiler's standard redistributable directory, with their input hashes
and provided notices recorded. Existing runtime directories and selection files are never
written. The handoff explicitly leaves third-party redistribution/source-offer review
pending; it is available for local verification only.

## Separate AI behavior correction

`0002-stop-unoccupiable-escapes-and-exhausted-chains.patch` is a separate correction
on the same pinned engine. The frozen diagnosis is
`build/reports/crash-review/frontier-ai-chain-1792569648361182300/REVIEW.md`.
Rosic's actual friendly meeting was selected again as an ESCAPE destination even though
the occupied tile could not be entered. Udyr's actual final BattleAction consumed all
movement before the old immediate route was checked; the terminal packet arrived later.

The escape scorer now excludes another friendly map HERO occupying its destination,
while preserving town garrisons and intentional meeting goals. Hero chains defer and
lock an exhausted post-special-action hero before rechecking its live immediate path.
Actual ended player status stops remaining chain/composite actions. No hypothetical
victory prediction, generic exception catch, log severity or strict runner rule changed.

Native fixtures retain real map/pathfinding/Nullkiller consumers. One test completes
an actual CGameHandler friendly meeting and answers its real exchange query once;
others exercise real BattleAction and applied movement/PlayerEndsGame packets. The
post-action path cache is actually invalidated, so its immediate target really requires
another turn. These packet-controlled movement tests do not simulate an entire battle.
Unexpected active failed movement still emits ERROR, repeated idle chains still fail,
and all twelve shutdown regressions remain unchanged.

Direct AI test calls now hold the shared game-state lock that their normal makingTurn
caller owns. This fixes an existing test invocation precondition on Windows; production
locking was not changed. Locks are scoped at direct call sites, avoiding a second lock
in tests that call AIGateway::makeTurn itself. Historical failing receipts are retained.

`patch-series.json` pins all patch hashes. Handoff validation applies them in order to
a separate temporary Git index, compares their full canonical diff with the compiled
tree, and binds that diff plus every executable/DLL to the native test receipt. It does
not touch the normal index, first sealed runtime or selected runtime. The provenance
field `patch_sha256` identifies the canonical combined source diff; `patch_series`
records each separate patch. [VALIDATION.md](VALIDATION.md) lists the exact executed
RED/GREEN receipts.

## Local sessions and LAN discovery

`0003-keep-local-games-off-lan-listeners.patch` corrects the unnecessary incoming
listeners behind repeated firewall prompts for fresh sandbox executable paths.
The diagnosis is under `build/reports/firewall-local-transport/1792573817324303200/`.
The earlier server constructor started discovery before knowing the session mode;
Hotseat also retained MULTI and requested a TCP listener. Neither was needed for
same-process local play.

Single-player and Hotseat now use the real internal transport with no incoming
TCP or discovery socket. The runner receives the actual Hotseat intent. The
separate-process route passes the documented `VCMI_server.exe --local-only` flag
and binds TCP only to 127.0.0.1, with no discovery. `--local-only --lobby` is rejected
before startup. The existing `--run-by-client` option is now read by its declared
spelling. No unsupported settings override or firewall rule is introduced.

Actual LAN hosting retains ANY TCP binding and UDP discovery on port3030. Discovery
starts only after the TCP listener succeeds and advertises its actual assigned port.
It stops on leaving the lobby, restarts when an actual LAN host returns to the lobby,
and never starts for internal or loopback-only sessions. Global-lobby login can still
start its incoming listener later. The socket protocols and save formats are unchanged.

Native tests inspect actual Windows owning-PID IPv4 TCP/UDP tables for local threads,
working internal connections, real spawned external Single/Hotseat processes, loopback
binding and cleanup. The LAN case verifies actual ANY binding, automatic production
UDP3030 stop/restart, wire reply and accepted TCP connection. If another instance owns
3030, only the wire-format probe uses a private port; the recorded test property states
that limitation. The final executed run observed the automatic production listener.
Controlled INetworkHandler implementations additionally exercise real server lifecycle
methods, failed binding and constructor/start ordering without opening sockets.

The ten-case negative control retains only new API signatures/injection needed to
compile identical fixtures, while restoring original listener/Hotseat/process/bind
behavior. It is not an exact upstream binary. All ten tests fail under that control.
Final source/fixture hashes and all original failures are retained in the reports.

The correction requires no administrator rights or firewall-policy change. Native
socket observations do not by themselves prove the absence of Windows notification
UI on a future game launch; the newly selected app still needs that check.
LAN hosting still opens incoming network listeners. Pre-existing external-process/global-lobby
localPort=0 connection handoff and custom non-loopback localHostname limitations
are outside this fix; external tests use an explicit reserved port and default loopback.

`probe_local_transport_cli.py` reproduces the built server's help/version/conflicting
flag checks without starting networking or a game. The source archive includes this
helper and all three ordered corrections. Earlier sealed apps/archives remain intact.
