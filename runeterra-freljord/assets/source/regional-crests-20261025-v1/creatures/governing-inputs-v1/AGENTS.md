# AGENTS.md — Homm3 workspace (Runeterra / Demacia)

This workspace builds a complete additional Heroes III town, **Demacia**, for VCMI, as the first
delivery of a wider Runeterra expansion. It is a long-running implementation effort with an
authored source, a production pipeline and hash-bound evidence.

This file is a router. It states the rules that must never be violated and points at the
authoritative documents. It does not repeat them.

## Read in this order

1. `RUNETERRA_DEMACIA_PROJECT_PROMPT.txt` — the reusable town-creation coordinator template:
   shared lore/eligibility, art, layout, tooling, preservation and acceptance rules.
   **Read it before planning or changing implementation work.** Quote its rules;
   do not paraphrase them from memory. For Demacia, also read its preserved scoped brief:
   `prompts/history/DEMACIA_PROJECT_PROMPT_20261022_b78fec6fa703.txt`, alongside current sources.
2. `runeterra-demacia/STATUS.md` — current stage hash, what is actually verified, what is pending.
   This is a dated snapshot: recheck evidence after any change.
3. `runeterra-demacia/docs/CORRECTED_SPEC.md` and `runeterra-demacia/docs/FACTION_SEPARATION.md`
   — the design and separation contracts.
4. `runeterra-demacia/build/reports/` — executed evidence. `source-tests.log` and
   `source-tests.json` are the authority for the last executed test count and result.
   **Never predict a test count; read it.**

## Workspace layout (real paths — the tree contains nested copies)

| Path | Role |
| --- | --- |
| `runeterra-demacia/` | **Implementation root.** `content/`, `design/`, `assets/`, `scripts/`, `tests/`, `build/`, `docs/` |
| `homm3-runterra-main/homm3-runterra-main/mod_design/` | Design documentation (not implementation) |
| `homm3-runterra-main/homm3-runterra-main/review/` | Audited source review and preserved baseline |
| `vcmi-develop/vcmi-develop/` | VCMI source checkout — **read-only reference** |
| `tools/` | Tool source checkouts (MMArchiveCLI, homm3data, mmarch, …) |
| `.tools/blender45/` | Removed at the user's request, 24 October 2026. Do not restore; painted 2D production is required. |
| `scripts/runeterra.py`, `scripts/runeterra.ps1` | Workspace entry points to the production CLI |

`runeterra-demacia/` is the content root, not the outer directory. `mod_design/` is documentation,
not runtime content. Do not treat a shorter link as the content root.

## Production CLI

Run from the workspace root. Prefer the project environment:

```powershell
.\scripts\runeterra.ps1 doctor
.\scripts\runeterra.ps1 references
.\scripts\runeterra.ps1 assets --resume
.\scripts\runeterra.ps1 build
.\scripts\runeterra.ps1 validate
.\scripts\runeterra.ps1 test --runtime
.\scripts\runeterra.ps1 preview
.\scripts\runeterra.ps1 package
.\scripts\runeterra.ps1 all
```

Equivalent: `python scripts/runeterra.py <command>`. Use
`runeterra-demacia/.venv/Scripts/python.exe` when the active interpreter lacks dependencies.

The CLI is the authority for production. Exit 0 means that stage passed; exit 2 means
incomplete/failed. `doctor` is an inventory and can succeed while listing missing prerequisites.
`package` (release) is blocked until the release gates pass; `package --source` produces a
labelled development-source archive, **not** an installable mod. Installation is always a
separate explicit command with a named destination.

## Non-negotiable rules

- **No Blender or equivalent 3D artwork production.** The latest user correction
  applies to all graphics, including towns, buildings, portraits, creatures,
  adventure objects, terrain, siege, UI and effects. Follow the mandatory graphics
  override and section 3 of `RUNETERRA_DEMACIA_PROJECT_PROMPT.txt`. Do not substitute
  another 3D renderer or paint over its renders. Use coherent painted 2D sources
  matched to original HoMM3 at native size. This supersedes older non-creature
  Blender allowances and regional production recipes. The earlier correction supersedes
  previous creature-rendering recipes: "PLEASE STOP USING BLENDER TO CREATE CREATURES
  ARTS, ITS NOT CARRY ON HOMM3 AESTETHICS". Follow
  `RUNETERRA_CREATURE_ART_POLICY.txt`. Use image-based painted sprite production and
  coherent 2D actions guided by actual native HoMM3 references. Do not model, rig,
  render or repaint Blender creature renders as the replacement workflow. Preserve
  the old sources as history; Targon's current Blender creature appearance is
  user-rejected for final use. Engineering checks do not approve its appearance.
- **Never modify** the licensed original game install (`D:\e2e\Heroes of Might & Magic III`),
  the checked-out VCMI source (`vcmi-develop/`), the extracted original references
  (`runeterra-demacia/references/extracted|frames|boards/`), or any audited source that a
  preserved baseline depends on. They are read-only inputs.
- **Never overwrite** an audited source with an earlier draft. Retired designs (Guardian/Royal
  Guardian, Royal Knight/Champion Knight, the old bolt-projector plan, rejected timings) are
  preserved as history, not aliases and not spawn sources.
