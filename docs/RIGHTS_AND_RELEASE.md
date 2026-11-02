# Rights and release preparation

This project references third-party worlds, characters, trademarks, software and artwork. The root GNU GPL version 3 license is intended for project-original source code only, to the extent contributors own the rights to license it. It cannot grant rights in third-party materials. Contributor ownership and the boundary between original and third-party code still require review; availability of a Git repository alone does not resolve those questions.

GPL is a copyleft open-source license: recipients may reuse, modify and distribute the code, and distributed derivatives must satisfy its source and license conditions. GPL permits selling copies; it does not prohibit resale. An explicit noncommercial restriction would not satisfy the Open Source Definition and may raise compatibility questions for third-party components.

The bundled VCMI engine is modified. The recorded upstream source and all nine
known patches can be reconstructed as described in [VCMI source and
distribution](VCMI_SOURCE.md), but their correspondence to the distributed
executables and the bundled dependencies is not yet established. GPL notices
and patches alone do not close that gap. Treat binary redistribution as pending
until the complete corresponding source and applicable dependency obligations
are verified and available to recipients.

Before publishing:

1. Confirm that contributors can grant the stated code license. Document any different licenses for code, art, documentation and third-party dependencies.
2. Inventory game data, extracted references, card art, fan art, generated images, audio, fonts, third-party source and binaries. Verify permission and license terms for each distributed item; remove or replace items without suitable rights.
3. Audit the full Git history and staged files for private data, secrets, local machine paths, licensed game assets and large files. Ignoring a path does not remove tracked content or history.
4. Reproduce the intended build and installation using a clean checkout and independently supplied game data. Document the actual VCMI version, dependencies, known limitations and removal instructions.
5. Publish credits and notices for material that may be distributed, and obtain any required contributor or external approvals.

Do not describe a source snapshot, loader success or development profile as a release unless its own acceptance and distribution requirements have been met.

The development history contains possible game archives and source records with personal file paths. Review both the current files and earlier commits before publishing. A separate repository containing only reviewed source may be needed; keep the original sources and development records locally.
