# Executed local engine validation

The requested-disconnect correction has **runtime verified** native-unit coverage.
It is not a Freljord gameplay, art, installation or release acceptance result.

- Base: official VCMI `725ae80c42929ebbf6ccd620b38bd45ac32644c2`.
- Separate patch SHA-256:
  `fda36a1cf4aa5742de3f6a108610cea2ac16996c5226bb0a8685979c6c99395a`.
- Six source files match `build/reports/engine-shutdown/source-freeze-v2.json`.
  Independent read-only review approved the source scope at
  `build/reports/engine-shutdown/independent-review-1792544801146/REVIEW.md`.
- CMake configure passed. The actual two-job MSVC client/server/test build completed
  all 888 build steps with exit zero in 1,265.933 seconds. Exact command and checksummed
  output: `build/reports/engine-shutdown/build-1792544023115791200/result.json`.
- The compiler executable reports MSVC **19.51.36256**. Its installed toolset directory
  is `14.51.36231`; the executable's version takes precedence over that folder name.
- The executed filtered C++ suite passed **12 tests, 0 failures, 0 disabled, 0 errors**,
  with native exit zero. Authority:
  `build/reports/engine-shutdown/test-1792545295749604800/gtest.json` and `result.json`.
  GTest reported 1.303 seconds; process capture including startup took 2.077 seconds.
- Tests call the actual server's protocol/transport-callback methods with controlled
  transports. They cover authorized host shutdown, denied requests, expected late and
  repeated completion, callback during close, unexpected active and unknown loss,
  independent players, weak lifetime and shared-owner identity. Unexpected ERROR
  records and their reasons are explicitly asserted. These are not end-to-end TCP or
  in-process transport gameplay tests.
- Fifteen enumerated original-install archives were read and copied into the owned
  unit-test data directory. Their SHA-256 values matched before and after. They are
  excluded from the runtime/source handoff. No installed original, reference checkout,
  existing runtime, mod stage or runtime selection was changed.

The coordinator must explicitly select the separate custom runtime, bind its complete
file inventory and source correction, and rerun current staged native validation.
The original strict diagnostic parser and release gates remain in force. No Freljord
game, graphical window or desktop input was performed by this engine-build worker.
Redistribution review and dependency corresponding-source obligations remain pending.

## Separate AI correction: exact-fixture RED/GREEN

The bounded AI correction is **runtime verified** only by native unit/regression
fixtures. Full Frontier replay and interactive acceptance remain pending.

- Separate patch #2 SHA-256:
  `9410fb047a1c102f8397b180933918186cf192796a2c93a39c584899fdb8fbad`.
  Patch #1 and its six frozen source/test files are unchanged.
- Final canonical ordered source diff SHA-256:
  `c30d04748ebf5ec258f53c9f4e3a96ee8fbc48ffa82fbf46fdfa5a96ed52749e`.
  Source hashes: `build/reports/engine-shutdown/ai-source-freeze-1792570908841472200/freeze.json`.
- Final RED: exact original two production AI files, final unchanged fixture bytes,
  and retained shutdown patch. **3 tests, 3 failures**, native exit 1,
  demonstrating the occupied escape endpoint, post-BattleAction zero-MP/live-path
  exception, and continued terminal composite action. Authority:
  `build/reports/engine-shutdown/test-1792570960658630100/gtest.json`.
  `ai-regression-red-final-1792570937062638100/result.json` records fixture hashes
  and byte-for-byte restoration of candidate production files.
- Final two-job incremental build passed in 21.038 seconds, exit 0:
  `build/reports/engine-shutdown/build-1792571005454271800/result.json`.
- Final GREEN passed **41 tests, 0 failures, 0 disabled, 0 errors**,
  exit 0; GTest 1.014s, captured process 2.316 seconds:
  `build/reports/engine-shutdown/test-1792571054123426800/gtest.json` and `result.json`.
  The suite includes all twelve unchanged shutdown regressions, the six new AI
  behavior/control cases, and existing immediate movement, blocked movement, idle
  interaction, route-failure, escape and multi-turn controls.
- The zero-MP fixture runs actual BattleAction and applied movement packets,
  invalidates actual gateway paths, observes a live destination requiring a later
  turn, and asserts defer/lock, no extra movement, and no immediate-route exception.
  It does not execute a complete native battle. The terminal fixture applies actual
  PlayerEndsGame and verifies that remaining CompositeAction/chain work stops.