- **Status vocabulary is strict.** Use exactly: *design proposal*, *authored configuration*,
  *runtime verified*, *release accepted*. Promote a feature only when evidence for that status
  exists. Loader success is not gameplay acceptance; a headless timeout is not a victory; source
  inspection is not execution; a successful source test is not art acceptance.
- **Do not weaken release acceptance** to make a development run look complete. Development
  staging stays explicitly labelled as development staging.
- **One native desktop operator at a time.** Only the assigned worker drives the VCMI window.
  Verify the owned PID and foreground window before any input. Never use `--testmap` for the
  interactive route; it forces AI-only ownership.
- **The coordinator publishes stages.** Workers own separate file paths and report; the
  coordinator integrates, stages and publishes. A runtime test holds the tested stage until it
  reaches a safe checkpoint.
- **The test window must follow the newest successfully built, production-fresh stage.** Reject
  stale conversions, mismatched sandbox copies and mid-build launches. `preview --stop` stops only
  the owned watcher/window.

## Working method

- Work autonomously through reversible implementation choices. Do not pause after writing a plan,
  after creating empty entity files, or after generating concept art.
- Report implemented, tested, incomplete and blocked work **separately**. Never claim full
  graphics, mechanics, automation or playability from a mock, an unexecuted script, a renamed
  Castle clone, a static preview, or a test that was not run.
- Preserve editable sources, recipes, manifests and evidence so a later review can reproduce
  any result. Use new report paths; do not overwrite historical evidence.
- Maintain `issues/README.md` and `issues/` as the open-only, High Priority six-town backlog.
  Document unresolved defects, verification gaps and external blockers with evidence and closure
  criteria. Once an item is fixed and appropriately verified, remove its issue file and index
  entry; preserve historical evidence in reports, not as closed items in `issues/`.
- Bilgewater review is the final queued item: start it only after every preceding todo and open
  issue is resolved. Recheck its then-current readiness and source-owner releases; do not assume
  the in-progress implementation has finished or begin its review in parallel with earlier work.
- Generated JSON must stay deterministic. Hand-edited design inputs in `content/` and `design/`
  are source, not output — never regenerate them from a script.

## Delegation (Kilo subagents)

### Mandatory model routing

- All project coordination, implementation, research and reviews use
  **`openai/gpt-6.1-sol` with reasoning variant `high`**. This includes Task
  subagents, command overrides and any explicitly requested Agent Manager work.
- Do not select Claude, another model, or a paid `kilo/` fallback. An independent
  review uses a separate GPT-6.1 Sol high worker, not a different model family.
- This routing supersedes older alternate-model review prompts. If the required
  model cannot run, report the routing/access error instead of trying other models.
- Preserve historical failed-dispatch and audit records; their model names are
  evidence, not executable routing instructions.
- Turn actionable audit findings into new todos and automatically delegate bounded
  follow-ups within the approved task scope to GPT-6.1 Sol high workers. External
  human review and rights approvals remain explicit blockers, never fabricated
  automated passes. Do not create visible sessions or worktrees without permission.

Six project specialist subagents are defined in `.kilo/agent/` and are dispatched with the Task
tool. Give each a concrete, bounded task with separate file ownership and an expected result.

| Subagent | Assignment |
| --- | --- |
| `demacia-runtime` | Native gameplay reproduction and build-bound evidence (sole desktop operator) |
| `demacia-town` | Town layers, building geometry, siege sources |
| `demacia-creatures` | Creature art and coherent action sets |
| `demacia-mechanics` | Mechanics, APIs, meaningful regressions |
| `demacia-lore` | Primary-source research and consistency review |
| `demacia-release` | Independent evidence and release review |

Subagents inherit the parent session's permissions. Their role instructions are working rules,
not an independent filesystem sandbox.

Slash commands for the recurring workflows live in `.kilo/command/`:
`/demacia-status`, `/demacia-build`, `/demacia-test`, `/demacia-preview`, `/demacia-lore`,
`/demacia-release-review`.

## Kilo configuration facts

- The model is pinned to `openai/gpt-6.1-sol` in `.kilo/kilo.jsonc` and in the global
  `~/.config/kilo/kilo.jsonc`, with default reasoning and subagent overrides set to
  `high`. The project allows only the OpenAI provider and this model. The `openai/`
  prefix is the authenticated path: it uses the
  ChatGPT browser login. The `kilo/` gateway prefix is **not** authenticated in the CLI
  credential store and every `kilo/...` model call fails with "You need to sign in to use
  this model". Do not change the prefix to `kilo/` unless `kilo profile` reports an
  authenticated account.
- `.kilo/kilo.jsonc` must keep `mcp` in the flat `{ "<server>": {...} }` form. A sibling
  `mcp.timeout` key makes the extension reject the whole file as invalid.
- Codebase indexing runs against a local Ollama instance: `nomic-embed-text`, 768 dimensions,
  `http://localhost:11434`. It is enabled in `~/.config/kilo/kilo.jsonc`. The Ollama service
  must be running before a session relies on `semantic_search`; the extension builds the
  index after a window reload.
- The workspace is a git repository on `main`. Agent Manager worktree mode is therefore
  available. Each worktree copies roughly 2 GB of authored assets, so keep the number of
  concurrent worktrees small and run desktop work in the main checkout.
