# Developer tools

Run `python -m dev --help` from the repository root to list the commands.
This package contains the shared checks, profile launcher and publication audits.
These public modules work without the separate maintainer production tools.

```text
python -m dev check
python -m dev doctor --faction demacia
python -m dev doctor --world
python -m dev play --profile "<installed or sealed profile>"
python -m dev audit --tracked-only --all
python -m dev source plan
```

`check` runs offline tests without starting the game. A standard checkout runs
the public smoke checks; the extended suite requires separate maintainer inputs.
`doctor` requires the
separate maintainer production tools and reports an explicit error when they are
unavailable. With those tools installed, it lists prerequisites and missing
inputs. Review publication-audit findings before sharing files;
licenses and repository history need separate checks.
See [development](../docs/DEVELOPMENT.md) for the full workflow.
