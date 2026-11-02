# Adding content

Start in the relevant region or world component. Read its `README.md`,
`STATUS.md` and existing `content/` definitions before choosing identifiers or
artwork. Check the dates of earlier test results; changed content needs fresh checks.

1. **Define the behavior.** Add or update the hand-edited configuration in the
   component's `content/`. Explain associated design decisions in the pull request.
   Keep IDs, upgrade relationships, recruitment, descriptions and scenario references
   consistent. Follow the component's own schema and source conventions.
2. **Add assets and provenance.** Put editable masters in the component's `assets/source/` tree.
   Coordinate recipe changes with the maintainers when artwork must be regenerated.
   Record the source and redistribution rights for new work. New game artwork
   follows the project's [painted 2D art requirements](standards/art.md).
3. **Build and check.** Run the shared contributor checks. Component asset regeneration
   and a fresh production stage also require its separate authoring inputs. Make
   changes in the source files rather than generated `build/` files.
4. **Try it in game.** Test the new stage in a separate VCMI profile. Check the
   affected screens, animation, combat and computer-player behavior, and record
   any problems. A successful load is only the first check.
5. **Open a pull request.** Explain the change, list the commands and results,
   note outstanding limitations and attach screenshots when useful. Include
   project source and redistributable assets; keep game archives, private
   references, personal paths, saves and local logs outside the contribution.

See [development](DEVELOPMENT.md), [architecture](ARCHITECTURE.md), and
[contributing](../CONTRIBUTING.md) for entry points and project conventions.
