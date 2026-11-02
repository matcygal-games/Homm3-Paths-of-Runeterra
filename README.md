# Heroes of Might and Magic III: Paths of Runeterra

Paths of Runeterra brings Runeterra-inspired towns, armies, heroes and adventures to Heroes III, using [VCMI](https://vcmi.eu/). The art direction follows the painted 2D style of the original game.

**You need your own compatible copy of Heroes of Might and Magic III: Complete.** Game data is not included. The mod is in development, and most available scenarios are playtest maps.

## Start here

- **Play:** [download a release](https://github.com/matcygal-games/HOMM3-Paths-of-Runeterra-Releases/releases), follow its installation instructions, and use its launcher.
- **Contribute:** read [CONTRIBUTING.md](CONTRIBUTING.md) and the [local development guide](docs/DEVELOPMENT.md).
- **Report a problem:** include your mod version, VCMI version, affected faction and steps to reproduce it in a GitHub issue.

After cloning, check the developer tools with:

```powershell
python -m dev check
```

The checks run offline without game data. List the other developer commands with:

```powershell
python -m dev --help
```

## Source layout

| Directory | Purpose |
| --- | --- |
| `runeterra-<region>/` | A faction's gameplay configuration and artwork |
| `runeterra-world/`, `runeterra-world-systems/` | Adventure-map content and world systems |
| `paths-of-runeterra/` | Shared mod and scenario configuration |
| `dev/` | Common contributor commands |
| `tests/` | Shared tests and fixtures |
| `docs/` | Development guides and content standards |
| `installer/` | Windows installer source |
| `vendor/` | Redistributable third-party source and its licenses |

For faction changes, start with its `README.md`, `content/` files and `STATUS.md`. Full production builds and artwork regeneration require separate maintainer tools and authoring inputs, which are excluded from a standard source checkout. Check the dates in status records before relying on old build results. See [architecture](docs/ARCHITECTURE.md) for the project structure and [adding content](docs/ADDING_CONTENT.md) for the content workflow.

## Project standards

Include editable sources and credits with each contribution. Use painted 2D artwork that fits Heroes III, and test gameplay changes in a freshly built VCMI profile.

The [workspace](docs/standards/workspace.md), [production](docs/standards/production.md), [art](docs/standards/art.md) and [heraldry](docs/standards/heraldry.md) standards describe the shared requirements.

## License and third-party content

Project-original source code is intended to use [GNU GPL version 3](LICENSE), as described in [NOTICE.md](NOTICE.md). Third-party software and assets keep their own terms. This license does not cover Heroes III or Riot Games characters, trademarks, artwork or game data.

Before distributing source or an installer, read [rights and release preparation](docs/RIGHTS_AND_RELEASE.md) and [repository hygiene](docs/REPOSITORY_HYGIENE.md).
