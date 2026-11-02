# VCMI source and distribution

The packaged game includes a modified VCMI engine. VCMI's code is licensed
under GNU GPL version 2 or later; its copyright notices and license text must
remain available to recipients. Upstream VCMI artwork has separate terms,
generally CC BY-SA 4.0, and third-party dependencies may have additional
license and source requirements. Review the notices for the actual build.

The recorded engine source starts from VCMI commit
`725ae80c42929ebbf6ccd620b38bd45ac32644c2`, with the pinned dependencies and
GoogleTest submodules, followed by nine local patches. The ninth records a
last-stack safeguard recovered from the retained binary-build source tree. To reconstruct that
recorded source in a new local directory:

```powershell
python -m dev.engine_source --output build/engine-source
```

This fetches the pinned sources and applies the nine hash-checked patches.
The reconstruction has been compared with the retained source tree associated
with the published binary build: all 4,077 files match after line-ending
normalization. The retained binaries match the pre-sanitization hashes in the
package audit. Source timestamps precede the binary build, but do not establish
historical immutability. This evidence does not establish complete corresponding
source for the distributed executable. In particular,
the exact build configuration, any additional source changes and bundled
dependency source and license obligations must be checked against the binary's
build records. Do not describe the reconstruction as verified corresponding
source until that comparison is complete.

The packaged FFmpeg libraries report LGPL 2.1-or-later and expose their build
configuration. Opening the bundled libdav1d decoder reports version 1.5.4.
The exact source revision and any downstream changes still need to be identified, and its applicable
copyright notice must accompany redistribution. Upstream FFmpeg and libiconv
source releases with the recorded version numbers are useful references, but
they do not establish whether the distributed libraries contain downstream
changes. The VCMI asset contributor list is likewise an upstream reference
until it has been compared with the assets actually shipped.

For an online binary distribution under GPLv2, arrange access to the complete
corresponding source and required build and installation scripts through the
same download location, or satisfy another applicable section 3 option. Keep
the copyright notices, license text and notices of changes. A link to the
unmodified upstream project or a collection of patches alone does not establish
that recipients have the complete corresponding source of a modified build.

The upstream VCMI project documents its licensing in its
[repository](https://github.com/vcmi/vcmi); its asset sources and attribution
are maintained in [vcmi-assets](https://github.com/vcmi/vcmi-assets). The
[GNU GPLv2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html) sets out
the distribution terms. Review the project’s separate
[rights and release preparation](RIGHTS_AND_RELEASE.md) for non-engine assets.
