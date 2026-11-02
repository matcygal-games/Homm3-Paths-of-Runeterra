# Fifth local engine patch: own hero defeated during movement

This incremental patch follows the immutable fourth patch
`0004-ai-turn-lifecycle.patch` (SHA256
`2cc42f37d47c6c688eaa1b0e270dae04e08e4a5641d47dca1359829bcc56eb3a`).
It is a local VCMI modification, not an official VCMI distribution. Native game
acceptance and rights approval remain separate.

The captured fourth-patch frontier run finished normally, but the AI printed two
ERRORs after Rashka instance65 retreated from Battle1 (native actionType2 maps to RETREAT, then ESCAPE) and the server removed that hero.
`moveHeroToTile` represented normal defeat as a generic failed goal; `executeTask`
then printed the two errors and already replanned. The later rehired Rashka
instance2 is a separate loss. Raw diagnostics remain preserved.

The new cancellation requires all of these conditions:

- The moving hero was verified and belonged to this AI when movement began.
- A new authoritative NORMAL, ESCAPE or SURRENDER BattleResult has the opposite valid winner and names that same own fighting hero.
- Its own HERO removal callback follows that result.
- The movement wait returns and that hero no longer verifies.

The mutex-protected per-hero sequence is sampled before movement, so an earlier
loss, another hero's loss, or an unrelated removal cannot authorize this path.
A distinct exception passes through the existing hero-chain generic-error catches.
The task consumer logs an explicit INFO cancellation, retains the existing failed
path exclusion and pathfinder invalidation, and returns false to the existing
bounded retry/replanning policy. Generic failure diagnostics remain intact.
Unknown result codes, invalid winners, stale lookup, wrong ownership and battle wins retain generic failure reporting.

No server authority, movement, combat strength, save field, network packet,
serialization version, turn protocol or random draw changes. The transient AI
bookkeeping is not saved. Planning decisions after a real defeat can change
because this case is classified explicitly, but gameplay state mutations remain
under the existing server consumers. Both execution paths already stopped the
failed movement and replanned.

Reproduction requires the pinned corresponding-source ZIP and the exported
fourth-patch sibling. The ZIP, toolchain, licensed original archives and runtime
are external prerequisites, not archive payloads. From the workspace root:

```powershell
python runeterra-bandlecity/engine-patches/hero-loss-replanning/prepare_source.py --zip <pinned-source.zip> --with-preview
python runeterra-bandlecity/engine-patches/hero-loss-replanning/build_candidate.py configure
python runeterra-bandlecity/engine-patches/hero-loss-replanning/build_candidate.py build --jobs 4
python runeterra-bandlecity/engine-patches/hero-loss-replanning/build_candidate.py test --filter "HeroLossReplanning.*:CreaturePreview.*"
```

The optional sixth patch follows fifth-only CMake and adds the optional creature
preview field. Fifth-only reconstruction omits `--with-preview`. The new builder
uses this family's own `src`/`b` by default; `--working-cache` explicitly uses the
authorized mutable fourth-family working cache used during development. It never
selects a runtime or launches a client/server game.

The native regression starts a real CGameHandler attack and drives real
BattleResultProcessor result/finalization/removal consumers with a fixed normal
outcome. A passive tactical interface keeps combat choice outside its scope. Separate retreat and surrender regressions submit real MakeAction requests to the server, exercising validation and the actual RetreatAction/SurrenderAction result mapping.
This is a battle lifecycle and task-consumer test, not combat or gameplay
acceptance. Final exact source/build/RED/GREEN/runtime pins are in provenance.json.

Fixture limits: this is an in-process server-finalization/task adapter. A passive tactical interface and explicit ONGOING_BATTLE status substitute for full CClient battleStart. HeroVisit, PlayerBlocked and battleResultsApplied routing, network concurrency and real tactical AI choice are outside this adapter; final exact-stage native frontier reproduction remains required.
