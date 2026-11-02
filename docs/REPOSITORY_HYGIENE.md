# Repository hygiene

Commit the code, configuration, documentation and editable assets needed to build the mod, with their credits and licenses. Keep game installations, generated output and personal files out of Git.

## Public source and local files

| Include after review | Keep local and ignored |
| --- | --- |
| Authored configuration and design inputs | Original Heroes III data and extracted references |
| Build tools, tests and dependency declarations | Runtime installations and playtest profiles |
| Redistributable editable assets and credits | Generated stages, archives, logs and recordings |
| Contributor guides and build specifications | Working notes, research drafts and local test reports |
| Licenses and relevant third-party notices | Personal settings, paths, saved games and credentials |

Keep local notes, experiments and historical records outside the public source set. Moving a tracked file into an ignored directory does not remove it from Git or its history.

Keep required source files, credits and licenses with the assets they describe. Store historical development records locally.

## Audit before publication

Run the tracked audit, then check tracked and unignored files together:

```powershell
python -m dev audit --tracked-only --all
python -m dev audit --all
```

For machine-readable findings:

```powershell
python -m dev audit --tracked-only --format json
```

The audit flags personal paths, possible game archives, linked or unreadable files, large files and missing indexed paths. Review each finding. An unstaged deletion is still indexed and appears as missing; staging it removes the path from the tracked-file list. License and secret checks need separate review.

Before committing, review additions and removals together:

```powershell
git status --short
git diff --cached --stat
git diff --cached
```

Check additions and removals together. Review image metadata, binaries and third-party licenses before including them.

## Existing history

Earlier commits may contain files that are now ignored or deleted. The development history still needs privacy and rights review before publication. If it cannot be shared, prepare a separate repository containing reviewed source, and keep the original development history locally.

Read [rights and release preparation](RIGHTS_AND_RELEASE.md) before publishing source or installer artifacts.
