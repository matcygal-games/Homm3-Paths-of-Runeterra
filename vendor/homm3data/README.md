# homm3data decoder

This directory vendors the minimal `homm3data` Python decoder used by the
project's reference tools and guarded UI checks. The source files and MIT license
are copied without modification from the upstream homm3data project.
The upstream project is <https://github.com/laserlicht/homm3data>.

Only the package's five Python modules and `LICENSE` are included. No original
Heroes III data, extracted game images, local settings, development history or
third-party binaries are included.

Consumers put this directory on Python's module search path. Pillow and NumPy
requirements are specified by each consuming regional project. There is no
network download during import or source export.

When updating the decoder, retain the upstream license and review the guarded
decoder inventory in `runeterra-ionia/docs/TOOL_DEPENDENCIES.json`. Changing the
declared files or their paths requires fresh source and runtime checks. Earlier
test records continue to describe the decoder version used for those runs.