- A real CGameHandler meeting emits and resolves one real exchange query without
  occupying the partner's tile. Actual active failed movement remains a failed task
  with ERROR records. The existing repeated-idle failure remains intact.
- Initial broader test execution exposed an upstream fixture's missing caller shared
  lock on Windows (STATUS_RESOURCE_NOT_OWNED). Direct test invocation sites now hold
  the normal makingTurn lock; no production lock code changed. Initial failed run
  `test-1792570416699783200` is retained. The first RED's cached-path weakness was
  corrected by actual invalidation; both earlier RED receipts remain as history.
- All fifteen enumerated original archives match their before/after hashes again.
  Every native-tested binary and the canonical source diff are bound in the receipt;
  handoff refuses a changed binary/source or nonzero GTest result.

No strict parser, severity, threshold, timeout, stage, runtime selection or original
engine checkout was changed. The older fda sealed app and source ZIP remain intact.
The new source archive includes both ordered patches and final reproduction helpers.

## Local transport and firewall trigger correction

The third correction is **runtime verified** by native server/runner/socket fixtures.
A fresh graphical game launch and its actual Windows notification behavior remain
pending; no firewall policy, UAC, installer, mod stage or selected runtime was changed.

- Patch #3 SHA-256:
  `3f894f73627b92435a2abc6dea3ba54d31ae8331f3a99ae772d3a6b32bade212`.
  Earlier two patch files and all forty-one earlier regression source cases remain
  unchanged. Ordered combined source diff:
  `a168a7b34aefe870f13d556563f50cab049ea7572d3c516703c231fa409e310e`.
- Frozen eleven source files and earlier regression hashes:
  `build/reports/engine-shutdown/local-transport-freeze-1792575157782740500/freeze.json`.
- Initial two-job incremental build:76 steps,222.838 seconds,exit0
  (`build-1792574492137401700/result.json`); final restore build:31.262
  seconds,exit0 (`build-1792575075818013700/result.json`). No clean or dependency
  rebuild was used.
- Final negative behavior control:10 tests,10 failures,exit1
  (`test-1792575025133088700/gtest.json`). It restores original listener, Hotseat,
  process and ANY-bind behavior while retaining only new API signatures/injection
  needed by the same exact fixtures. It is not an exact upstream binary. Fixture
  and candidate restoration hashes are in `local-transport-red-1792574987238408700/result.json`.
- Final GREEN:51 tests,0 failures,0 disabled,0 errors,exit0;
  GTest 2.252s,captured process 3.720 seconds
  (`test-1792575172502036900/gtest.json` and `result.json`). This includes all
  earlier41 and ten new native lifecycle/socket cases. Actual automatic production
  UDP3030 was observed (`automatic_udp_3030_observed=true`).
- Real Single/Hotseat thread runners establish internal connections without adding
  owning-PID IPv4 TCP or UDP listeners. Real spawned external Single/Hotseat server
  processes bind only127.0.0.1 TCP with no UDP; loopback address and cleanup are
  inspected via Windows IP Helper tables. Actual LAN ANY TCP binding, assigned
  advertised port, automatic UDP3030 stop/restart, discovery reply and TCP accept
  are verified. Controlled handlers also test no constructor listener, startup
  ordering, failed binding, global-lobby deferred hosting and conflicting local flags.
- First new-fixture run `test-1792574779806423600` retains its one cleanup-observation
  failure. A bounded1s fixture wait now synchronizes the Windows owning-PID table
  retirement after process exit; production/runtime timeouts were not changed.
- Built early CLI probes (`local-transport-cli-1792575200741028200/result.json`):
  --help exit0 includes --local-only/loopback, --version exit0, and
  --local-only --lobby exit1 with the exact conflict message before networking.
- All15 enumerated original archives again match before/after SHA-256 values.
  Test receipts bind the full executable/DLL inventory and exact canonical source.
  New handoff contains all three patches, final helpers, exact engine source and
  dependency/license provenance. Earlier fda/c30 apps and archives remain sealed.

The existing external-process/global-lobby localPort=0 connection handoff limitation
and custom non-loopback localHostname configuration are not claimed fixed. External
fixtures use a reserved explicit port and normal127.0.0.1. The ten native tests prove
listener behavior; they do not substitute for gameplay/GUI acceptance or a complete
third-party redistribution/source-offer review.
