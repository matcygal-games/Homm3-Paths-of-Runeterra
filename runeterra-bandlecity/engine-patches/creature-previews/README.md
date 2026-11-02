# Optional creature preview animation (incremental patch six)

Authored configuration. The actual client/server/test build succeeded, and all seven native preview controls passed in the final targeted21 and broader93 test runs. Those counts overlap; they are not summed. GUI framing acceptance still requires the runtime operator's current-stage Fort and recruitment witnesses. `provenance.json` binds the exact final receipts and binaries.

`graphics.animationPreview` is an optional animation resource string. Only `CCreaturePic` selects it. Combat, adventure animation, projectiles, timing, battle registration and save/network versions are unchanged. An unavailable explicitly selected resource fails the creature loader. No faction identifier is hardcoded.

An absent field preserves the original animation and exact crop `(single ? 150 : 170,155,width,height)`. An explicit preview uses one shared frame canvas and centered integer crop. The Bandle authored canvas is 100x130: Fort's 100x120 window uses `(0,5,100,120)`; recruitment/details' 100x130 window uses `(0,0,100,130)`. Both footprints use the same camera. A canvas smaller than its actual viewport throws instead of silently clipping. All animation frames must retain that canvas and camera. Ordinary preview groups and native timing are unchanged.

The common constructor covers Fort, recruitment, CreaturePurchaseCard, creature/stack details, stack experience, upgrade comparisons and wiki. The independent blacksmith war-machine `CCreatureAnim` consumer is unchanged. The fixed camera derives from the complete preview-group union, with the holding body centered at (50,65), and does not recenter individual action frames.

Apply after patch five. `changes.json` binds exact old/new bytes for four production files, the new native test and central test CMake. The four production baselines equal the preserved fourth-patch source; CMake starts from the builder's fifth-patch checkpoint. `prepare_source.py <explicit-disposable-source-tree>` verifies all six baseline/overlay hashes before writing, and is idempotent. It never opens game data or compiles. The exact overlay is authoritative for CRLF bytes; the patch is the reviewable incremental diff. The builder owns compilation and CMake registration.

For direct patch application use `git -c core.autocrlf=false apply 0006-creature-preview-animation.patch` from the prepared source root, outside an enclosing unrelated Git repository. This preserves the explicit mixed line endings. The byte-verifying overlay helper avoids global Git settings entirely.

Native `CreaturePreview.*` tests exercise original nine-town fallback, real optional selection, both viewport/footprint crops, invalid canvas rejection, native JSON schema, real missing-resource loader behavior, and JSON/binary persistence independence. `python tests/test_preview_patch.py` checks the handoff and negative overlay controls offline. Source inspection finds no new serialization member: presentation is reloaded from mod configuration, while existing creature JSON and bonus-node binary serialization stay unchanged.

Source export uses only a schema-two `source-export-files.json` explicit compact list. Baseline copies, build trees, source archives, original assets and private/runtime data are excluded.
