# ppau-graphics
Graphics for @ppau


There are several purposes for this repository:

1. Version control and general ability for collaboration with source documents.
2. Build an infrastructure that allows us to seamlessly update authorisation tags and, if necessary, printing tags.


# Requirements

The following programs are required by the render script.

- a working Python 3.5 (or newer) install to run it.
- `rsvg-convert` (path defined in the script, you'll probably have to update this)
- `find(1)`
- `sed(1)`

Additionally, most files in this repository are tracked using Git LFS. See the `.gitattributes` file for a detailed list. An example line:

`*.jpg filter=lfs diff=lfs merge=lfs -text`

The `rsvg-convert` tool is installed as part of `librsvg` on my machine.
