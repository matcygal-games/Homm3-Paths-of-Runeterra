# Contributing

You can contribute code, balance changes, artwork, lore research, maps or documentation. Open an issue before starting a large feature so we can agree on its scope. Small fixes can go straight to a pull request.

## Local workflow

1. Create a branch from `main`.
2. Follow [local development](docs/DEVELOPMENT.md) and run `python -m dev check`.
3. Read the owning component's `README.md`, `content/` definitions and `STATUS.md`.
4. Make your change and run the relevant component checks.
5. Open a pull request explaining what changed, how you tested it and any remaining problems.

Documentation corrections and reproducible bug reports are good first contributions. Include the mod version, faction, expected behavior and steps to reproduce a bug.

The public smoke checks, source export, publication audit and existing-profile launcher work from a standard checkout. The extended test suite, component builds, artwork regeneration and prerequisite inventory require separate maintainer inputs; arrange those inputs with the maintainers when needed.

## Content and code conventions

- Edit gameplay definitions in `content/` directly and explain design decisions in the PR. Keep build output in ignored directories.
- Use clear names and deterministic generated JSON. Keep identifiers, upgrades, recruitment and scenario references consistent.
- Preserve editable artwork, credits and license information. Coordinate production recipe changes with the maintainers, and include screenshots or animation samples for visual changes when useful.
- Follow the [workspace](docs/standards/workspace.md), [production](docs/standards/production.md), [art](docs/standards/art.md) and [heraldry](docs/standards/heraldry.md) standards.
- List the tests you ran and their results. For gameplay and visual changes, describe what you checked in VCMI as well.

See [adding content](docs/ADDING_CONTENT.md) for the content workflow and [architecture](docs/ARCHITECTURE.md) for component responsibilities.

## What to include in a pull request

Explain the problem and your fix, identify affected regions, and list your test results. For assets, include the source, editable files and redistribution license or permission.

Keep game archives, local profiles, saves, personal paths, credentials and build output out of the PR. Use the [repository hygiene checklist](docs/REPOSITORY_HYGIENE.md) before submitting.

## Contribution license

Original source-code contributions are intended to use GNU GPL version 3. Only contribute work you have the right to license under those terms. Third-party materials retain their own licenses and require separate permission where applicable; opening a pull request does not establish those rights. See [NOTICE.md](NOTICE.md).
